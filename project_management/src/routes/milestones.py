"""
里程碑管理路由
"""

import contextlib
import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Milestone, MilestoneStatus, Project
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission, get_user_projects
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class MilestoneResponse(BaseModel):
    """里程碑响应模型"""

    id: str
    project_id: str
    phase_id: str | None = None
    category_id: str  # 基础数据分类ID
    category_name: str | None = None  # 基础数据分类名称
    category_code: str | None = None  # 基础数据分类编码
    name: str  # 里程碑名称（从基础数据同步）
    description: str | None = None
    target_date: str | None = None
    actual_date: str | None = None
    status: str
    project_name: str | None = None
    completion_date: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class MilestoneListResponse(BaseModel):
    """里程碑列表响应"""

    total: int
    items: list[MilestoneResponse]


@router.get("", response_model=MilestoneListResponse)
async def list_milestones(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取里程碑列表（只返回用户有权限的项目里程碑）"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的用户ID")

        # 检查是否是管理员
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        # 获取用户有权限的项目列表（管理员返回None，表示所有项目）
        user_project_ids = get_user_projects(user_uuid, db, is_admin=is_admin)

        query = db.query(Milestone)

        # 只查询用户有权限的项目里程碑
        # 如果 user_project_ids 是 None，表示管理员，不进行过滤
        if user_project_ids is not None:
            if user_project_ids:
                query = query.filter(Milestone.project_id.in_(user_project_ids))
            else:
                # 用户没有任何项目权限，返回空列表
                return MilestoneListResponse(total=0, items=[])

        if project_id:
            try:
                project_uuid = UUID(project_id)
                # 如果不是管理员，检查用户是否有该项目的权限
                if not is_admin and user_project_ids is not None:
                    if project_uuid not in user_project_ids:
                        raise HTTPException(status_code=403, detail="没有权限访问该项目")
                query = query.filter(Milestone.project_id == project_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        if status:
            try:
                milestone_status = MilestoneStatus(status.lower())
                query = query.filter(Milestone.status == milestone_status)
            except ValueError:
                pass

        total = query.count()
        milestones = query.order_by(Milestone.target_date.desc()).offset(skip).limit(limit).all()

        # 获取项目名称
        project_ids = {str(m.project_id) for m in milestones}
        projects = {}
        if project_ids:
            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        # 获取基础数据分类信息
        from database.src.models.basic_data_models import BasicDataCategory

        category_ids = {str(m.category_id) for m in milestones if m.category_id}
        categories = {}
        if category_ids:
            category_list = (
                db.query(BasicDataCategory).filter(BasicDataCategory.id.in_([UUID(cid) for cid in category_ids])).all()
            )
            categories = {str(c.id): c for c in category_list}

        items = []
        for milestone in milestones:
            # 如果里程碑有category_id，优先使用基础数据中的名称
            category = categories.get(str(milestone.category_id)) if milestone.category_id else None
            milestone_name = category.name if category else milestone.name

            items.append(
                MilestoneResponse(
                    id=str(milestone.id),
                    project_id=str(milestone.project_id),
                    phase_id=str(milestone.phase_id) if milestone.phase_id else None,
                    category_id=str(milestone.category_id) if milestone.category_id else "",
                    category_name=category.name if category else milestone.name,
                    category_code=category.code if category else None,
                    name=milestone_name,
                    description=milestone.description,
                    target_date=milestone.target_date.isoformat() if milestone.target_date else None,
                    actual_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
                    status=milestone.status.value if hasattr(milestone.status, "value") else str(milestone.status),
                    project_name=projects.get(str(milestone.project_id)),
                    completion_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
                    created_at=milestone.created_at.isoformat() if milestone.created_at else "",
                )
            )

        return MilestoneListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"获取里程碑列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取里程碑列表失败: {e!s}")


