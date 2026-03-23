"""
工作流版本管理API路由
提供工作流版本查询和管理功能
"""
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List, Optional, Dict, Any
import logging

from ..dependencies.database import get_db
from ..workflows.workflow_manager_db import WorkflowManagerDB
from shared_libs.luminaos_common.schemas.base_models import ErrorResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["工作流版本管理"])


def get_workflow_manager(db: Session = Depends(get_db)) -> WorkflowManagerDB:
    """获取工作流管理器"""
    return WorkflowManagerDB(db)


@router.get(
    "/{workflow_name}/versions",
    summary="列出工作流版本",
    description="获取指定工作流的所有版本列表",
    responses={
        200: {"description": "版本列表"},
        404: {"description": "工作流不存在", "model": ErrorResponse}
    }
)
async def list_workflow_versions(
    workflow_name: str = Path(..., description="工作流名称"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """列出工作流的所有版本"""
    try:
        manager = get_workflow_manager(db)
        versions = await manager.list_versions(workflow_name)
        
        if not versions:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found"
            )
        
        return {
            "workflow_name": workflow_name,
            "versions": versions,
            "total": len(versions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list workflow versions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflow versions: {str(e)}"
        )


@router.get(
    "/{workflow_name}/versions/latest",
    summary="获取最新版本",
    description="获取工作流的最新版本",
    responses={
        200: {"description": "工作流定义"},
        404: {"description": "工作流不存在", "model": ErrorResponse}
    }
)
async def get_latest_version(
    workflow_name: str = Path(..., description="工作流名称"),
    db: Session = Depends(get_db)
):
    """获取工作流的最新版本"""
    try:
        manager = get_workflow_manager(db)
        workflow_detail = await manager.get_workflow_by_name(workflow_name)
        
        if not workflow_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found"
            )
        
        return workflow_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest version: {str(e)}"
        )


@router.get(
    "/{workflow_name}/versions/{version}",
    summary="获取指定版本",
    description="获取工作流的指定版本",
    responses={
        200: {"description": "工作流定义"},
        404: {"description": "工作流或版本不存在", "model": ErrorResponse}
    }
)
async def get_workflow_version(
    workflow_name: str = Path(..., description="工作流名称"),
    version: str = Path(..., description="版本号"),
    db: Session = Depends(get_db)
):
    """获取工作流的指定版本"""
    try:
        manager = get_workflow_manager(db)
        workflow_detail = await manager.get_workflow_by_name(workflow_name, version=version)
        
        if not workflow_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' version '{version}' not found"
            )
        
        return workflow_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow version: {str(e)}"
        )


@router.post(
    "/{workflow_name}/versions",
    summary="创建新版本",
    description="基于现有工作流创建新版本",
    responses={
        201: {"description": "新版本创建成功"},
        400: {"description": "请求参数错误", "model": ErrorResponse},
        404: {"description": "工作流不存在", "model": ErrorResponse}
    }
)
async def create_new_version(
    workflow_name: str = Path(..., description="工作流名称"),
    db: Session = Depends(get_db),
    created_by: Optional[str] = None  # 可以从认证中间件获取
):
    """创建工作流新版本"""
    try:
        # 获取当前版本
        manager = get_workflow_manager(db)
        current_workflow = await manager.get_workflow_by_name(workflow_name)
        
        if not current_workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found"
            )
        
        # 创建新版本（需要传入工作流定义）
        # 这里需要从请求体获取新的工作流定义
        # 暂时返回错误，提示需要传入完整定义
        raise HTTPException(
            status_code=400,
            detail="Please use POST /api/workflows to create a new version with workflow definition"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create new version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create new version: {str(e)}"
        )









