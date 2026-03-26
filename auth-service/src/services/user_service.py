"""
用户服务
管理用户数据存储和业务逻辑（集成数据库）
"""
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..repositories.user_repository import UserRepository
from ..sso.cache_manager import cache_manager
from ..core.database import get_async_redis
from database.src.models.user_models import User as DBUser

logger = logging.getLogger(__name__)


class UserService:
    """用户服务（集成数据库）"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self._user_cache_prefix = "user:info:"
        self._user_list_cache_key = "users:all"
    
    async def create_user(self, user_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        创建用户
        
        Args:
            user_data: 用户数据
        
        Returns:
            (用户信息字典, 错误消息)
        """
        try:
            # 检查用户名和邮箱是否已存在
            if self.user_repo.get_by_username(user_data.get("username", "")):
                return None, "用户名已存在"
            
            if self.user_repo.get_by_email(user_data.get("email", "")):
                return None, "邮箱已被注册"

            password_hash = user_data.get("password_hash")
            if not password_hash:
                return None, "密码不能为空"
            
            # 创建用户
            db_user = self.user_repo.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=password_hash,
                full_name=user_data.get("display_name") or user_data.get("full_name"),
                user_metadata=user_data.get("metadata"),
                status=user_data.get("status", "active")
            )
            
            self.db.commit()
            
            # 缓存用户信息
            await self._cache_user_info(db_user)
            
            logger.info(f"User created: {db_user.id} ({db_user.username})")
            
            return self._user_to_dict(db_user), None
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            self.db.rollback()
            return None, f"创建用户失败: {str(e)}"
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息字典，如果不存在则返回None
        """
        try:
            # 尝试从缓存获取
            cached_user = await self._get_cached_user(user_id)
            if cached_user:
                return cached_user
            
            # 从数据库获取
            db_user = self.user_repo.get_by_id(user_id)
            if not db_user:
                return None
            
            # 缓存用户信息
            await self._cache_user_info(db_user)
            
            return self._user_to_dict(db_user)
            
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}", exc_info=True)
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        try:
            db_user = self.user_repo.get_by_username(username)
            if not db_user:
                return None
            
            # 缓存用户信息
            await self._cache_user_info(db_user)
            
            return self._user_to_dict(db_user)
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}", exc_info=True)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        try:
            db_user = self.user_repo.get_by_email(email)
            if not db_user:
                return None
            
            # 缓存用户信息
            await self._cache_user_info(db_user)
            
            return self._user_to_dict(db_user)
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}", exc_info=True)
            return None
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        更新用户
        
        Args:
            user_id: 用户ID
            updates: 更新数据
        
        Returns:
            (更新后的用户信息字典, 错误消息)
        """
        try:
            db_user = self.user_repo.get_by_id(user_id)
            if not db_user:
                return None, "用户不存在"
            
            # 如果更新用户名或邮箱，检查是否冲突
            if "username" in updates:
                existing = self.user_repo.get_by_username(updates["username"])
                if existing and str(existing.id) != user_id:
                    return None, "用户名已存在"
            
            if "email" in updates:
                existing = self.user_repo.get_by_email(updates["email"])
                if existing and str(existing.id) != user_id:
                    return None, "邮箱已被注册"
            
            # 转换字段名（display_name -> full_name）
            db_updates = {}
            if "display_name" in updates:
                db_updates["full_name"] = updates["display_name"]
            elif "full_name" in updates:
                db_updates["full_name"] = updates["full_name"]
            
            if "status" in updates:
                db_updates["status"] = updates["status"]
            
            if "email" in updates:
                db_updates["email"] = updates["email"]
            
            if "username" in updates:
                db_updates["username"] = updates["username"]

            if "password_hash" in updates:
                db_updates["password_hash"] = updates["password_hash"]

            if "metadata" in updates:
                db_updates["user_metadata"] = updates["metadata"]
            
            # 更新用户
            updated_user = self.user_repo.update_user(user_id, **db_updates)
            if not updated_user:
                return None, "更新用户失败"
            
            self.db.commit()
            
            # 清除缓存
            await self._clear_user_cache(user_id)
            
            # 重新缓存
            await self._cache_user_info(updated_user)
            
            logger.info(f"User updated: {user_id}")
            
            return self._user_to_dict(updated_user), None
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}", exc_info=True)
            self.db.rollback()
            return None, f"更新用户失败: {str(e)}"
    
    async def delete_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        删除用户（软删除）
        
        Args:
            user_id: 用户ID
        
        Returns:
            (是否成功, 错误消息)
        """
        try:
            success = self.user_repo.delete_user(user_id)
            if not success:
                return False, "用户不存在"
            
            self.db.commit()
            
            # 清除缓存
            await self._clear_user_cache(user_id)
            
            logger.info(f"User deleted: {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            self.db.rollback()
            return False, f"删除用户失败: {str(e)}"
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        role: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        列出用户
        
        Args:
            page: 页码
            page_size: 每页大小
            search: 搜索关键词
            status: 状态过滤
            role: 角色过滤
        
        Returns:
            (用户列表, 总数)
        """
        try:
            skip = (page - 1) * page_size
            
            logger.info(f"list_users called: page={page}, page_size={page_size}, search={search}, status={status}, role={role}")
            
            # 从数据库获取
            users = self.user_repo.list_users(
                skip=skip,
                limit=page_size,
                search=search,
                status=status
            )
            
            logger.info(f"list_users: got {len(users)} users from repository")
            
            # 角色过滤（如果指定）
            if role:
                users = [u for u in users if any(str(r.id) == role for r in u.roles)]
                logger.info(f"list_users: after role filter, {len(users)} users remain")
            
            # 转换为字典
            user_dicts = [self._user_to_dict(u) for u in users]
            logger.info(f"list_users: converted to {len(user_dicts)} user dicts")
            
            # 获取总数：需要查询数据库获取实际总数
            # 构建查询以获取总数（与list_users使用相同的过滤条件）
            from database.src.models.user_models import UserStatus as DBUserStatus
            from sqlalchemy import func
            
            total_query = self.db.query(func.count(DBUser.id))
            
            # 状态过滤
            if status:
                try:
                    total_query = total_query.filter(DBUser.status == DBUserStatus[status.upper()])
                    logger.info(f"list_users: applied status filter: {status}")
                except KeyError:
                    logger.warning(f"list_users: invalid status value: {status}")
                    pass
            
            # 搜索过滤
            if search:
                total_query = total_query.filter(
                    or_(
                        DBUser.username.ilike(f"%{search}%"),
                        DBUser.email.ilike(f"%{search}%"),
                        DBUser.full_name.ilike(f"%{search}%")
                    )
                )
                logger.info(f"list_users: applied search filter: {search}")
            
            total = total_query.scalar() or 0
            logger.info(f"list_users: total count = {total}")
            
            return user_dicts, total
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True)
            return [], 0
    
    async def assign_role(self, user_id: str, role_id: str) -> Tuple[bool, Optional[str]]:
        """为用户添加角色"""
        try:
            success = self.user_repo.assign_role(user_id, role_id)
            if not success:
                return False, "分配角色失败"
            
            self.db.commit()
            
            # 清除缓存
            await self._clear_user_cache(user_id)
            
            logger.info(f"Role {role_id} assigned to user {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error assigning role: {str(e)}", exc_info=True)
            self.db.rollback()
            return False, f"分配角色失败: {str(e)}"
    
    async def remove_role(self, user_id: str, role_id: str) -> Tuple[bool, Optional[str]]:
        """移除用户角色"""
        try:
            success = self.user_repo.remove_role(user_id, role_id)
            if not success:
                return False, "移除角色失败"
            
            self.db.commit()
            
            # 清除缓存
            await self._clear_user_cache(user_id)
            
            logger.info(f"Role {role_id} removed from user {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error removing role: {str(e)}", exc_info=True)
            self.db.rollback()
            return False, f"移除角色失败: {str(e)}"
    
    def _user_to_dict(self, db_user) -> Dict[str, Any]:
        """将数据库用户模型转换为字典"""
        return {
            "user_id": str(db_user.id),
            "username": db_user.username,
            "email": db_user.email,
            "display_name": db_user.full_name,
            "full_name": db_user.full_name,
            "status": db_user.status.value if hasattr(db_user.status, 'value') else str(db_user.status),
            "roles": [str(r.id) for r in db_user.roles],
            "permissions": [p.code for p in self.user_repo.get_user_permissions(str(db_user.id))],
            "metadata": db_user.user_metadata or {},
            "last_login_at": db_user.last_login_at.isoformat() if db_user.last_login_at else None,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
            "updated_at": db_user.updated_at.isoformat() if db_user.updated_at else None,
        }
    
    async def _cache_user_info(self, db_user):
        """缓存用户信息到Redis"""
        try:
            user_key = f"{self._user_cache_prefix}{db_user.id}"
            user_data = self._user_to_dict(db_user)
            await cache_manager.set(user_key, user_data, ttl=3600)  # 1小时
        except Exception as e:
            logger.warning(f"Failed to cache user info: {str(e)}")
    
    async def _get_cached_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从缓存获取用户信息"""
        try:
            user_key = f"{self._user_cache_prefix}{user_id}"
            return await cache_manager.get(user_key)
        except Exception as e:
            logger.warning(f"Failed to get cached user: {str(e)}")
            return None
    
    async def _clear_user_cache(self, user_id: str):
        """清除用户缓存"""
        try:
            user_key = f"{self._user_cache_prefix}{user_id}"
            await cache_manager.delete(user_key)
        except Exception as e:
            logger.warning(f"Failed to clear user cache: {str(e)}")


# 创建全局 user_service 实例的工厂函数
def get_user_service() -> UserService:
    """获取 UserService 实例（每次创建新实例，使用新的数据库会话）"""
    from ..core.database import SessionLocal
    db = SessionLocal()
    return UserService(db)


# 为了向后兼容，创建一个全局实例（延迟初始化）
_user_service_instance: Optional[UserService] = None


def get_user_service_singleton() -> UserService:
    """获取单例 UserService 实例（不推荐，但为了兼容性保留）"""
    global _user_service_instance
    if _user_service_instance is None:
        from ..core.database import SessionLocal
        db = SessionLocal()
        _user_service_instance = UserService(db)
    return _user_service_instance


# 创建全局 user_service 实例（使用 SessionLocal 获取会话）
from ..core.database import SessionLocal
_user_service_db = SessionLocal()
user_service = UserService(_user_service_db)
