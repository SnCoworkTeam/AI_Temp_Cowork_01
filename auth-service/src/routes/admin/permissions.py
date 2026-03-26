"""
权限管理API
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import logging

from ...models.permission_models import (
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionListResponse,
    ResourceType,
    PermissionType,
)
from ...services.permission_service import permission_service
from ...middleware.permission_middleware import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/permissions", tags=["权限管理"])


def _permission_to_response(permission) -> PermissionResponse:
    """转换权限为响应模型"""
    resource_type = getattr(permission, "resource_type", None)
    permission_type = getattr(permission, "permission_type", None)

    if resource_type is None:
        resource_type = getattr(permission, "resource", None)
    if permission_type is None:
        permission_type = getattr(permission, "action", None)

    if resource_type is None or permission_type is None:
        code = getattr(permission, "code", "") or ""
        if ":" in code:
            parts = code.split(":", 1)
            if resource_type is None:
                resource_type = parts[0]
            if permission_type is None:
                permission_type = parts[1]

    if hasattr(resource_type, "value"):
        resource_type = resource_type.value
    if hasattr(permission_type, "value"):
        permission_type = permission_type.value

    def _format_dt(value):
        if not value:
            return None
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    return PermissionResponse(
        id=str(permission.id),
        name=permission.name,
        code=permission.code,
        resource_type=resource_type or "",
        permission_type=permission_type or "",
        description=permission.description,
        created_at=_format_dt(permission.created_at),
        updated_at=_format_dt(permission.updated_at),
    )


@router.get("", response_model=PermissionListResponse)
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    resource_type: Optional[ResourceType] = Query(None, description="资源类型过滤"),
    permission_type: Optional[PermissionType] = Query(None, description="权限类型过滤"),
    current_user: dict = Depends(require_admin),
):
    """
    获取权限列表
    
    需要管理员权限
    """
    try:
        permissions, total = await permission_service.list_permissions(
            page=page,
            page_size=page_size,
            search=search,
            resource_type=resource_type,
            permission_type=permission_type,
        )
        
        return PermissionListResponse(
            permissions=[_permission_to_response(p) for p in permissions],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Failed to list permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list permissions: {str(e)}"
        )


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: dict = Depends(require_admin),
):
    """
    创建权限
    
    需要管理员权限
    """
    try:
        permission = await permission_service.create_permission(permission_data.dict())
        return _permission_to_response(permission)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create permission: {str(e)}"
        )


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    current_user: dict = Depends(require_admin),
):
    """
    获取权限详情
    
    需要管理员权限
    """
    try:
        permission = await permission_service.get_permission(permission_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_id}' not found"
            )
        
        return _permission_to_response(permission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permission: {str(e)}"
        )


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    current_user: dict = Depends(require_admin),
):
    """
    更新权限
    
    需要管理员权限
    """
    try:
        updated_permission = await permission_service.update_permission(
            permission_id,
            permission_data.dict(exclude_unset=True)
        )
        
        if not updated_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_id}' not found"
            )
        
        return _permission_to_response(updated_permission)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update permission: {str(e)}"
        )


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: str,
    current_user: dict = Depends(require_admin),
):
    """
    删除权限
    
    需要管理员权限
    """
    try:
        success = await permission_service.delete_permission(permission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete permission: {str(e)}"
        )







