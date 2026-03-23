"""
工作流执行管理API路由
提供执行历史查询、回放、状态恢复等功能
"""
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List, Optional, Dict, Any
import logging

from ..dependencies.database import get_db
from ..workflows.workflow_manager_db import WorkflowManagerDB
from shared_libs.luminaos_common.schemas.base_models import ErrorResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["工作流执行"])


def get_workflow_manager(db: Session = Depends(get_db)) -> WorkflowManagerDB:
    """获取工作流管理器"""
    return WorkflowManagerDB(db)


@router.get(
    "/{execution_id}",
    summary="获取执行状态",
    description="获取工作流执行的详细状态信息",
    responses={
        200: {"description": "执行状态"},
        404: {"description": "执行不存在", "model": ErrorResponse}
    }
)
async def get_execution_status(
    execution_id: str = Path(..., description="执行ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取执行状态"""
    try:
        manager = get_workflow_manager(db)
        status = await manager.get_execution_status(execution_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Execution '{execution_id}' not found"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution status: {str(e)}"
        )


@router.get(
    "",
    summary="获取执行历史",
    description="获取工作流执行历史列表，支持按工作流或用户过滤",
    responses={
        200: {"description": "执行历史列表"}
    }
)
async def get_execution_history(
    workflow_id: Optional[str] = Query(None, description="工作流ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取执行历史"""
    try:
        manager = get_workflow_manager(db)
        skip = (page - 1) * page_size
        
        executions = await manager.get_execution_history(
            workflow_id=workflow_id,
            user_id=user_id,
            skip=skip,
            limit=page_size
        )
        
        return {
            "executions": executions,
            "page": page,
            "page_size": page_size,
            "total": len(executions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution history: {str(e)}"
        )


@router.post(
    "/{execution_id}/replay",
    summary="回放执行",
    description="使用相同的输入重新执行工作流",
    responses={
        200: {"description": "回放结果"},
        404: {"description": "执行不存在", "model": ErrorResponse}
    }
)
async def replay_execution(
    execution_id: str = Path(..., description="执行ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """回放执行"""
    try:
        manager = get_workflow_manager(db)
        result = await manager.replay_execution(execution_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to replay execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to replay execution: {str(e)}"
        )


@router.post(
    "/{execution_id}/resume",
    summary="恢复执行",
    description="从检查点恢复工作流执行",
    responses={
        200: {"description": "恢复执行结果"},
        404: {"description": "执行或检查点不存在", "model": ErrorResponse}
    }
)
async def resume_execution(
    execution_id: str = Path(..., description="执行ID"),
    checkpoint_name: Optional[str] = Query(None, description="检查点名称（默认最新）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """从检查点恢复执行"""
    try:
        manager = get_workflow_manager(db)
        result = await manager.resume_execution(execution_id, checkpoint_name)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to resume execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume execution: {str(e)}"
        )


@router.get(
    "/{execution_id}/checkpoints",
    summary="列出检查点",
    description="列出执行的所有检查点",
    responses={
        200: {"description": "检查点列表"},
        404: {"description": "执行不存在", "model": ErrorResponse}
    }
)
async def list_checkpoints(
    execution_id: str = Path(..., description="执行ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """列出检查点"""
    try:
        from ..core.state_manager import WorkflowStateManager
        
        state_manager = WorkflowStateManager(db)
        checkpoints = await state_manager.list_checkpoints(execution_id)
        
        return {
            "execution_id": execution_id,
            "checkpoints": checkpoints
        }
        
    except Exception as e:
        logger.error(f"Failed to list checkpoints: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list checkpoints: {str(e)}"
        )









