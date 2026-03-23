"""
项目成员管理路由
"""

import logging
from datetime import date
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Project, ProjectMember, ProjectMemberRole
from database.src.models.system_models import AuditLog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, require_project_permission

router = APIRouter()
logger = logging.getLogger(__name__)


class ProjectMemberResponse(BaseModel):
    """项目成员响应模型"""

    id: str
    project_id: str
    user_id: str
    username: str | None = None
    full_name: str | None = None
    email: str | None = None
    role: str
    joined_at: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectMemberListResponse(BaseModel):
    """项目成员列表响应"""

    total: int
    items: list[ProjectMemberResponse]


class ProjectMemberCreate(BaseModel):
    """添加项目成员请求模型"""

    user_id: str
    role: str = "member"  # manager, member, viewer
    joined_at: str | None = None


class ProjectMemberUpdate(BaseModel):
    """更新项目成员请求模型"""

    role: str | None = None


@router.get("/projects/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_project_members(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.READ)),
):
    """获取项目成员列表（需要项目查看权限）"""
    try:
        project_uuid = UUID(project_id)

        # 查询项目成员
        members = db.query(ProjectMember).filter(ProjectMember.project_id == project_uuid).all()

        # 获取用户信息
        from database.src.models.user_models import User

        user_ids = [m.user_id for m in members]
        users = {}
        if user_ids:
            user_list = db.query(User).filter(User.id.in_(user_ids)).all()
            users = {str(u.id): u for u in user_list}

        items = []
        for member in members:
            user = users.get(str(member.user_id))
            items.append(
                ProjectMemberResponse(
                    id=str(member.id),
                    project_id=str(member.project_id),
                    user_id=str(member.user_id),
                    username=user.username if user else None,
                    full_name=user.full_name if user else None,
                    email=user.email if user else None,
                    role=member.role.value if hasattr(member.role, "value") else str(member.role),
                    joined_at=member.joined_at.isoformat() if member.joined_at else None,
                    created_at=member.created_at.isoformat() if member.created_at else "",
                    updated_at=member.updated_at.isoformat() if member.updated_at else "",
                )
            )

        return ProjectMemberListResponse(total=len(items), items=items)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    except Exception as e:
        logger.error(f"获取项目成员列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目成员列表失败: {e!s}")


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: str,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.MANAGE)),
):
    """添加项目成员（需要项目管理权限）"""
    try:
        project_uuid = UUID(project_id)
        user_uuid = UUID(member_data.user_id)

        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查用户是否存在
        from database.src.models.user_models import User

        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 检查是否已经是成员
        existing = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_uuid, ProjectMember.user_id == user_uuid)
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="用户已经是项目成员")

        # 解析角色
        try:
            role = ProjectMemberRole(member_data.role.lower())
        except ValueError:
            role = ProjectMemberRole.MEMBER

        # 解析加入日期
        joined_date = None
        if member_data.joined_at:
            try:
                from datetime import datetime

                joined_date = datetime.fromisoformat(member_data.joined_at.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                joined_date = datetime.strptime(member_data.joined_at, "%Y-%m-%d").date()
        else:
            joined_date = date.today()

        # 创建成员
        member = ProjectMember(project_id=project_uuid, user_id=user_uuid, role=role, joined_at=joined_date)

        db.add(member)
        db.flush()

        # 记录审计日志
        try:
            audit_log = AuditLog(
                user_id=UUID(current_user.get("user_id")) if current_user.get("user_id") != "anonymous" else None,
                action="create",
                resource_type="project_member",
                resource_id=str(member.id),
                details={"project_id": project_id, "user_id": member_data.user_id, "role": member_data.role},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        return ProjectMemberResponse(
            id=str(member.id),
            project_id=str(member.project_id),
            user_id=str(member.user_id),
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=member.role.value if hasattr(member.role, "value") else str(member.role),
            joined_at=member.joined_at.isoformat() if member.joined_at else None,
            created_at=member.created_at.isoformat() if member.created_at else "",
            updated_at=member.updated_at.isoformat() if member.updated_at else "",
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e!s}")
    except Exception as e:
        logger.error(f"添加项目成员失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加项目成员失败: {e!s}")


@router.put("/projects/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    project_id: str,
    member_id: str,
    member_data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.MANAGE)),
):
    """更新项目成员角色（需要项目管理权限）"""
    try:
        project_uuid = UUID(project_id)
        member_uuid = UUID(member_id)

        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.id == member_uuid, ProjectMember.project_id == project_uuid)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="项目成员不存在")

        # 更新角色
        if member_data.role:
            try:
                member.role = ProjectMemberRole(member_data.role.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的角色")

        db.flush()

        # 记录审计日志
        try:
            from datetime import datetime

            audit_log = AuditLog(
                user_id=UUID(current_user.get("user_id")) if current_user.get("user_id") != "anonymous" else None,
                action="update",
                resource_type="project_member",
                resource_id=str(member.id),
                details={"role": member_data.role},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        # 获取用户信息
        from database.src.models.user_models import User

        user = db.query(User).filter(User.id == member.user_id).first()

        return ProjectMemberResponse(
            id=str(member.id),
            project_id=str(member.project_id),
            user_id=str(member.user_id),
            username=user.username if user else None,
            full_name=user.full_name if user else None,
            email=user.email if user else None,
            role=member.role.value if hasattr(member.role, "value") else str(member.role),
            joined_at=member.joined_at.isoformat() if member.joined_at else None,
            created_at=member.created_at.isoformat() if member.created_at else "",
            updated_at=member.updated_at.isoformat() if member.updated_at else "",
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID或成员ID")
    except Exception as e:
        logger.error(f"更新项目成员失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新项目成员失败: {e!s}")


@router.delete("/projects/{project_id}/members/{member_id}")
async def remove_project_member(
    project_id: str,
    member_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.MANAGE)),
):
    """移除项目成员（需要项目管理权限）"""
    try:
        project_uuid = UUID(project_id)
        member_uuid = UUID(member_id)

        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.id == member_uuid, ProjectMember.project_id == project_uuid)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="项目成员不存在")

        # 记录审计日志
        try:
            from datetime import datetime

            audit_log = AuditLog(
                user_id=UUID(current_user.get("user_id")) if current_user.get("user_id") != "anonymous" else None,
                action="delete",
                resource_type="project_member",
                resource_id=str(member.id),
                details={"project_id": project_id},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(member)
        db.commit()

        return {"message": "项目成员已移除", "id": member_id}

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID或成员ID")
    except Exception as e:
        logger.error(f"移除项目成员失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除项目成员失败: {e!s}")
