"""
工作流性能指标API路由
提供工作流和节点性能监控数据
"""
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import Optional, Dict, Any
import logging

from ..dependencies.database import get_db
from ..workflows.workflow_manager_db import WorkflowManagerDB
from shared_libs.luminaos_common.schemas.base_models import ErrorResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["工作流性能监控"])


def get_workflow_manager(db: Session = Depends(get_db)) -> WorkflowManagerDB:
    """获取工作流管理器"""
    return WorkflowManagerDB(db)


@router.get(
    "/{workflow_id}/metrics",
    summary="获取工作流性能指标",
    description="获取工作流的整体性能指标",
    responses={
        200: {"description": "性能指标"},
        404: {"description": "工作流不存在", "model": ErrorResponse}
    }
)
async def get_workflow_metrics(
    workflow_id: str = Path(..., description="工作流ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工作流性能指标"""
    try:
        manager = get_workflow_manager(db)
        metrics = manager.get_performance_metrics(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow metrics: {str(e)}"
        )


@router.get(
    "/{workflow_id}/nodes/{node_id}/metrics",
    summary="获取节点性能指标",
    description="获取指定节点的性能指标",
    responses={
        200: {"description": "节点性能指标"},
        404: {"description": "工作流或节点不存在", "model": ErrorResponse}
    }
)
async def get_node_metrics(
    workflow_id: str = Path(..., description="工作流ID"),
    node_id: str = Path(..., description="节点ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取节点性能指标"""
    try:
        manager = get_workflow_manager(db)
        metrics = manager.get_performance_metrics(workflow_id, node_id=node_id)
        
        return {
            "workflow_id": workflow_id,
            "node_id": node_id,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get node metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get node metrics: {str(e)}"
        )


@router.get(
    "/{workflow_id}/statistics",
    summary="获取执行统计",
    description="获取工作流的执行统计数据",
    responses={
        200: {"description": "执行统计"},
        404: {"description": "工作流不存在", "model": ErrorResponse}
    }
)
async def get_execution_statistics(
    workflow_id: str = Path(..., description="工作流ID"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取执行统计"""
    try:
        from datetime import datetime
        from ..repositories.execution_repository import ExecutionRepository
        
        execution_repo = ExecutionRepository(db)
        
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                pass
        
        stats = execution_repo.get_statistics(
            workflow_id=workflow_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "workflow_id": workflow_id,
            "statistics": stats,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution statistics: {str(e)}"
        )









