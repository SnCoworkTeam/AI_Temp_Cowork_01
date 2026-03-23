"""
用户Repository
用户、角色、权限管理
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from ..models.user_models import User, Role, Permission, UserStatus
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """用户Repository"""
    
    def __init__(self, session: Session):
        super().__init__(User, session)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户实例或None
        """
        try:
            # 刷新会话，确保能查询到刚创建的用户
            self.session.expire_all()
            return self.session.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            raise
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            用户实例或None
        """
        try:
            # 刷新会话，确保能查询到刚创建的用户
            self.session.expire_all()
            return self.session.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise
    
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        获取活跃用户列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            活跃用户列表
        """
        try:
            return self.session.query(User).filter(
                User.status == UserStatus.ACTIVE
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active users: {str(e)}")
            raise
    
    def assign_role(self, user_id: UUID, role_id: UUID) -> bool:
        """
        为用户分配角色
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            是否分配成功
        """
        try:
            user = self.get_by_id(user_id)
            role = self.session.query(Role).filter(Role.id == role_id).first()
            
            if user and role and role not in user.roles:
                user.roles.append(role)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error assigning role {role_id} to user {user_id}: {str(e)}")
            self.session.rollback()
            raise
    
    def remove_role(self, user_id: UUID, role_id: UUID) -> bool:
        """
        移除用户角色
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            是否移除成功
        """
        try:
            user = self.get_by_id(user_id)
            if user:
                role = self.session.query(Role).filter(Role.id == role_id).first()
                if role and role in user.roles:
                    user.roles.remove(role)
                    self.session.flush()
                    return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error removing role {role_id} from user {user_id}: {str(e)}")
            self.session.rollback()
            raise
    
    def get_user_permissions(self, user_id: UUID) -> List[Permission]:
        """
        获取用户的所有权限（包括角色权限）
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限列表
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return []
            
            permissions = set()
            
            # 获取角色权限
            for role in user.roles:
                permissions.update(role.permissions)
            
            # 获取直接分配的权限（如果有）
            # 注意：User模型中可能没有直接的permissions关系，这里假设通过角色获取
            
            return list(permissions)
        except SQLAlchemyError as e:
            logger.error(f"Error getting permissions for user {user_id}: {str(e)}")
            raise


class RoleRepository(BaseRepository[Role]):
    """角色Repository"""
    
    def __init__(self, session: Session):
        super().__init__(Role, session)
    
    def get_by_code(self, code: str) -> Optional[Role]:
        """
        根据角色代码获取角色
        
        Args:
            code: 角色代码
            
        Returns:
            角色实例或None
        """
        try:
            return self.session.query(Role).filter(Role.code == code).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting role by code {code}: {str(e)}")
            raise
    
    def assign_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """
        为角色分配权限
        
        Args:
            role_id: 角色ID
            permission_id: 权限ID
            
        Returns:
            是否分配成功
        """
        try:
            role = self.get_by_id(role_id)
            permission = self.session.query(Permission).filter(Permission.id == permission_id).first()
            
            if role and permission and permission not in role.permissions:
                role.permissions.append(permission)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error assigning permission {permission_id} to role {role_id}: {str(e)}")
            self.session.rollback()
            raise
    
    def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        """
        移除角色权限
        
        Args:
            role_id: 角色ID
            permission_id: 权限ID
            
        Returns:
            是否移除成功
        """
        try:
            role = self.get_by_id(role_id)
            if role:
                permission = self.session.query(Permission).filter(Permission.id == permission_id).first()
                if permission and permission in role.permissions:
                    role.permissions.remove(permission)
                    self.session.flush()
                    return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error removing permission {permission_id} from role {role_id}: {str(e)}")
            self.session.rollback()
            raise


class PermissionRepository(BaseRepository[Permission]):
    """权限Repository"""
    
    def __init__(self, session: Session):
        super().__init__(Permission, session)
    
    def get_by_code(self, code: str) -> Optional[Permission]:
        """
        根据权限代码获取权限
        
        Args:
            code: 权限代码
            
        Returns:
            权限实例或None
        """
        try:
            return self.session.query(Permission).filter(Permission.code == code).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting permission by code {code}: {str(e)}")
            raise

