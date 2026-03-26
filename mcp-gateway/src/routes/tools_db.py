"""
MCP工具路由（数据库集成版本）
"""
from fastapi import APIRouter, HTTPException, Path, Query, Depends, Request
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.tool_models import (
    ToolRegisterRequest,
    ToolRegisterResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolInfo,
    ToolListResponse,
    ToolStatus,
    ErrorResponse
)
from ..services.tool_service import ToolService
from ..dependencies.database import get_db
from ..tools import tool_registry  # 使用全局单例实例
from sqlalchemy.orm import Session

import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_tool_service(db: Session = Depends(get_db)) -> ToolService:
    """获取工具服务"""
    return ToolService(db, tool_registry=tool_registry)


@router.post(
    "/register",
    response_model=ToolRegisterResponse,
    status_code=201,
    summary="注册MCP工具",
    description="注册一个新的MCP工具到网关中（数据库集成版本）",
    responses={
        201: {
            "description": "工具注册成功",
            "model": ToolRegisterResponse
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse
        },
        409: {
            "description": "工具已存在",
            "model": ErrorResponse
        }
    }
)
async def register_tool(
    request: ToolRegisterRequest,
    db: Session = Depends(get_db)
) -> ToolRegisterResponse:
    """
    注册MCP工具
    
    - **tool**: 工具定义（包含名称、描述、参数等）
    - **overwrite**: 是否覆盖已存在的工具（默认：False）
    """
    try:
        service = get_tool_service(db)
        
        # 转换为字典
        tool_dict = request.tool.model_dump()
        
        # 获取执行器（如果有）
        executor = None
        if hasattr(request, 'executor') and request.executor:
            executor = request.executor
        
        result = await service.register_tool(
            tool_def=tool_dict,
            overwrite=request.overwrite,
            executor=executor
        )
        
        return ToolRegisterResponse(
            success=result["success"],
            tool_name=result["tool_name"],
            message=result["message"],
            registered_at=datetime.now()
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400 if "already exists" not in str(e) else 409,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to register tool: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register tool: {str(e)}"
        )


