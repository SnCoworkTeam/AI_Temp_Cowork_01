"""
工作流版本管理API路由
提供工作流版本的CRUD操作和版本管理功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..services.version_service import VersionService
from ..models.workflow_version import (
    WorkflowVersionCreate,
    WorkflowVersionSchema,
    WorkflowVersionListResponse,
    VersionRestoreRequest
)
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


def get_version_service(db: Session = Depends(get_db)) -> VersionService:
    """获取版本管理服务"""
    return VersionService(db)


@router.post(
    "/workflows/{workflow_id}/versions",
    response_model=WorkflowVersionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="创建工作流新版本",
    description="为工作流创建新版本，新版本会自动设置为当前版本",
    tags=["Workflow Versions"]
)
async def create_workflow_version(
    workflow_id: str,
    version_data: WorkflowVersionCreate,
    service: VersionService = Depends(get_version_service)
):
    """
    创建工作流新版本
    
    - **workflow_id**: 工作流ID
    - **version_data**: 版本数据（必须包含workflow_id，且必须与路径参数一致）
    """
    try:
        # 确保workflow_id一致
        if version_data.workflow_id != workflow_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workflow_id in path and body must match"
            )
        
        return service.create_version(version_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get(
    "/workflows/{workflow_id}/versions",
    response_model=WorkflowVersionListResponse,
    summary="获取工作流版本列表",
    description="获取工作流的所有版本历史，按版本号降序排列",
    tags=["Workflow Versions"]
)
async def get_workflow_versions(
    workflow_id: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    service: VersionService = Depends(get_version_service)
):
    """
    获取工作流版本列表
    
    - **workflow_id**: 工作流ID
    - **skip**: 跳过的记录数（分页）
    - **limit**: 每页记录数（分页）
    """
    try:
        return service.get_versions(workflow_id, skip, limit)
    except Exception as e:
        logger.error(f"Failed to get versions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get versions: {str(e)}"
        )


@router.get(
    "/workflows/{workflow_id}/versions/{version}",
    response_model=WorkflowVersionSchema,
    summary="获取特定版本",
    description="获取工作流的特定版本信息",
    tags=["Workflow Versions"]
)
async def get_workflow_version(
    workflow_id: str,
    version: str,
    service: VersionService = Depends(get_version_service)
):
    """
    获取工作流特定版本
    
    - **workflow_id**: 工作流ID
    - **version**: 版本号
    """
    try:
        result = service.get_version(workflow_id, version)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found for workflow {workflow_id}"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version: {str(e)}"
        )


@router.put(
    "/workflows/{workflow_id}/versions/{version}/set-current",
    response_model=WorkflowVersionSchema,
    summary="设置当前版本",
    description="将指定版本设置为当前活跃版本，其他版本将自动设为非当前版本",
    tags=["Workflow Versions"]
)
async def set_current_version(
    workflow_id: str,
    version: str,
    service: VersionService = Depends(get_version_service)
):
    """
    设置当前版本
    
    - **workflow_id**: 工作流ID
    - **version**: 要设置为当前版本的版本号
    """
    try:
        return service.set_current_version(workflow_id, version)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set current version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set current version: {str(e)}"
        )


@router.post(
    "/workflows/{workflow_id}/versions/{version}/restore",
    response_model=WorkflowVersionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="恢复版本",
    description="基于历史版本创建新版本，新版本会自动设置为当前版本",
    tags=["Workflow Versions"]
)
async def restore_workflow_version(
    workflow_id: str,
    version: str,
    request: VersionRestoreRequest,
    service: VersionService = Depends(get_version_service)
):
    """
    恢复工作流版本
    
    - **workflow_id**: 工作流ID
    - **version**: 要恢复的版本号（必须与路径参数一致）
    - **request**: 恢复请求参数
    """
    try:
        # 确保version一致
        if request.version != version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="version in path and body must match"
            )
        
        return service.restore_version(workflow_id, version, request.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore version: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore version: {str(e)}"
        )


@router.post(
    "/workflows/{workflow_id}/versions/{version}/tags/{tag}",
    response_model=WorkflowVersionSchema,
    summary="添加版本标签",
    description="为工作流版本添加标签（如stable, beta, deprecated等）",
    tags=["Workflow Versions"]
)
async def add_version_tag(
    workflow_id: str,
    version: str,
    tag: str,
    service: VersionService = Depends(get_version_service)
):
    """
    添加版本标签
    
    - **workflow_id**: 工作流ID
    - **version**: 版本号
    - **tag**: 标签名称
    """
    try:
        return service.add_version_tag(workflow_id, version, tag)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add tag: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tag: {str(e)}"
        )


@router.delete(
    "/workflows/{workflow_id}/versions/{version}/tags/{tag}",
    response_model=WorkflowVersionSchema,
    summary="移除版本标签",
    description="移除工作流版本的标签",
    tags=["Workflow Versions"]
)
async def remove_version_tag(
    workflow_id: str,
    version: str,
    tag: str,
    service: VersionService = Depends(get_version_service)
):
    """
    移除版本标签
    
    - **workflow_id**: 工作流ID
    - **version**: 版本号
    - **tag**: 标签名称
    """
    try:
        return service.remove_version_tag(workflow_id, version, tag)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to remove tag: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove tag: {str(e)}"
        )

