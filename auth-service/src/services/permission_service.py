"""
权限服务
管理权限数据存储和业务逻辑（数据库）
"""
from typing import Dict, Any, Optional, List, Tuple
import logging
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.src.models.user_models import Permission as DBPermission
from database.src.repositories.user_repository import PermissionRepository
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


def _normalize_enum(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "value"):
        return value.value
    return str(value)


class PermissionService:
    """权限服务（数据库）"""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def _get_session(self) -> Tuple[Session, bool]:
        if self._db:
            return self._db, False
        db = SessionLocal()
        return db, True

    def _close_session(self, db: Session, should_close: bool) -> None:
        if should_close:
            db.close()

    async def create_permission(self, permission_data: Dict[str, Any]) -> DBPermission:
        """创建权限"""
        db, should_close = self._get_session()
        try:
            repo = PermissionRepository(db)
            code = permission_data["code"]
            existing = repo.get_by_code(code)
            if existing:
                raise ValueError(f"Permission with code '{code}' already exists")

            resource_type = _normalize_enum(permission_data.get("resource_type"))
            permission_type = _normalize_enum(permission_data.get("permission_type"))

            permission = repo.create(
                code=code,
                name=permission_data["name"],
                description=permission_data.get("description", ""),
                resource=resource_type,
                action=permission_type,
            )

            db.commit()
            db.refresh(permission)
            return permission
        except Exception as e:
            logger.error(f"Error creating permission: {str(e)}", exc_info=True)
            db.rollback()
            raise
        finally:
            self._close_session(db, should_close)

    async def get_permission(self, permission_id: str) -> Optional[DBPermission]:
        """获取权限"""
        db, should_close = self._get_session()
        try:
            repo = PermissionRepository(db)
            try:
                permission_uuid = UUID(str(permission_id))
            except (ValueError, TypeError):
                return None
            return repo.get_by_id(permission_uuid)
        finally:
            self._close_session(db, should_close)

    async def get_permission_by_code(self, code: str) -> Optional[DBPermission]:
        """根据代码获取权限"""
        db, should_close = self._get_session()
        try:
            repo = PermissionRepository(db)
            return repo.get_by_code(code)
        finally:
            self._close_session(db, should_close)

    async def update_permission(self, permission_id: str, updates: Dict[str, Any]) -> Optional[DBPermission]:
        """更新权限"""
        db, should_close = self._get_session()
        try:
            repo = PermissionRepository(db)
            try:
                permission_uuid = UUID(str(permission_id))
            except (ValueError, TypeError):
                return None

            permission = repo.get_by_id(permission_uuid)
            if not permission:
                return None

            if "name" in updates and updates["name"] is not None:
                permission.name = updates["name"]
            if "description" in updates and updates["description"] is not None:
                permission.description = updates["description"]

            db.flush()
            db.commit()
            db.refresh(permission)
            return permission
        except Exception as e:
            logger.error(f"Error updating permission: {str(e)}", exc_info=True)
            db.rollback()
            raise
        finally:
            self._close_session(db, should_close)

    async def delete_permission(self, permission_id: str) -> bool:
        """删除权限"""
        db, should_close = self._get_session()
        try:
            repo = PermissionRepository(db)
            try:
                permission_uuid = UUID(str(permission_id))
            except (ValueError, TypeError):
                return False
            success = repo.delete(permission_uuid)
            if success:
                db.commit()
            return success
        except Exception as e:
            logger.error(f"Error deleting permission: {str(e)}", exc_info=True)
            db.rollback()
            return False
        finally:
            self._close_session(db, should_close)

    async def list_permissions(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        resource_type: Optional[str] = None,
        permission_type: Optional[str] = None
    ) -> Tuple[List[DBPermission], int]:
        """列出权限"""
        db, should_close = self._get_session()
        try:
            query = db.query(DBPermission)

            if resource_type:
                resource_value = _normalize_enum(resource_type)
                query = query.filter(
                    or_(
                        DBPermission.resource == resource_value,
                        DBPermission.code.ilike(f"{resource_value}:%")
                    )
                )

            if permission_type:
                action_value = _normalize_enum(permission_type)
                query = query.filter(
                    or_(
                        DBPermission.action == action_value,
                        DBPermission.code.ilike(f"%:{action_value}")
                    )
                )

            if search:
                search_lower = f"%{search}%"
                query = query.filter(
                    or_(
                        DBPermission.name.ilike(search_lower),
                        DBPermission.code.ilike(search_lower),
                        DBPermission.description.ilike(search_lower)
                    )
                )

            total = query.count()
            permissions = query.order_by(DBPermission.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return permissions, total
        except Exception as e:
            logger.error(f"Error listing permissions: {str(e)}", exc_info=True)
            return [], 0
        finally:
            self._close_session(db, should_close)


# 全局权限服务实例
permission_service = PermissionService()