@router.get(
    "/search",
    response_model=ToolListResponse,
    summary="搜索工具",
    description="根据关键词搜索工具（数据库集成版本）",
    responses={
        200: {
            "description": "匹配的工具列表",
            "model": ToolListResponse
        }
    }
)
async def search_tools(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    db: Session = Depends(get_db)
) -> ToolListResponse:
    """搜索工具"""
    try:
        service = get_tool_service(db)
        
        # 搜索工具
        result = await service.search_tools(
            query=q,
            page=page,
            page_size=page_size
        )
        
        # 转换为Pydantic模型
        tool_infos = []
        for tool_dict in result["tools"]:
            tool_infos.append(ToolInfo(
                name=tool_dict["name"],
                description=tool_dict["description"],
                version=tool_dict["version"],
                tool_type=tool_dict["tool_type"],
                status=ToolStatus(tool_dict["status"]),
                parameters=tool_dict.get("parameters", {}),
                required_parameters=tool_dict.get("required_parameters", []),
                metadata=tool_dict.get("metadata", {})
            ))
        
        return ToolListResponse(
            tools=tool_infos,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    
    except Exception as e:
        logger.error(f"Error searching tools: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching tools: {str(e)}"
        )


@router.get(
    "",
    response_model=ToolListResponse,
    summary="获取可用工具列表",
    description="获取所有已注册的MCP工具列表，支持分页和过滤（数据库集成版本）",
    responses={
        200: {
            "description": "工具列表",
            "model": ToolListResponse
        }
    }
)
async def list_tools(
    status: Optional[ToolStatus] = Query(
        None,
        description="按状态过滤工具",
        example="active"
    ),
    tool_type: Optional[str] = Query(
        None,
        description="按工具类型过滤",
        example="function"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    db: Session = Depends(get_db)
) -> ToolListResponse:
    """获取可用工具列表"""
    try:
        service = get_tool_service(db)
        
        result = await service.list_tools(
            page=page,
            page_size=page_size,
            status=status.value if status else None,
            tool_type=tool_type
        )
        
        # 转换为Pydantic模型
        tool_infos = []
        for tool_dict in result["tools"]:
            tool_infos.append(ToolInfo(
                name=tool_dict["name"],
                description=tool_dict["description"],
                version=tool_dict["version"],
                tool_type=tool_dict["tool_type"],
                status=ToolStatus(tool_dict["status"]),
                parameters=tool_dict.get("parameters", {}),
                required_parameters=tool_dict.get("required_parameters", []),
                metadata=tool_dict.get("metadata", {})
            ))
        
        return ToolListResponse(
            tools=tool_infos,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
        
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tools: {str(e)}"
        )


@router.get(
    "/{tool_name}",
    response_model=ToolInfo,
    summary="获取工具详情",
    description="根据工具名称获取工具详细信息（数据库集成版本）",
    responses={
        200: {
            "description": "工具信息",
            "model": ToolInfo
        },
        404: {
            "description": "工具不存在",
            "model": ErrorResponse
        }
    }
)
async def get_tool(
    tool_name: str = Path(..., description="工具名称"),
    db: Session = Depends(get_db)
) -> ToolInfo:
    """获取工具详情"""
    try:
        service = get_tool_service(db)
        tool_info = await service.get_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        return ToolInfo(
            name=tool_info["name"],
            description=tool_info["description"],
            version=tool_info["version"],
            tool_type=tool_info["tool_type"],
            status=ToolStatus(tool_info["status"]),
            parameters=tool_info.get("parameters", {}),
            required_parameters=tool_info.get("required_parameters", []),
            metadata=tool_info.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool: {str(e)}"
        )


@router.post(
    "/{tool_name}/execute",
    response_model=ToolExecutionResponse,
    summary="执行工具",
    description="执行指定的MCP工具（数据库集成版本）",
    responses={
        200: {
            "description": "执行成功",
            "model": ToolExecutionResponse
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse
        },
        404: {
            "description": "工具不存在",
            "model": ErrorResponse
        },
        429: {
            "description": "频率限制",
            "model": ErrorResponse
        },
        500: {
            "description": "执行失败",
            "model": ErrorResponse
        }
    }
)
async def execute_tool(
    tool_name: str = Path(..., description="工具名称"),
    request: ToolExecutionRequest = ...,
    db: Session = Depends(get_db),
    executed_by: Optional[str] = None,  # 可以从认证中间件获取
    workflow_execution_id: Optional[str] = None  # 可以从请求头获取
) -> ToolExecutionResponse:
    """
    执行工具
    
    - **tool_name**: 工具名称（路径参数）
    - **parameters**: 执行参数（请求体）
    - **timeout**: 超时时间（可选）
    """
    try:
        service = get_tool_service(db)
        
        result = await service.execute_tool(
            tool_name=tool_name,
            parameters=request.parameters,
            executed_by=executed_by,
            workflow_execution_id=workflow_execution_id,
            timeout=request.timeout
        )
        
        return ToolExecutionResponse(
            success=result["success"],
            tool_name=result["tool_name"],
            result=result["result"],
            execution_time=result["execution_time"]
        )
        
    except ValueError as e:
        error_msg = str(e)
        status_code = 400
        if "Rate limit" in error_msg:
            status_code = 429
        elif "not found" in error_msg.lower():
            status_code = 404
        
        raise HTTPException(
            status_code=status_code,
            detail=error_msg
        )
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error executing tool: {str(e)}"
        )


@router.delete(
    "/{tool_name}",
    summary="注销工具",
    description="注销指定的MCP工具（数据库集成版本）",
    responses={
        200: {
            "description": "注销成功"
        },
        404: {
            "description": "工具不存在",
            "model": ErrorResponse
        }
    }
)
async def unregister_tool(
    tool_name: str = Path(..., description="工具名称"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """注销工具"""
    try:
        service = get_tool_service(db)
        success = await service.unregister_tool(tool_name)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        return {
            "success": True,
            "message": f"Tool '{tool_name}' unregistered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering tool: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error unregistering tool: {str(e)}"
        )

