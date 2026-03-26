"""
MCP工具路由
提供工具注册、查询和执行功能
"""
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.tool_models import (
    ToolRegisterRequest,
    ToolRegisterResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolInfo,
    ToolListResponse,
    ToolStatus,
    ToolDefinition,
    ErrorResponse
)
from ..tools import tool_registry
from ..tools.tool_registry import ToolExecutionError
from ..core.mcp_client import MCPConnectionError, MCPProtocolError
from database.src.core.session import get_db
from sqlalchemy.orm import Session
import base64
import json
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=ToolRegisterResponse,
    status_code=201,
    summary="注册MCP工具",
    description="注册一个新的MCP工具到网关中",
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
async def register_tool(request: ToolRegisterRequest) -> ToolRegisterResponse:
    """
    注册MCP工具
    
    - **tool**: 工具定义（包含名称、描述、参数等）
    - **overwrite**: 是否覆盖已存在的工具（默认：False）
    
    注意：工具会同时注册到内存注册表和数据库，并同步到元数据服务
    """
    try:
        # 1. 先注册到内存注册表（用于执行）
        tool_registry.register_tool(
            tool_def=request.tool,
            overwrite=request.overwrite
        )
        
        # 2. 尝试持久化到数据库和元数据服务（可选，如果失败不影响内存注册）
        try:
            from ..services.tool_service import ToolService
            from database.src.core.session import SessionLocal
            
            # 获取数据库会话
            db = SessionLocal()
            try:
                tool_service = ToolService(db, tool_registry)
                
                # 转换为字典格式
                tool_def_dict = {
                    "name": request.tool.name,
                    "description": request.tool.description,
                    "version": request.tool.version,
                    "tool_type": request.tool.tool_type.value if hasattr(request.tool.tool_type, 'value') else str(request.tool.tool_type),
                    "parameters": request.tool.parameters,
                    "required_parameters": request.tool.required_parameters,
                    "returns": request.tool.returns,
                    "metadata": request.tool.metadata or {}
                }
                
                # 注册到数据库和元数据服务
                result = await tool_service.register_tool(
                    tool_def_dict,
                    overwrite=request.overwrite
                )
                
                if result.get("success"):
                    logger.info(f"Tool '{request.tool.name}' persisted to database and metadata service")
                else:
                    logger.warning(f"Tool '{request.tool.name}' registered in memory but failed to persist: {result.get('message', 'Unknown error')}")
            finally:
                db.close()
        except Exception as e:
            # 如果持久化失败，记录警告但不影响内存注册
            logger.warning(f"Failed to persist tool '{request.tool.name}' to database/metadata: {str(e)}")
        
        return ToolRegisterResponse(
            success=True,
            tool_name=request.tool.name,
            message=f"Tool '{request.tool.name}' registered successfully",
            registered_at=datetime.now()
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400 if "already exists" not in str(e) else 409,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register tool: {str(e)}"
        )


@router.get(
    "",
    response_model=ToolListResponse,
    summary="获取可用工具列表",
    description="获取所有已注册的MCP工具列表，支持分页和过滤",
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
    page: int = Query(
        1,
        ge=1,
        description="页码",
        example=1
    ),
    page_size: int = Query(
        100,
        ge=1,
        le=1000,
        description="每页大小",
        example=100
    )
) -> ToolListResponse:
    """
    获取可用工具列表
    
    - **status**: 按工具状态过滤（active, inactive, deprecated）
    - **tool_type**: 按工具类型过滤（function, api, script, workflow）
    - **page**: 页码（从1开始）
    - **page_size**: 每页大小（1-1000）
    """
    try:
        tools_data = tool_registry.list_tools(
            status=status,
            tool_type=tool_type,
            page=page,
            page_size=page_size
        )
        
        # 转换为ToolInfo对象，修复无效的tool_type
        tools = []
        for tool_data in tools_data:
            # 修复tool_type：如果类型不在枚举中，默认为FUNCTION
            tool_type_value = tool_data.get("tool_type")
            if tool_type_value and tool_type_value not in ["function", "api", "script", "workflow"]:
                logger.warning(f"Tool {tool_data.get('name', 'unknown')} has invalid tool_type '{tool_type_value}', converting to 'function'")
                tool_data = tool_data.copy()
                tool_data["tool_type"] = "function"
            try:
                tools.append(ToolInfo(**tool_data))
            except Exception as e:
                logger.warning(f"Failed to parse tool {tool_data.get('name', 'unknown')}: {e}")
                continue
        
        return ToolListResponse(
            tools=tools,
            total=tool_registry.get_tool_count(),
            page=page,
            page_size=page_size
        )
    
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MCP_SERVER_UNAVAILABLE",
                "message": f"MCP server connection failed: {str(e)}",
                "recovery": "Check if MCP servers are running and network connectivity"
            }
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "MCP_SERVER_TIMEOUT",
                "message": f"MCP server request timeout: {str(e)}",
                "recovery": "Try again later or increase timeout configuration"
            }
        )
    except Exception as e:
        logger.error(f"Failed to list tools: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"Failed to list tools: {str(e)}",
                "recovery": "Contact system administrator"
            }
        )


