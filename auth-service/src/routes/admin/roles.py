"""
角色管理API
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import logging

from ...models.role_models import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
)
from ...services.role_service import role_service
from ...middleware.permission_middleware import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/roles", tags=["角色管理"])


def _role_to_response(role) -> RoleResponse:
    """转换角色为响应模型"""
    permissions = []
    if getattr(role, "permissions", None) is not None:
        for perm in role.permissions:
            if hasattr(perm, "id"):
                permissions.append(str(perm.id))
            else:
                permissions.append(str(perm))

    def _format_dt(value):
        if not value:
            return None
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    return RoleResponse(
        id=str(role.id),
        name=role.name,
        code=role.code,
        description=role.description,
        permissions=permissions,
        is_system=role.is_system,
        created_at=_format_dt(role.created_at),
        updated_at=_format_dt(role.updated_at),
    )


@router.get("", response_model=RoleListResponse)
async def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(require_admin),
):
    """
    获取角色列表
    
    需要管理员权限
    """
    try:
        roles, total = await role_service.list_roles(
            page=page,
            page_size=page_size,
            search=search,
        )
        
        return RoleListResponse(
            roles=[_role_to_response(role) for role in roles],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Failed to list roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list roles: {str(e)}"
        )


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: dict = Depends(require_admin),
):
    """
    创建角色
    
    需要管理员权限
    """
    try:
        # 检查角色代码是否已存在
        existing = await role_service.get_role_by_code(role_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role code '{role_data.code}' already exists"
            )
        
        # 创建角色
        role = await role_service.create_role(role_data.dict())
        
        return _role_to_response(role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: dict = Depends(require_admin),
):
    """
    获取角色详情
    
    需要管理员权限
    """
    try:
        role = await role_service.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_id}' not found"
            )
        
        return _role_to_response(role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get role: {str(e)}"
        )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: dict = Depends(require_admin),
):
    """
    更新角色权限
    
    需要管理员权限
    """
    try:
        role = await role_service.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_id}' not found"
            )
        
        # 更新角色
        updated_role = await role_service.update_role(
            role_id,
            role_data.dict(exclude_unset=True)
        )
        
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role"
            )
        
        return _role_to_response(updated_role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: dict = Depends(require_admin),
):
    """
    删除角色
    
    需要管理员权限
    """
    try:
        success = await role_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_id}' not found or is system role"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )


@router.post("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_permission_to_role(
    role_id: str,
    permission_id: str,
    current_user: dict = Depends(require_admin),
):
    """为角色添加权限"""
    try:
        success = await role_service.add_permission_to_role(role_id, permission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add permission to role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add permission to role: {str(e)}"
        )


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    current_user: dict = Depends(require_admin),
):
    """移除角色权限"""
    try:
        success = await role_service.remove_permission_from_role(role_id, permission_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove permission from role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove permission from role: {str(e)}"
        )





