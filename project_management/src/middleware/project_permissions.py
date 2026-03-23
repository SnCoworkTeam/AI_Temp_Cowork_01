"""
项目级别权限检查中间件
"""

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.src.core.session import get_db
from database.src.models.project_models import Project, ProjectMember, ProjectMemberRole

from ..routes.auth import require_auth

logger = logging.getLogger(__name__)


class ProjectPermission:
    """项目权限操作"""

    CREATE = "create"  # 创建
    READ = "read"  # 查看
    UPDATE = "update"  # 更新
    EDIT = "edit"  # 编辑（等同于update，为了兼容性保留）
    WRITE = "write"  # 写入（等同于update）
    DELETE = "delete"  # 删除
    MANAGE = "manage"  # 管理（所有操作）


def check_project_permission(
    project_id: UUID, user_id: UUID, permission: str, db: Session, is_admin: bool = False
) -> bool:
    """
    检查用户对项目的权限

    Args:
        project_id: 项目ID
        user_id: 用户ID
        permission: 权限操作（create, read, update, delete, manage）
        db: 数据库会话
        is_admin: 是否是管理员

    Returns:
        True if has permission, False otherwise
    """
    # 管理员有所有权限
    if is_admin:
        return True

    # 权限映射：EDIT和WRITE等同于UPDATE
    permission_mapped = permission
    if permission == ProjectPermission.EDIT or permission == ProjectPermission.WRITE:
        permission_mapped = ProjectPermission.UPDATE

    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False

    # 检查是否是项目创建者/管理员
    if project.manager_id == user_id:
        return True

    # 检查项目成员权限
    member = (
        db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id).first()
    )

    if not member:
        return False

    # 根据角色判断权限（role现在是字符串）
    if member.role == "manager" or member.role == ProjectMemberRole.MANAGER.value:
        return True  # 项目经理有所有权限

    if member.role == "member" or member.role == ProjectMemberRole.MEMBER.value:
        # 成员可以创建、读取、更新（包括edit和write），但不能删除和管理
        return permission_mapped in [ProjectPermission.CREATE, ProjectPermission.READ, ProjectPermission.UPDATE]

    if member.role == "viewer" or member.role == ProjectMemberRole.VIEWER.value:
        # 查看者只能读取
        return permission_mapped == ProjectPermission.READ

    return False


def require_project_permission(permission: str):
    """
    要求项目权限的依赖注入函数工厂

    Args:
        permission: 需要的权限（create, read, update, delete, manage）

    Returns:
        依赖注入函数
    """

    async def permission_checker(
        project_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
    ) -> dict:
        """
        权限检查函数

        Args:
            project_id: 从路径参数获取的项目ID
            db: 数据库会话
            current_user: 当前用户

        Returns:
            用户信息

        Raises:
            HTTPException: 如果没有权限
        """
        try:
            project_uuid = UUID(project_id)
            user_uuid = UUID(current_user.get("user_id"))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的项目ID或用户ID")

        # 检查是否是管理员
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        # 检查权限
        has_permission = check_project_permission(project_uuid, user_uuid, permission, db, is_admin=is_admin)

        if not has_permission:
            logger.warning(
                f"User {current_user.get('user_id')} does not have {permission} permission for project {project_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"没有权限执行此操作。需要项目{permission}权限"
            )

        return current_user

    return permission_checker


def require_project_manager(project_id: str):
    """
    要求项目经理权限的依赖注入函数工厂

    Args:
        project_id: 项目ID

    Returns:
        依赖注入函数
    """
    return require_project_permission(ProjectPermission.MANAGE)


def get_user_projects(
    user_id: UUID, db: Session, role: ProjectMemberRole | None = None, is_admin: bool = False
) -> list | None:
    """
    获取用户有权限的项目列表

    Args:
        user_id: 用户ID
        db: 数据库会话
        role: 可选的角色过滤
        is_admin: 是否是管理员（管理员可以看到所有项目）

    Returns:
        项目ID列表，如果是管理员则返回None（表示所有项目）
    """
    # 如果是管理员，返回None表示所有项目
    if is_admin:
        return None

    query = db.query(ProjectMember.project_id).filter(ProjectMember.user_id == user_id)

    if role:
        role_value = role.value if hasattr(role, "value") else str(role)
        query = query.filter(ProjectMember.role == role_value)

    # 也包含用户作为manager的项目
    project_ids = db.query(Project.id).filter(Project.manager_id == user_id).all()
    member_project_ids = query.all()

    all_project_ids = set()
    for pid in project_ids:
        all_project_ids.add(pid[0])
    for pid in member_project_ids:
        all_project_ids.add(pid[0])

    return list(all_project_ids)