@router.get(
    "/{tool_name}",
    response_model=ToolInfo,
    summary="获取工具详情",
    description="获取指定工具的详细信息，包括参数定义、返回值等",
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
async def get_tool_info(
    tool_name: str = Path(
        ...,
        description="工具名称",
        example="sap_query",
        min_length=1,
        max_length=100
    )
) -> ToolInfo:
    """
    获取工具详情
    
    - **tool_name**: 工具名称（路径参数）
    """
    tool_info = tool_registry.get_tool_info(tool_name)
    
    if not tool_info:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found"
        )
    
    try:
        return ToolInfo(**tool_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse tool info: {str(e)}"
        )


@router.post(
    "/{tool_name}/execute",
    response_model=ToolExecutionResponse,
    summary="执行工具",
    description="执行指定的MCP工具，需要提供工具所需的参数",
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
        408: {
            "description": "执行超时",
            "model": ErrorResponse
        },
        500: {
            "description": "执行失败",
            "model": ErrorResponse
        }
    }
)
async def execute_tool(
    tool_name: str = Path(
        ...,
        description="工具名称",
        example="sap_query",
        min_length=1,
        max_length=100
    ),
    request: ToolExecutionRequest = ...
) -> ToolExecutionResponse:
    """
    执行工具
    
    - **tool_name**: 工具名称（路径参数）
    - **parameters**: 工具执行参数（必需）
    - **timeout**: 执行超时时间（秒，默认30，最大300）
    - **metadata**: 执行元数据（可选）
    """
    try:
        # 获取工具信息用于结果处理
        tool_info = tool_registry.get_tool_info(tool_name)
        if not tool_info:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "TOOL_NOT_FOUND",
                    "message": f"Tool '{tool_name}' not found",
                    "recovery": "Check tool name or refresh tool list"
                }
            )
        
        # 执行工具
        response = await tool_registry.execute_tool(
            tool_name=tool_name,
            execution_request=request
        )

        # 处理执行结果（根据类型进行转换）
        tool_def = ToolDefinition(**tool_info)
        processed_result = _process_execution_result(response.result, tool_def)
        
        # 构建响应（保留原始结果，添加处理后的元数据）
        return ToolExecutionResponse(
            success=response.success,
            tool_name=response.tool_name,
            result=processed_result.get("result", response.result),
            execution_time=response.execution_time,
            executed_at=datetime.now()
        )
    
    except ToolExecutionError as e:
        status_code = {
            "TOOL_NOT_FOUND": 404,
            "TOOL_INACTIVE": 400,
            "INVALID_PARAMETERS": 400,
            "NO_EXECUTOR": 500,
            "EXECUTION_TIMEOUT": 408,
            "EXECUTION_ERROR": 500,
            "MCP_EXECUTION_ERROR": 502,
            "MCP_CLIENT_NOT_FOUND": 503,
            "MAX_RETRIES_EXCEEDED": 504
        }.get(e.error_code, 500)
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "tool_name": e.tool_name,
                "recovery": _get_recovery_suggestion(e.error_code)
            }
        )
    
    except (MCPConnectionError, ConnectionError) as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "MCP_SERVER_UNAVAILABLE",
                "message": f"MCP server connection failed: {str(e)}",
                "recovery": "Check if MCP servers are running and network connectivity"
            }
        )
    
    except (MCPProtocolError, TimeoutError) as e:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "MCP_SERVER_TIMEOUT",
                "message": f"MCP server request timeout: {str(e)}",
                "recovery": "Try again later or increase timeout configuration"
            }
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
            detail={
                "error": "VALIDATION_ERROR",
                "message": error_msg,
                "recovery": "Check parameter types and requirements"
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in tools endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "recovery": "Contact system administrator"
            }
        )


def _process_execution_result(result: Any, tool: ToolDefinition) -> Dict[str, Any]:
    """
    处理工具执行结果，根据类型进行适当转换
    
    Args:
        result: 执行结果
        tool: 工具定义
    
    Returns:
        处理后的结果字典
    """
    processed_result = {
        "success": True,
        "timestamp": datetime.now().isoformat()
    }
    
    if result is None:
        processed_result["result"] = None
        processed_result["type"] = "void"
    elif isinstance(result, bytes):
        # 二进制数据：base64编码并提供下载信息
        processed_result["result"] = base64.b64encode(result).decode('utf-8')
        processed_result["type"] = "binary"
        processed_result["encoding"] = "base64"
        processed_result["size"] = len(result)
    elif isinstance(result, str):
        # 文本数据
        processed_result["result"] = result
        processed_result["type"] = "text"
        processed_result["size"] = len(result)
    elif isinstance(result, (dict, list)):
        # JSON数据
        processed_result["result"] = result
        processed_result["type"] = "json"
        # 验证结果是否符合工具定义的returns schema
        if tool.returns:
            validation_error = _validate_result_schema(result, tool.returns)
            if validation_error:
                processed_result["schema_warning"] = validation_error
    else:
        # 其他类型尝试JSON序列化
        try:
            processed_result["result"] = json.loads(json.dumps(result, default=str))
            processed_result["type"] = "object"
        except (TypeError, ValueError):
            processed_result["result"] = str(result)
            processed_result["type"] = "string"
    
    return processed_result


