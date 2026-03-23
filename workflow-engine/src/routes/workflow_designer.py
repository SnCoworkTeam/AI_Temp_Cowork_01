"""
工作流设计器API路由
提供工作流的保存、查询和执行功能
"""
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.workflow_models import (
    WorkflowDefinition,
    WorkflowSaveRequest,
    WorkflowSaveResponse,
    WorkflowDetailResponse,
    WorkflowListResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowNode,
    WorkflowConnection
)
from ..workflows import workflow_manager
from ..workflows.workflow_manager_db import WorkflowManagerDB
from ..dependencies.database import get_db
from shared_libs.luminaos_common.common.error_handler import AppError
from shared_libs.luminaos_common.schemas.base_models import ErrorResponse, PaginatedResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局工作流管理器实例（数据库版本）
_workflow_manager_db: Optional[WorkflowManagerDB] = None


def get_workflow_manager(db: Session = Depends(get_db)) -> WorkflowManagerDB:
    """获取工作流管理器（数据库版本）"""
    return WorkflowManagerDB(db)


@router.post(
    "",
    response_model=WorkflowSaveResponse,
    status_code=201,
    summary="保存工作流设计",
    description="保存或更新工作流设计定义",
    responses={
        201: {
            "description": "工作流保存成功",
            "model": WorkflowSaveResponse
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse
        },
        409: {
            "description": "工作流已存在",
            "model": ErrorResponse
        }
    },
    tags=["Workflow Designer"]
)
async def save_workflow(
    request: WorkflowSaveRequest,
    db: Session = Depends(get_db)
) -> WorkflowSaveResponse:
    """
    保存工作流设计
    
    - **workflow**: 工作流定义（包含节点、连接线等）
    - **overwrite**: 是否覆盖已存在的工作流（默认：False）
    
    返回保存的工作流ID和版本信息。
    """
    try:
        # 验证工作流定义
        workflow = request.workflow
        logger.info(f"Received workflow save request: name={workflow.name}, nodes_count={len(workflow.nodes) if workflow.nodes else 0}")
        
        # 检查必需字段
        if not workflow.name:
            raise HTTPException(
                status_code=400,
                detail="Workflow name is required"
            )
        
        if not workflow.nodes:
            raise HTTPException(
                status_code=400,
                detail="Workflow must have at least one node"
            )
        
        # 验证起始节点（model_validator 应该已经处理了自动推断，这里只做验证）
        node_ids = {node.id for node in workflow.nodes}
        if not workflow.start_node_id:
            # 如果 model_validator 没有设置，这里再次尝试
            start_nodes = [
                node for node in workflow.nodes 
                if (node.node_type.value == "start" if hasattr(node.node_type, 'value') else str(node.node_type) == "start")
            ]
            if start_nodes:
                workflow.start_node_id = start_nodes[0].id
                logger.info(f"Auto-detected start_node_id: {workflow.start_node_id}")
            else:
                # 如果没有 start 节点，使用第一个节点
                workflow.start_node_id = workflow.nodes[0].id
                logger.info(f"No start node found, using first node as start: {workflow.start_node_id}")
        
        if workflow.start_node_id not in node_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Start node '{workflow.start_node_id}' not found in nodes"
            )
        
        # 验证连接线
        for conn in workflow.connections:
            if conn.source.node_id not in node_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Connection source node '{conn.source.node_id}' not found"
                )
            if conn.target.node_id not in node_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Connection target node '{conn.target.node_id}' not found"
                )
        
        # 保存工作流（使用数据库版本）
        manager = get_workflow_manager(db)
        workflow_id = await manager.save_workflow(
            workflow=workflow,
            overwrite=request.overwrite,
            created_by=request.created_by if hasattr(request, 'created_by') else None
        )
        
        logger.info(f"Workflow saved: {workflow.name} (id: {workflow_id})")
        
        return WorkflowSaveResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            message=f"Workflow '{workflow.name}' saved successfully",
            version=workflow.version
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to save workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save workflow: {str(e)}"
        )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowDetailResponse,
    summary="获取工作流定义",
    description="根据工作流ID获取完整的工作流定义，包括节点和连接线",
    responses={
        200: {
            "description": "工作流定义",
            "model": WorkflowDetailResponse
        },
        404: {
            "description": "工作流不存在",
            "model": ErrorResponse
        }
    },
    tags=["Workflow Designer"]
)
async def get_workflow(
    workflow_id: str = Path(...,
        description="工作流ID",
        example="wf-12345678-1234-1234-1234-123456789abc"
    ),
    db: Session = Depends(get_db)
) -> WorkflowDetailResponse:
    """
    获取工作流定义
    
    - **workflow_id**: 工作流ID（路径参数）
    
    返回完整的工作流定义，包括所有节点、连接线和元数据。
    """
    try:
        manager = get_workflow_manager(db)
        workflow_detail = await manager.get_workflow_by_id(workflow_id)
        
        if not workflow_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow with id '{workflow_id}' not found"
            )
        
        return workflow_detail
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow: {str(e)}"
        )


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="列出所有工作流",
    description="获取工作流列表，支持分页和过滤",
    responses={
        200: {
            "description": "工作流列表",
            "model": WorkflowListResponse
        }
    },
    tags=["Workflow Designer"]
)
async def list_workflows(
    page: int = Query(
        1,
        ge=1,
        description="页码",
        example=1
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="每页大小",
        example=20
    ),
    status: Optional[str] = Query(
        None,
        description="按状态过滤",
        example="active"
    ),
    search: Optional[str] = Query(
        None,
        description="搜索关键词（匹配名称或描述）",
        example="sap"
    ),
    db: Session = Depends(get_db)
) -> WorkflowListResponse:
    """
    列出所有工作流
    
    - **page**: 页码（从1开始）
    - **page_size**: 每页大小（1-100）
    - **status**: 按状态过滤（draft, active, inactive, archived）
    - **search**: 搜索关键词（匹配工作流名称或描述）
    """
    try:
        manager = get_workflow_manager(db)
        workflows_data = await manager.list_workflows(
            page=page,
            page_size=page_size,
            status=status,
            search=search
        )
        
        total = await manager.get_workflow_count(
            status=status,
            search=search
        )
        
        return WorkflowListResponse(
            workflows=workflows_data,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflows: {str(e)}"
        )


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
    summary="执行工作流",
    description="执行指定的工作流，支持同步和异步执行",
    responses={
        200: {
            "description": "执行成功",
            "model": WorkflowExecutionResponse
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse
        },
        404: {
            "description": "工作流不存在",
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
    },
    tags=["Workflow Designer"]
)
async def execute_workflow(
    workflow_id: str = Path(
        ...,
        description="工作流ID",
        example="wf-12345678-1234-1234-1234-123456789abc"
    ),
    request: WorkflowExecutionRequest = ...,
    db: Session = Depends(get_db),
    executed_by: Optional[str] = None  # 可以从认证中间件获取
) -> WorkflowExecutionResponse:
    """
    执行工作流
    
    - **workflow_id**: 工作流ID（路径参数）
    - **input_data**: 工作流输入数据（必需）
    - **context**: 执行上下文（可选）
    - **timeout**: 超时时间（秒，默认300，最大3600）
    - **async_execution**: 是否异步执行（默认：False）
    
    返回执行结果和执行ID。
    """
    try:
        # 将路径参数中的 workflow_id 设置到请求对象中（如果请求对象中没有）
        # 由于 Pydantic 模型可能是不可变的，我们需要创建一个新的请求对象
        if not request.workflow_id and not request.workflow_name:
            # 创建新的请求对象，包含 workflow_id
            request_dict = request.model_dump() if hasattr(request, 'model_dump') else request.dict()
            request_dict['workflow_id'] = workflow_id
            request = WorkflowExecutionRequest(**request_dict)
        
        # 验证输入数据（允许空字典）
        if request.input_data is None:
            raise HTTPException(
                status_code=400,
                detail="input_data is required"
            )
        
        # 执行工作流（使用数据库版本）
        manager = get_workflow_manager(db)
        execution_response = await manager.execute_workflow(
            workflow_id=workflow_id,
            request=request,
            executed_by=executed_by
        )
        
        return execution_response
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Workflow execution timeout"
        )
    except Exception as e:
        logger.error(f"Failed to execute workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.patch(
    "/{workflow_id}/status",
    response_model=WorkflowSaveResponse,
    summary="更新工作流状态",
    description="更新工作流的状态（draft, active, inactive, archived）",
    responses={
        200: {
            "description": "状态更新成功",
            "model": WorkflowSaveResponse
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse
        },
        404: {
            "description": "工作流不存在",
            "model": ErrorResponse
        }
    },
    tags=["Workflow Designer"]
)
async def update_workflow_status(
    workflow_id: str = Path(
        ...,
        description="工作流ID",
        example="wf-12345678-1234-1234-1234-123456789abc"
    ),
    status: str = Query(
        ...,
        description="新状态",
        example="active",
        regex="^(draft|active|inactive|archived)$"
    ),
    db: Session = Depends(get_db)
) -> WorkflowSaveResponse:
    """
    更新工作流状态
    
    - **workflow_id**: 工作流ID（路径参数）
    - **status**: 新状态（draft, active, inactive, archived）
    
    返回更新后的工作流信息。
    """
    try:
        manager = get_workflow_manager(db)
        workflow_detail = await manager.get_workflow_by_id(workflow_id)
        
        if not workflow_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow with id '{workflow_id}' not found"
            )
        
        # 更新状态
        updated_workflow = manager.workflow_repo.update_workflow(
            workflow_id=workflow_id,
            status=status
        )
        
        if not updated_workflow:
            raise HTTPException(
                status_code=500,
                detail="Failed to update workflow status"
            )
        
        manager.db.commit()
        
        logger.info(f"Workflow status updated: {workflow_id} -> {status}")
        
        return WorkflowSaveResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_name=workflow_detail.workflow.name,
            message=f"Workflow status updated to '{status}'",
            version=workflow_detail.version
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update workflow status: {str(e)}"
        )


@router.delete(
    "/{workflow_id}",
    status_code=204,
    summary="删除工作流",
    description="删除指定的工作流定义",
    responses={
        204: {
            "description": "工作流删除成功"
        },
        404: {
            "description": "工作流不存在",
            "model": ErrorResponse
        }
    },
    tags=["Workflow Designer"]
)
async def delete_workflow(
    workflow_id: str = Path(
        ...,
        description="工作流ID",
        example="wf-12345678-1234-1234-1234-123456789abc"
    ),
    db: Session = Depends(get_db)
):
    """
    删除工作流
    
    - **workflow_id**: 工作流ID（路径参数）
    """
    try:
        manager = get_workflow_manager(db)
        success = await manager.delete_workflow(workflow_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow with id '{workflow_id}' not found"
            )
        
        logger.info(f"Workflow deleted: {workflow_id}")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workflow: {str(e)}"
        )

