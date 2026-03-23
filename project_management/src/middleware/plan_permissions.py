"""
计划级别权限检查中间件
扩展项目权限控制，支持计划级别的细粒度权限
"""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.src.core.session import get_db
from database.src.models.project_models import Project, ProjectPlan

from ..routes.auth import require_auth
from .project_permissions import ProjectPermission, check_project_permission

logger = logging.getLogger(__name__)


class PlanPermission:
    """计划权限操作"""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SET_BASELINE = "set_baseline"
    CLONE = "clone"
    MANAGE_TASKS = "manage_tasks"
    CALCULATE_CP = "calculate_critical_path"


# 权限矩阵
PERMISSION_MATRIX = {
    "project_plan": {
        "admin": [p for p in dir(PlanPermission) if not p.startswith("_")],
        "project_manager": [
            PlanPermission.READ,
            PlanPermission.CREATE,
            PlanPermission.UPDATE,
            PlanPermission.SET_BASELINE,
            PlanPermission.CLONE,
            PlanPermission.MANAGE_TASKS,
            PlanPermission.CALCULATE_CP,
        ],
        "team_lead": [
            PlanPermission.READ,
            PlanPermission.UPDATE,
            PlanPermission.MANAGE_TASKS,
        ],
        "project_member": [
            PlanPermission.READ,
        ],
        "viewer": [PlanPermission.READ],
    }
}


def check_plan_permission(plan_id: UUID, user_id: UUID, permission: str, db: Session, is_admin: bool = False) -> bool:
    """
    检查用户对计划的权限

    Args:
        plan_id: 计划ID
        user_id: 用户ID
        permission: 权限操作
        db: 数据库会话
        is_admin: 是否是管理员

    Returns:
        True if has permission, False otherwise
    """
    # 管理员有所有权限
    if is_admin:
        return True

    # 检查计划是否存在
    plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_id).first()
    if not plan:
        return False

    # 检查项目权限（计划权限基于项目权限）
    has_project_permission = check_project_permission(
        plan.project_id, user_id, ProjectPermission.READ, db, is_admin=is_admin  # 至少需要项目READ权限
    )

    if not has_project_permission:
        return False

    # 获取用户在项目中的角色
    from database.src.models.project_models import ProjectMember

    project = db.query(Project).filter(Project.id == plan.project_id).first()
    if not project:
        return False

    # 检查是否是项目经理
    if project.manager_id == user_id:
        # 项目经理有所有计划权限
        return True

    # 检查项目成员角色
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == plan.project_id, ProjectMember.user_id == user_id)
        .first()
    )

    if not member:
        # 不是项目成员，只有READ权限（如果项目是公开的）
        return permission == PlanPermission.READ

    # 根据角色判断权限
    role = member.role.lower()
    allowed_permissions = PERMISSION_MATRIX.get("project_plan", {}).get(role, [])

    return permission in allowed_permissions


def require_plan_permission(permission: str):
    """
    要求计划权限的依赖注入函数工厂

    Args:
        permission: 需要的权限

    Returns:
        依赖注入函数
    """

    async def permission_checker(
        plan_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
    ) -> dict:
        """
        权限检查函数

        Args:
            plan_id: 从路径参数获取的计划ID
            db: 数据库会话
            current_user: 当前用户

        Returns:
            用户信息

        Raises:
            HTTPException: 如果没有权限
        """
        try:
            plan_uuid = UUID(plan_id)
            user_uuid = UUID(current_user.get("user_id"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的计划ID或用户ID")

        # 检查是否是管理员
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        # 检查权限
        has_permission = check_plan_permission(plan_uuid, user_uuid, permission, db, is_admin=is_admin)

        if not has_permission:
            logger.warning(
                f"User {current_user.get('user_id')} does not have {permission} permission for plan {plan_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"没有权限执行此操作。需要计划{permission}权限"
            )

        return current_user

    return permission_checker
