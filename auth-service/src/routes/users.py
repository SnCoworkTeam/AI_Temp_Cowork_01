"""
用户管理路由
集成数据库的用户信息管理
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from ..dependencies.database import get_db
from ..services.user_service import UserService
from ..middleware.auth_middleware import get_current_user
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["用户"])


# 响应模型
class UserInfo(BaseModel):
    """用户信息"""
    user_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    full_name: Optional[str] = None
    roles: list = []
    permissions: list = []
    status: str
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户信息（包含权限列表）
    
    需要认证，从数据库获取完整用户信息，包括角色和权限
    """
    try:
        user_service = UserService(db)
        user_id = current_user.get("user_id")
        
        user_info = await user_service.get_user(user_id)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserInfo(**user_info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.get("/me/permissions")
async def get_current_user_permissions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的权限列表
    
    返回用户的所有权限代码（包括角色权限和直接分配的权限）
    """
    try:
        user_service = UserService(db)
        user_id = current_user.get("user_id")
        
        user_info = await user_service.get_user(user_id)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 返回权限代码列表
        permissions = user_info.get("permissions", [])
        
        return {
            "user_id": user_id,
            "permissions": permissions,
            "permission_count": len(permissions)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user permissions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户权限失败: {str(e)}"
        )

