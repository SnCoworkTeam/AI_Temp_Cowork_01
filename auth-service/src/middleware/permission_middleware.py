"""
权限验证中间件
验证用户是否有特定权限
"""
from typing import List, Optional
from fastapi import HTTPException, status, Depends
import logging
from uuid import UUID

from .auth_middleware import get_current_user
from ..services.user_service import user_service
from ..services.permission_service import permission_service

logger = logging.getLogger(__name__)


async def get_user_permissions(user_id: str) -> List[str]:
    """
    获取用户的所有权限（包括角色权限和直接分配的权限）
    
    Args:
        user_id: 用户ID
    
    Returns:
        权限代码列表
    """
    user = await user_service.get_user(user_id)
    if not user:
        return []
    
    permissions = user.get("permissions", []) if isinstance(user, dict) else []
    return list(set(permissions))


async def check_permission(
    permission_code: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    检查用户是否有指定权限
    
    Args:
        permission_code: 权限代码（如 "workflow:execute"）
        current_user: 当前用户（从认证中间件获取）
    
    Returns:
        用户信息
    
    Raises:
        HTTPException: 如果没有权限
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    # 获取用户权限
    user_permissions = await get_user_permissions(user_id)
    
    # 获取权限对象
    permission = await permission_service.get_permission_by_code(permission_code)
    if not permission:
        logger.warning(f"Permission not found: {permission_code}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission_code}' not found"
        )
    
    # 检查是否有权限
    if permission_code not in user_permissions:
        logger.warning(
            f"User {user_id} does not have permission: {permission_code}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {permission_code}"
        )
    
    return current_user


async def require_permissions(
    *permission_codes: str,
    require_all: bool = False
):
    """
    权限要求装饰器（依赖注入函数）
    
    Args:
        *permission_codes: 需要的权限代码列表
        require_all: 是否要求所有权限（默认False，任一即可）
    
    Returns:
        依赖函数
    """
    async def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        user_permissions = await get_user_permissions(user_id)
        
        if require_all:
            # 要求所有权限
            if not all(code in user_permissions for code in permission_codes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required all: {permission_codes}"
                )
        else:
            # 要求任一权限
            if not any(code in user_permissions for code in permission_codes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required any: {permission_codes}"
                )
        
        return current_user
    
    return permission_checker


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求管理员权限
    
    Args:
        current_user: 当前用户
    
    Returns:
        用户信息
    
    Raises:
        HTTPException: 如果不是管理员
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # 检查是否有admin角色 - 直接从数据库查询，不依赖缓存
    has_admin = False
    # user 是字典类型，需要使用字典访问方式
    user_roles = user.get('roles', []) if isinstance(user, dict) else (user.roles if hasattr(user, 'roles') else [])
    
    if user_roles:
        # 直接从数据库查询用户是否有admin角色
        from ..core.database import SessionLocal
        from database.src.models.user_models import User, Role
        from sqlalchemy.orm import joinedload
        
        db = SessionLocal()
        try:
            # 查询用户及其角色（预加载roles关系）
            db_user = db.query(User).options(joinedload(User.roles)).filter(User.id == UUID(user_id)).first()
            if db_user:
                # 检查是否有code为"admin"的角色
                for role in db_user.roles:
                    if role.code == "admin":
                        has_admin = True
                        break
        except Exception as e:
            logger.error(f"Error checking admin role from database: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    if not has_admin:
        logger.warning(f"User {user_id} does not have admin role. User roles: {user_roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user