@router.get("/{milestone_id}", response_model=MilestoneResponse)
async def get_milestone(milestone_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取里程碑详情（需要项目READ权限）"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            milestone_uuid = UUID(milestone_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的里程碑ID或用户ID")

        milestone = db.query(Milestone).filter(Milestone.id == milestone_uuid).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")

        # 检查用户是否有该项目的READ权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            milestone.project_id, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限查看该里程碑")

        from database.src.models.project_models import Project

        project = db.query(Project).filter(Project.id == milestone.project_id).first()

        # 获取基础数据分类信息
        from database.src.models.basic_data_models import BasicDataCategory

        category = None
        if milestone.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == milestone.category_id).first()

        return MilestoneResponse(
            id=str(milestone.id),
            project_id=str(milestone.project_id),
            phase_id=str(milestone.phase_id) if milestone.phase_id else None,
            category_id=str(milestone.category_id) if milestone.category_id else "",
            category_name=category.name if category else milestone.name,
            category_code=category.code if category else None,
            name=category.name if category else milestone.name,
            description=milestone.description,
            target_date=milestone.target_date.isoformat() if milestone.target_date else None,
            actual_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
            status=milestone.status.value if hasattr(milestone.status, "value") else str(milestone.status),
            project_name=project.name if project else None,
            completion_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
            created_at=milestone.created_at.isoformat() if milestone.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取里程碑详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取里程碑详情失败: {e!s}")


class MilestoneCreate(BaseModel):
    """里程碑创建模型"""

    project_id: str
    phase_id: str | None = None
    category_id: str  # 必须从基础数据中选择
    description: str | None = None
    status: str | None = "planned"
    target_date: str | None = None


class MilestoneUpdate(BaseModel):
    """里程碑更新模型"""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    target_date: str | None = None
    actual_date: str | None = None


@router.post("", response_model=MilestoneResponse)
async def create_milestone(
    milestone_data: MilestoneCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """创建里程碑（需要项目CREATE权限）"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 验证项目是否存在
        try:
            project_id = UUID(milestone_data.project_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的项目ID或用户ID")

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查用户是否有该项目的CREATE权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            project_id, user_uuid, ProjectPermission.CREATE, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限在该项目中创建里程碑")

        # 解析状态
        status = MilestoneStatus.PLANNED
        if milestone_data.status:
            try:
                status = MilestoneStatus(milestone_data.status.lower())
            except ValueError:
                status = MilestoneStatus.PLANNED

        # 解析日期
        target_date = None
        if milestone_data.target_date:
            try:
                target_date = datetime.fromisoformat(milestone_data.target_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                target_date = datetime.strptime(milestone_data.target_date, "%Y-%m-%d").date()

        # 解析phase_id，并验证它属于同一项目
        phase_id = None
        if milestone_data.phase_id:
            try:
                phase_id = UUID(milestone_data.phase_id)
                # 验证阶段属于同一项目
                from database.src.models.project_models import ProjectPhase

                phase = (
                    db.query(ProjectPhase)
                    .filter(ProjectPhase.id == phase_id, ProjectPhase.project_id == project_id)
                    .first()
                )
                if not phase:
                    raise HTTPException(status_code=400, detail="阶段不属于该项目")
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的阶段ID")

        # 验证并获取基础数据分类
        from database.src.models.basic_data_models import BasicDataCategory

        try:
            category_id = UUID(milestone_data.category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的分类ID")

        category = (
            db.query(BasicDataCategory)
            .filter(
                BasicDataCategory.id == category_id,
                BasicDataCategory.category_type == "milestone",
                BasicDataCategory.is_active,
            )
            .first()
        )

        if not category:
            raise HTTPException(status_code=404, detail="里程碑分类不存在或已禁用")

        # 创建里程碑（名称从基础数据同步）
        milestone = Milestone(
            project_id=project_id,
            phase_id=phase_id,
            category_id=category_id,
            name=category.name,  # 从基础数据同步名称
            description=milestone_data.description,
            status=status,
            target_date=target_date,
        )

        db.add(milestone)
        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="milestone",
                resource_id=str(milestone.id),
                details={"project_id": str(project_id), "category_id": str(category_id), "name": category.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        # 获取基础数据分类信息
        from database.src.models.basic_data_models import BasicDataCategory

        category = None
        if milestone.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == milestone.category_id).first()

        return MilestoneResponse(
            id=str(milestone.id),
            project_id=str(milestone.project_id),
            phase_id=str(milestone.phase_id) if milestone.phase_id else None,
            category_id=str(milestone.category_id) if milestone.category_id else "",
            category_name=category.name if category else milestone.name,
            category_code=category.code if category else None,
            name=category.name if category else milestone.name,
            description=milestone.description,
            target_date=milestone.target_date.isoformat() if milestone.target_date else None,
            actual_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
            status=milestone.status.value if hasattr(milestone.status, "value") else str(milestone.status),
            project_name=project.name,
            completion_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
            created_at=milestone.created_at.isoformat() if milestone.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建里程碑失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建里程碑失败: {e!s}")


@router.put("/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: str,
    milestone_data: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新里程碑"""
    try:
        from datetime import datetime

        from database.src.models.project_models import Project
        from database.src.models.system_models import AuditLog

        try:
            milestone_uuid = UUID(milestone_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的里程碑ID")

        milestone = db.query(Milestone).filter(Milestone.id == milestone_uuid).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")

        # 更新字段
        if milestone_data.category_id is not None:
            # 验证并更新基础数据分类
            from database.src.models.basic_data_models import BasicDataCategory

            try:
                category_id = UUID(milestone_data.category_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的分类ID")

            category = (
                db.query(BasicDataCategory)
                .filter(
                    BasicDataCategory.id == category_id,
                    BasicDataCategory.category_type == "milestone",
                    BasicDataCategory.is_active,
                )
                .first()
            )

            if not category:
                raise HTTPException(status_code=404, detail="里程碑分类不存在或已禁用")

            milestone.category_id = category_id
            milestone.name = category.name  # 同步名称

        if milestone_data.description is not None:
            milestone.description = milestone_data.description
        if milestone_data.status is not None:
            with contextlib.suppress(ValueError):
                milestone.status = MilestoneStatus(milestone_data.status.lower())
        if milestone_data.target_date is not None:
            try:
                milestone.target_date = datetime.fromisoformat(milestone_data.target_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                milestone.target_date = datetime.strptime(milestone_data.target_date, "%Y-%m-%d").date()
        if milestone_data.actual_date is not None:
            try:
                milestone.actual_date = datetime.fromisoformat(milestone_data.actual_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                milestone.actual_date = datetime.strptime(milestone_data.actual_date, "%Y-%m-%d").date()

        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="milestone",
                resource_id=str(milestone.id),
                details={"name": milestone_data.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        project = db.query(Project).filter(Project.id == milestone.project_id).first()

        # 获取基础数据分类信息
        from database.src.models.basic_data_models import BasicDataCategory

        category = None
        if milestone.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == milestone.category_id).first()

        return MilestoneResponse(
            id=str(milestone.id),
            project_id=str(milestone.project_id),
            phase_id=str(milestone.phase_id) if milestone.phase_id else None,
            category_id=str(milestone.category_id) if milestone.category_id else "",
            category_name=category.name if category else milestone.name,
            category_code=category.code if category else None,
            name=category.name if category else milestone.name,
            description=milestone.description,
            target_date=milestone.target_date.isoformat() if milestone.target_date else None,
            actual_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
            status=milestone.status.value if hasattr(milestone.status, "value") else str(milestone.status),
            project_name=project.name if project else None,
            completion_date=milestone.actual_date.isoformat() if milestone.actual_date else None,
            created_at=milestone.created_at.isoformat() if milestone.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新里程碑失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新里程碑失败: {e!s}")


@router.delete("/{milestone_id}")
async def delete_milestone(
    milestone_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """删除里程碑"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            milestone_uuid = UUID(milestone_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的里程碑ID")

        milestone = db.query(Milestone).filter(Milestone.id == milestone_uuid).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="里程碑不存在")

        milestone_name = milestone.name

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="milestone",
                resource_id=str(milestone.id),
                details={"name": milestone_name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(milestone)
        db.commit()

        return {"message": "里程碑已删除", "id": milestone_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除里程碑失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除里程碑失败: {e!s}")
