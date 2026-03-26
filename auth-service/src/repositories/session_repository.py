"""
会话Repository
用户会话数据访问层
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.user_models import UserSession as DBUserSession

logger = logging.getLogger(__name__)


class SessionRepository:
    """会话Repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_session(
        self,
        user_id: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_at: datetime = None
    ) -> DBUserSession:
        """创建会话"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            
            db_session = DBUserSession(
                user_id=user_uuid,
                access_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                is_active=True
            )
            self.session.add(db_session)
            self.session.flush()
            return db_session
        except SQLAlchemyError as e:
            logger.error(f"Error creating session: {str(e)}")
            self.session.rollback()
            raise
    
    def get_session_by_id(self, session_id: str) -> Optional[DBUserSession]:
        """根据会话ID获取会话"""
        try:
            uuid_id = UUID(session_id) if isinstance(session_id, str) else session_id
            return self.session.query(DBUserSession).filter(
                DBUserSession.id == uuid_id
            ).first()
        except (ValueError, TypeError):
            logger.warning(f"Invalid session_id format: {session_id}")
            return None
    
    def get_session_by_token(self, access_token: str) -> Optional[DBUserSession]:
        """根据访问令牌获取会话"""
        try:
            return self.session.query(DBUserSession).filter(
                and_(
                    DBUserSession.access_token == access_token,
                    DBUserSession.is_active == True
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting session by token: {str(e)}")
            return None
    
    def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[DBUserSession]:
        """获取用户的所有会话"""
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            
            query = self.session.query(DBUserSession).filter(
                DBUserSession.user_id == user_uuid
            )
            
            if active_only:
                query = query.filter(DBUserSession.is_active == True)
            
            return query.order_by(DBUserSession.created_at.desc()).offset(skip).limit(limit).all()
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return []
    
    def update_session(
        self,
        session_id: str,
        **updates
    ) -> Optional[DBUserSession]:
        """更新会话"""
        try:
            uuid_id = UUID(session_id) if isinstance(session_id, str) else session_id
            db_session = self.session.query(DBUserSession).filter(
                DBUserSession.id == uuid_id
            ).first()
            
            if db_session:
                for key, value in updates.items():
                    if hasattr(db_session, key):
                        setattr(db_session, key, value)
                self.session.flush()
            return db_session
        except (ValueError, TypeError):
            logger.warning(f"Invalid session_id format: {session_id}")
            return None
    
    def deactivate_session(self, session_id: str) -> bool:
        """停用会话"""
        try:
            uuid_id = UUID(session_id) if isinstance(session_id, str) else session_id
            db_session = self.session.query(DBUserSession).filter(
                DBUserSession.id == uuid_id
            ).first()
            
            if db_session:
                db_session.is_active = False
                self.session.flush()
                return True
            return False
        except (ValueError, TypeError):
            logger.warning(f"Invalid session_id format: {session_id}")
            return False
    
    def delete_expired_sessions(self, before: datetime) -> int:
        """删除过期会话"""
        try:
            count = self.session.query(DBUserSession).filter(
                and_(
                    DBUserSession.expires_at < before,
                    DBUserSession.is_active == True
                )
            ).update({"is_active": False}, synchronize_session=False)
            self.session.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error deleting expired sessions: {str(e)}")
            self.session.rollback()
            return 0









