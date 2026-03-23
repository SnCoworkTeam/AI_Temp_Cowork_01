"""
用户管理API
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import logging

from ...models.user_models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    UserListResponse,
    UserStatus,
)
from ...services.user_service import UserService
from ...services.auth_service import AuthService, pwd_context
from ...services.role_service import role_service
from ...services.permission_service import permission_service
from ...middleware.permission_middleware import require_admin
from ...dependencies.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/users", tags=["用户管理"])


def _user_to_response(user) -> UserResponse:
    """转换用户为响应模型"""
    if isinstance(user, dict):
        return UserResponse(
            user_id=user.get("user_id", ""),
            username=user.get("username", ""),
            email=user.get("email", ""),
            display_name=user.get("display_name"),
            roles=user.get("roles", []),
            permissions=user.get("permissions", []),
            status=user.get("status", "active"),
            last_login_at=user.get("last_login_at"),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
        )

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        roles=user.roles,
        permissions=user.permissions,
        status=user.status.value if hasattr(user.status, "value") else user.status,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[UserStatus] = Query(None, description="状态过滤"),
    role: Optional[str] = Query(None, description="角色过滤"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    获取用户列表（分页、搜索）
    
    需要管理员权限
    """
    try:
        # 使用依赖注入的数据库会话创建UserService实例
        user_service = UserService(db)
        users, total = await user_service.list_users(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            role=role,
        )
        
        # user_service.list_users 返回的是字典列表，需要转换为UserResponse
        user_responses = []
        for user_dict in users:
            # user_dict 已经是字典格式，包含 user_id, username, email 等字段
            user_responses.append(UserResponse(
                user_id=user_dict.get("user_id", ""),
                username=user_dict.get("username", ""),
                email=user_dict.get("email", ""),
                display_name=user_dict.get("display_name"),
                roles=user_dict.get("roles", []),
                permissions=user_dict.get("permissions", []),
                status=user_dict.get("status", "active"),
                last_login_at=user_dict.get("last_login_at"),
                created_at=user_dict.get("created_at"),
                updated_at=user_dict.get("updated_at"),
            ))
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    创建用户
    
    需要管理员权限
    """
    try:
        user_service = UserService(db)
        auth_service = AuthService(db)

        password_error = auth_service._validate_password(user_data.password)
        if password_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=password_error
            )

        password_hash = pwd_context.hash(user_data.password)
        payload = user_data.dict(exclude={"password"})
        payload["password_hash"] = password_hash

        # 检查用户名是否已存在
        existing = await user_service.get_user_by_username(user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' already exists"
            )
        
        # 检查邮箱是否已存在
        existing = await user_service.get_user_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' already exists"
            )
        
        # 创建用户
        user, error_msg = await user_service.create_user(payload)
        if error_msg:
            status_code = status.HTTP_400_BAD_REQUEST
            if error_msg.startswith("创建用户失败"):
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            raise HTTPException(
                status_code=status_code,
                detail=error_msg
            )

        return _user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    获取用户详情
    
    需要管理员权限
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found"
            )
        
        # 获取角色详情
        role_details = []
        for role_id in user.get("roles", []):
            role = await role_service.get_role(role_id)
            if role:
                role_details.append({
                    "id": str(role.id),
                    "name": role.name,
                    "code": role.code,
                })
        
        # 获取权限详情
        permission_details = []
        all_permissions = set(user.get("permissions", []))
        for permission_code in all_permissions:
            permission = await permission_service.get_permission_by_code(permission_code)
            if permission:
                permission_details.append({
                    "id": str(permission.id),
                    "name": permission.name,
                    "code": permission.code,
                })
        
        return UserDetailResponse(
            user_id=user.get("user_id", ""),
            username=user.get("username", ""),
            email=user.get("email", ""),
            display_name=user.get("display_name"),
            roles=user.get("roles", []),
            permissions=user.get("permissions", []),
            status=user.get("status", "active"),
            last_login_at=user.get("last_login_at"),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
            metadata=user.get("metadata", {}),
            role_details=role_details,
            permission_details=permission_details,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    更新用户信息
    
    需要管理员权限
    """
    try:
        user_service = UserService(db)
        auth_service = AuthService(db)

        # 检查用户是否存在
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found"
            )
        
        # 检查用户名是否冲突
        if user_data.username and user_data.username != user.get("username"):
            existing = await user_service.get_user_by_username(user_data.username)
            if existing and existing.get("user_id") != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{user_data.username}' already exists"
                )
        
        # 检查邮箱是否冲突
        if user_data.email and user_data.email != user.get("email"):
            existing = await user_service.get_user_by_email(user_data.email)
            if existing and existing.get("user_id") != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_data.email}' already exists"
                )

        updates = user_data.dict(exclude_unset=True)
        if "password" in updates and updates["password"]:
            password_error = auth_service._validate_password(updates["password"])
            if password_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=password_error
                )
            updates["password_hash"] = pwd_context.hash(updates["password"])
            updates.pop("password", None)
        
        # 更新用户
        updated_user, error_msg = await user_service.update_user(
            user_id,
            updates
        )
        
        if error_msg or not updated_user:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if error_msg in {"用户名已存在", "邮箱已被注册"}:
                status_code = status.HTTP_400_BAD_REQUEST
            if error_msg == "用户不存在":
                status_code = status.HTTP_404_NOT_FOUND
            raise HTTPException(
                status_code=status_code,
                detail=error_msg or "Failed to update user"
            )
        
        return _user_to_response(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    删除用户（软删除）
    
    需要管理员权限
    """
    try:
        user_service = UserService(db)
        success, error_msg = await user_service.delete_user(user_id)
        if not success:
            if error_msg == "用户不存在":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User '{user_id}' not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg or f"Failed to delete user '{user_id}'"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_role_to_user(
    user_id: str,
    role_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """为用户添加角色"""
    try:
        user_service = UserService(db)
        success, error_msg = await user_service.assign_role(user_id, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg or f"User '{user_id}' or role '{role_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add role to user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add role to user: {str(e)}"
        )


@router.delete("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """移除用户角色"""
    try:
        user_service = UserService(db)
        success, error_msg = await user_service.remove_role(user_id, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg or f"User '{user_id}' or role '{role_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove role from user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove role from user: {str(e)}"
        )