def _validate_result_schema(result: Any, schema: Dict[str, Any]) -> Optional[str]:
    """
    验证结果是否符合工具定义的返回schema
    
    Args:
        result: 执行结果
        schema: 返回schema定义
    
    Returns:
        验证错误消息，如果通过则返回None
    """
    try:
        # 使用JSON Schema验证结果
        if schema.get("type") == "object" and isinstance(result, dict):
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in result:
                    return f"Missing required field in result: {field}"
        
        # 可以集成 jsonschema 库进行更详细的验证
        # import jsonschema
        # jsonschema.validate(result, schema)
        
        return None
    except Exception as e:
        return f"Result schema validation failed: {str(e)}"


def _get_recovery_suggestion(error_code: str) -> str:
    """获取错误恢复建议"""
    suggestions = {
        "TOOL_NOT_FOUND": "Check tool name or refresh tool list",
        "TOOL_INACTIVE": "Tool is currently inactive, contact administrator",
        "INVALID_PARAMETERS": "Check parameter types and requirements",
        "NO_EXECUTOR": "Tool executor not configured, contact administrator",
        "EXECUTION_TIMEOUT": "Try again later or increase timeout configuration",
        "EXECUTION_ERROR": "Check tool implementation or contact administrator",
        "MCP_EXECUTION_ERROR": "MCP server error, check server status",
        "MCP_CLIENT_NOT_FOUND": "MCP client not configured, contact administrator",
        "MAX_RETRIES_EXCEEDED": "Service temporarily unavailable, try again later"
    }
    return suggestions.get(error_code, "Contact system administrator")


@router.delete(
    "/{tool_name}",
    status_code=204,
    summary="注销工具",
    description="从网关中注销指定的工具",
    responses={
        204: {
            "description": "工具注销成功"
        },
        404: {
            "description": "工具不存在",
            "model": ErrorResponse
        }
    }
)
async def unregister_tool(
    tool_name: str = Path(
        ...,
        description="工具名称",
        example="sap_query"
    )
):
    """
    注销工具
    
    - **tool_name**: 工具名称（路径参数）
    """
    success = tool_registry.unregister_tool(tool_name)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found"
        )
    
    return None


@router.get(
    "/{tool_name}/stats",
    summary="获取工具执行统计",
    description="获取指定工具的执行统计信息，包括执行次数、成功率、平均执行时间等",
    responses={
        200: {
            "description": "工具执行统计"
        },
        404: {
            "description": "工具不存在",
            "model": ErrorResponse
        }
    }
)
async def get_tool_stats(
    tool_name: str = Path(..., description="工具名称", example="sap_query")
):
    """
    获取工具执行统计
    
    - **tool_name**: 工具名称
    """
    from ..services.tool_service import get_tool_service
    
    tool_service = get_tool_service()
    tool_info = await tool_service.get_tool_info(tool_name)
    
    if not tool_info:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found"
        )
    
    stats = tool_info.get("statistics", {})
    
    return {
        "tool_name": tool_name,
        "tool_id": tool_info.get("tool_id"),
        "total_executions": stats.get("call_count", 0),
        "successful_executions": stats.get("success_count", 0),
        "failed_executions": stats.get("failure_count", 0),
        "success_rate": stats.get("success_rate", 0.0),
        "average_execution_time": stats.get("avg_duration_seconds", 0.0),
        "last_execution_time": stats.get("last_execution_time")
    }


@router.get(
    "/stats",
    summary="获取所有工具的执行统计",
    description="获取所有工具的执行统计信息汇总",
    responses={
        200: {
            "description": "所有工具的执行统计"
        }
    }
)
async def get_all_tools_stats():
    """
    获取所有工具的执行统计
    """
    from ..services.tool_service import get_tool_service
    
    tool_service = get_tool_service()
    tools = await tool_service.list_tools(limit=1000)
    
    all_stats = []
    total_executions = 0
    
    for tool in tools.get("tools", []):
        tool_name = tool.get("name")
        if tool_name:
            tool_info = await tool_service.get_tool_info(tool_name)
            if tool_info:
                stats = tool_info.get("statistics", {})
                tool_stats = {
                    "tool_name": tool_name,
                    "tool_id": tool_info.get("tool_id"),
                    "total_executions": stats.get("call_count", 0),
                    "successful_executions": stats.get("success_count", 0),
                    "failed_executions": stats.get("failure_count", 0),
                    "success_rate": stats.get("success_rate", 0.0),
                    "average_execution_time": stats.get("avg_duration_seconds", 0.0),
                    "last_execution_time": stats.get("last_execution_time")
                }
                all_stats.append(tool_stats)
                total_executions += tool_stats["total_executions"]
    
    return {
        "tools": all_stats,
        "total_tools": len(all_stats),
        "total_executions": total_executions
    }