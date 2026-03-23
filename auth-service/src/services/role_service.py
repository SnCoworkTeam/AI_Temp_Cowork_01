"""
角色服务
管理角色数据存储和业务逻辑（数据库）
"""
from typing import Dict, Any, Optional, List, Tuple
import logging
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from database.src.models.user_models import Role as DBRole
from database.src.repositories.user_repository import RoleRepository
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class RoleService:
    """角色服务（数据库）"""

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

    async def create_role(self, role_data: Dict[str, Any]) -> DBRole:
        """创建角色"""
        db, should_close = self._get_session()
        try:
            repo = RoleRepository(db)
            existing = repo.get_by_code(role_data["code"])
            if existing:
                raise ValueError(f"Role code '{role_data['code']}' already exists")

            role = repo.create(
                code=role_data["code"],
                name=role_data["name"],
                description=role_data.get("description", ""),
                is_system=role_data.get("is_system", False),
            )

            permission_ids = role_data.get("permissions") or []
            for permission_id in permission_ids:
                try:
                    repo.assign_permission(role.id, UUID(str(permission_id)))
                except Exception:
                    logger.warning(
                        f"Failed to assign permission {permission_id} to role {role.id}"
                    )

            db.commit()
            db.refresh(role)
            _ = role.permissions
            return role
        except Exception as e:
            logger.error(f"Error creating role: {str(e)}", exc_info=True)
            db.rollback()
            raise
        finally:
            self._close_session(db, should_close)

    async def get_role(self, role_id: str) -> Optional[DBRole]:
        """获取角色"""
        db, should_close = self._get_session()
        try:
            try:
                role_uuid = UUID(str(role_id))
            except (ValueError, TypeError):
                return None
            return db.query(DBRole).options(joinedload(DBRole.permissions)).filter(DBRole.id == role_uuid).first()
        finally:
            self._close_session(db, should_close)

    async def get_role_by_code(self, code: str) -> Optional[DBRole]:
        """根据代码获取角色"""
        db, should_close = self._get_session()
        try:
            return db.query(DBRole).options(joinedload(DBRole.permissions)).filter(DBRole.code == code).first()
        finally:
            self._close_session(db, should_close)

    async def update_role(self, role_id: str, updates: Dict[str, Any]) -> Optional[DBRole]:
        """更新角色"""
        db, should_close = self._get_session()
        try:
            repo = RoleRepository(db)
            try:
                role_uuid = UUID(str(role_id))
            except (ValueError, TypeError):
                return None

            role = repo.get_by_id(role_uuid)
            if not role:
                return None

            if role.is_system:
                updates.pop("code", None)
                updates.pop("is_system", None)

            permission_ids = updates.pop("permissions", None)

            if "name" in updates and updates["name"] is not None:
                role.name = updates["name"]
            if "description" in updates and updates["description"] is not None:
                role.description = updates["description"]

            db.flush()

            if permission_ids is not None:
                current_ids = {str(p.id) for p in role.permissions}
                target_ids = set(permission_ids)
                to_add = target_ids - current_ids
                to_remove = current_ids - target_ids

                for permission_id in to_add:
                    try:
                        repo.assign_permission(role.id, UUID(str(permission_id)))
                    except Exception:
                        logger.warning(
                            f"Failed to assign permission {permission_id} to role {role.id}"
                        )

                for permission_id in to_remove:
                    try:
                        repo.remove_permission(role.id, UUID(str(permission_id)))
                    except Exception:
                        logger.warning(
                            f"Failed to remove permission {permission_id} from role {role.id}"
                        )

            db.commit()
            db.refresh(role)
            _ = role.permissions
            return role
        except Exception as e:
            logger.error(f"Error updating role: {str(e)}", exc_info=True)
            db.rollback()
            raise
        finally:
            self._close_session(db, should_close)

    async def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        db, should_close = self._get_session()
        try:
            repo = RoleRepository(db)
            try:
                role_uuid = UUID(str(role_id))
            except (ValueError, TypeError):
                return False

            role = repo.get_by_id(role_uuid)
            if not role or role.is_system:
                return False

            success = repo.delete(role_uuid)
            if success:
                db.commit()
            return success
        except Exception as e:
            logger.error(f"Error deleting role: {str(e)}", exc_info=True)
            db.rollback()
            return False
        finally:
            self._close_session(db, should_close)

    async def list_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[DBRole], int]:
        """列出角色"""
        db, should_close = self._get_session()
        try:
            query = db.query(DBRole).options(joinedload(DBRole.permissions))
            if search:
                search_lower = f"%{search}%"
                query = query.filter(
                    or_(
                        DBRole.name.ilike(search_lower),
                        DBRole.code.ilike(search_lower),
                        DBRole.description.ilike(search_lower)
                    )
                )

            total = query.count()
            roles = query.order_by(DBRole.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return roles, total
        except Exception as e:
            logger.error(f"Error listing roles: {str(e)}", exc_info=True)
            return [], 0
        finally:
            self._close_session(db, should_close)

    async def add_permission_to_role(self, role_id: str, permission_id: str) -> bool:
        """为角色添加权限"""
        db, should_close = self._get_session()
        try:
            repo = RoleRepository(db)
            try:
                role_uuid = UUID(str(role_id))
                permission_uuid = UUID(str(permission_id))
            except (ValueError, TypeError):
                return False

            success = repo.assign_permission(role_uuid, permission_uuid)
            if success:
                db.commit()
            return success
        except Exception as e:
            logger.error(f"Error adding permission to role: {str(e)}", exc_info=True)
            db.rollback()
            return False
        finally:
            self._close_session(db, should_close)

    async def remove_permission_from_role(self, role_id: str, permission_id: str) -> bool:
        """移除角色权限"""
        db, should_close = self._get_session()
        try:
            repo = RoleRepository(db)
            try:
                role_uuid = UUID(str(role_id))
                permission_uuid = UUID(str(permission_id))
            except (ValueError, TypeError):
                return False

            success = repo.remove_permission(role_uuid, permission_uuid)
            if success:
                db.commit()
            return success
        except Exception as e:
            logger.error(f"Error removing permission from role: {str(e)}", exc_info=True)
            db.rollback()
            return False
        finally:
            self._close_session(db, should_close)


# 全局角色服务实例
role_service = RoleService()
