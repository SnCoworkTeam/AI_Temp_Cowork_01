"""
资源级别权限检查辅助函数
用于检查用户对项目相关资源的权限
"""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.src.core.session import get_db

from ..routes.auth import require_auth
from .project_permissions import check_project_permission

logger = logging.getLogger(__name__)


def check_resource_project_permission(
    resource_project_id: UUID, user_id: UUID, permission: str, db: Session, is_admin: bool = False
) -> bool:
    """
    检查用户对资源所属项目的权限

    Args:
        resource_project_id: 资源所属的项目ID
        user_id: 用户ID
        permission: 权限操作（create, read, update, delete, manage）
        db: 数据库会话
        is_admin: 是否是管理员

    Returns:
        True if has permission, False otherwise
    """
    return check_project_permission(resource_project_id, user_id, permission, db, is_admin=is_admin)


def require_resource_project_permission(permission: str):
    """
    要求资源所属项目权限的依赖注入函数工厂

    Args:
        permission: 需要的权限（create, read, update, delete, manage）

    Returns:
        依赖注入函数
    """

    async def permission_checker(
        resource_id: str,
        resource_type: str,  # 'task', 'milestone', 'phase', 'risk', 'weekly_report', 'monthly_report'
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_auth),
    ) -> dict:
        """
        权限检查函数

        Args:
            resource_id: 资源ID（从路径参数获取）
            resource_type: 资源类型
            db: 数据库会话
            current_user: 当前用户

        Returns:
            用户信息

        Raises:
            HTTPException: 如果没有权限
        """
        try:
            resource_uuid = UUID(resource_id)
            user_uuid = UUID(current_user.get("user_id"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的资源ID或用户ID")

        # 根据资源类型获取项目ID
        project_id = None
        if resource_type == "task":
            from database.src.models.project_models import Task

            resource = db.query(Task).filter(Task.id == resource_uuid).first()
            if resource:
                project_id = resource.project_id
        elif resource_type == "milestone":
            from database.src.models.project_models import Milestone

            resource = db.query(Milestone).filter(Milestone.id == resource_uuid).first()
            if resource:
                project_id = resource.project_id
        elif resource_type == "phase":
            from database.src.models.project_models import ProjectPhase

            resource = db.query(ProjectPhase).filter(ProjectPhase.id == resource_uuid).first()
            if resource:
                project_id = resource.project_id
        elif resource_type == "risk":
            from database.src.models.project_models import Risk

            resource = db.query(Risk).filter(Risk.id == resource_uuid).first()
            if resource:
                project_id = resource.project_id
        elif resource_type == "weekly_report":
            from database.src.models.project_models import WeeklyReport

            resource = db.query(WeeklyReport).filter(WeeklyReport.id == resource_uuid).first()
            if resource:
                project_id = resource.project_id
        elif resource_type == "monthly_report":
            from database.src.models.project_models import MonthlyReport

            resource = db.query(MonthlyReport).filter(MonthlyReport.id == resource_uuid).first()
            if resource:
                project_id = resource.project_id

        if not project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_type}不存在")

        # 检查是否是管理员
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        # 检查权限
        has_permission = check_project_permission(project_id, user_uuid, permission, db, is_admin=is_admin)

        if not has_permission:
            logger.warning(
                f"User {current_user.get('user_id')} does not have {permission} permission for {resource_type} {resource_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"没有权限执行此操作。需要项目{permission}权限"
            )

        return current_user

    return permission_checker
