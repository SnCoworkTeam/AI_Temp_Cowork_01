"""
用户Repository
用户数据访问层，适配auth-service需求
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.user_models import User as DBUser, Role, UserStatus as DBUserStatus
from database.src.repositories.user_repository import UserRepository as DBUserRepository

logger = logging.getLogger(__name__)


class UserRepository:
    """用户Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBUserRepository(session)
    
    def get_by_id(self, user_id: str) -> Optional[DBUser]:
        """根据ID获取用户（支持UUID字符串），并预加载roles关系"""
        try:
            # 尝试解析为UUID
            uuid_id = UUID(user_id) if isinstance(user_id, str) else user_id
            from sqlalchemy.orm import joinedload
            # 使用joinedload预加载roles关系
            user = self.session.query(DBUser).options(
                joinedload(DBUser.roles)
            ).filter(DBUser.id == uuid_id).first()
            return user
        except (ValueError, TypeError):
            # 如果不是UUID格式，返回None
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
    
    def get_by_username(self, username: str) -> Optional[DBUser]:
        """根据用户名获取用户，并预加载roles关系"""
        from sqlalchemy.orm import joinedload
        # 使用joinedload预加载roles关系
        user = self.session.query(DBUser).options(
            joinedload(DBUser.roles)
        ).filter(DBUser.username == username).first()
        return user
    
    def get_by_email(self, email: str) -> Optional[DBUser]:
        """根据邮箱获取用户，并预加载roles关系"""
        from sqlalchemy.orm import joinedload
        # 使用joinedload预加载roles关系
        user = self.session.query(DBUser).options(
            joinedload(DBUser.roles)
        ).filter(DBUser.email == email).first()
        return user
    
    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        user_metadata: Optional[dict] = None,
        status: str = "active"
    ) -> DBUser:
        """创建用户"""
        try:
            # 转换状态
            db_status = DBUserStatus.ACTIVE
            if status == "inactive":
                db_status = DBUserStatus.INACTIVE
            elif status == "suspended":
                db_status = DBUserStatus.SUSPENDED
            elif status == "deleted":
                db_status = DBUserStatus.DELETED
            
            user = DBUser(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                user_metadata=user_metadata,
                status=db_status
            )
            self.session.add(user)
            self.session.flush()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user: {str(e)}")
            self.session.rollback()
            raise
    
    def update_user(
        self,
        user_id: str,
        **updates
    ) -> Optional[DBUser]:
        """更新用户"""
        try:
            uuid_id = UUID(user_id) if isinstance(user_id, str) else user_id
            return self._db_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        try:
            uuid_id = UUID(user_id) if isinstance(user_id, str) else user_id
            user = self._db_repo.get_by_id(uuid_id)
            if user:
                user.status = DBUserStatus.DELETED
                self.session.flush()
                return True
            return False
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid user_id format: {user_id}, error: {str(e)}")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting user {user_id}: {str(e)}")
            self.session.rollback()
            raise
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[DBUser]:
        """列出用户"""
        try:
            filters = {}
            if status:
                try:
                    filters["status"] = DBUserStatus[status.upper()]
                except KeyError:
                    pass
            
            # 构建查询
            query = self.session.query(DBUser)
            
            # 状态过滤
            if status:
                try:
                    query = query.filter(DBUser.status == DBUserStatus[status.upper()])
                except KeyError:
                    pass
            
            # 搜索过滤
            if search:
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        DBUser.username.ilike(f"%{search}%"),
                        DBUser.email.ilike(f"%{search}%"),
                        DBUser.full_name.ilike(f"%{search}%")
                    )
                )
            
            # 应用排序（按创建时间倒序）
            query = query.order_by(DBUser.created_at.desc())
            
            # 应用分页
            users = query.offset(skip).limit(limit).all()
            
            logger.info(f"list_users: found {len(users)} users (skip={skip}, limit={limit}, search={search}, status={status})")
            
            return users
        except SQLAlchemyError as e:
            logger.error(f"Error listing users: {str(e)}")
            raise
    
    def assign_role(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            role_uuid = UUID(role_id) if isinstance(role_id, str) else role_id
            return self._db_repo.assign_role(user_uuid, role_uuid)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid ID format: {str(e)}")
            return False
    
    def remove_role(self, user_id: str, role_id: str) -> bool:
        """移除用户角色"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            role_uuid = UUID(role_id) if isinstance(role_id, str) else role_id
            return self._db_repo.remove_role(user_uuid, role_uuid)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid ID format: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id: str) -> List:
        """获取用户的所有权限（包括角色权限）"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            return self._db_repo.get_user_permissions(user_uuid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return []








