"""
项目阶段管理路由
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Project, ProjectPhase
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission, get_user_projects
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class PhaseResponse(BaseModel):
    """项目阶段响应模型"""

    id: str
    project_id: str
    category_id: str  # 基础数据分类ID
    name: str
    description: str | None = None
    sequence: int
    start_date: str | None = None
    end_date: str | None = None
    progress_percent: float = 0.0
    project_name: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class PhaseListResponse(BaseModel):
    """项目阶段列表响应"""

    total: int
    items: list[PhaseResponse]


@router.get("", response_model=PhaseListResponse)
async def list_phases(
    project_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取项目阶段列表（只返回用户有权限的项目阶段）"""
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

        # 获取用户有权限的项目列表
        user_project_ids = get_user_projects(user_uuid, db, is_admin=is_admin)

        query = db.query(ProjectPhase)

        # 只查询用户有权限的项目阶段
        if user_project_ids is None:
            # 管理员，可以查看所有项目阶段
            pass
        elif user_project_ids:
            query = query.filter(ProjectPhase.project_id.in_(user_project_ids))
        else:
            # 用户没有任何项目权限，返回空列表
            return PhaseListResponse(total=0, items=[])

        if project_id:
            try:
                project_uuid = UUID(project_id)
                # 检查用户是否有该项目的权限（管理员除外）
                if user_project_ids is not None and project_uuid not in user_project_ids:
                    raise HTTPException(status_code=403, detail="没有权限访问该项目")
                query = query.filter(ProjectPhase.project_id == project_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        total = query.count()
        phases = query.order_by(ProjectPhase.sequence).offset(skip).limit(limit).all()

        # 获取项目名称
        project_ids = {str(p.project_id) for p in phases}
        projects = {}
        if project_ids:
            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        # 获取基础数据分类信息
        from database.src.models.basic_data_models import BasicDataCategory

        category_ids = {str(p.category_id) for p in phases if p.category_id}
        categories = {}
        if category_ids:
            category_list = (
                db.query(BasicDataCategory).filter(BasicDataCategory.id.in_([UUID(cid) for cid in category_ids])).all()
            )
            categories = {str(c.id): c for c in category_list}

        items = []
        for phase in phases:
            # 如果阶段有category_id，优先使用基础数据中的名称
            category = categories.get(str(phase.category_id)) if phase.category_id else None
            phase_name = category.name if category and hasattr(category, 'name') else (phase.name if phase.name else "")

            items.append(
                PhaseResponse(
                    id=str(phase.id),
                    project_id=str(phase.project_id),
                    category_id=str(phase.category_id) if phase.category_id else "",
                    name=phase_name,
                    description=phase.description,
                    sequence=phase.sequence,
                    start_date=phase.start_date.isoformat() if phase.start_date else None,
                    end_date=phase.end_date.isoformat() if phase.end_date else None,
                    progress_percent=phase.progress_percent or 0.0,
                    project_name=projects.get(str(phase.project_id)),
                    created_at=phase.created_at.isoformat() if phase.created_at else "",
                )
            )

        return PhaseListResponse(total=total, items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目阶段列表失败: {e!s}", exc_info=True)
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取项目阶段列表失败: {e!s}")


@router.get("/{phase_id}", response_model=PhaseResponse)
async def get_phase(phase_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取阶段详情（需要项目READ权限）"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            phase_uuid = UUID(phase_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的阶段ID或用户ID")

        phase = db.query(ProjectPhase).filter(ProjectPhase.id == phase_uuid).first()
        if not phase:
            raise HTTPException(status_code=404, detail="阶段不存在")

        # 检查用户是否有该项目的READ权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            phase.project_id, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限访问该阶段")

        project = db.query(Project).filter(Project.id == phase.project_id).first()

        # 获取基础数据分类信息
        from database.src.models.basic_data_models import BasicDataCategory

        category = None
        if phase.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == phase.category_id).first()

        return PhaseResponse(
            id=str(phase.id),
            project_id=str(phase.project_id),
            category_id=str(phase.category_id) if phase.category_id else "",
            name=category.name if category else phase.name,
            description=phase.description,
            sequence=phase.sequence,
            start_date=phase.start_date.isoformat() if phase.start_date else None,
            end_date=phase.end_date.isoformat() if phase.end_date else None,
            progress_percent=phase.progress_percent or 0.0,
            project_name=project.name if project else None,
            created_at=phase.created_at.isoformat() if phase.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取阶段详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取阶段详情失败: {e!s}")


class PhaseCreate(BaseModel):
    """阶段创建模型"""

    project_id: str
    category_id: str  # 必须从基础数据中选择
    description: str | None = None
    sequence: int | None = None  # 如果不提供，自动设置为最大值+1
    start_date: str | None = None
    end_date: str | None = None


class PhaseUpdate(BaseModel):
    """阶段更新模型"""

    category_id: str | None = None  # 可以更新分类，但必须从基础数据中选择
    description: str | None = None
    sequence: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    progress_percent: float | None = None


@router.post("", response_model=PhaseResponse)
async def create_phase(
    phase_data: PhaseCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """创建项目阶段（需要项目CREATE权限）"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog
        from sqlalchemy import func

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 验证项目是否存在
        try:
            project_id = UUID(phase_data.project_id)
            UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的项目ID或用户ID")

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 验证并获取基础数据分类
        from database.src.models.basic_data_models import BasicDataCategory

        try:
            category_id = UUID(phase_data.category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的分类ID")

        category = (
            db.query(BasicDataCategory)
            .filter(
                BasicDataCategory.id == category_id,
                BasicDataCategory.category_type == "project_phase",
                BasicDataCategory.is_active,
            )
            .first()
        )

        if not category:
            raise HTTPException(status_code=404, detail="项目阶段分类不存在或已禁用")

        # 解析日期
        start_date = None
        end_date = None
        if phase_data.start_date:
            try:
                start_date = datetime.fromisoformat(phase_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                start_date = datetime.strptime(phase_data.start_date, "%Y-%m-%d").date()
        if phase_data.end_date:
            try:
                end_date = datetime.fromisoformat(phase_data.end_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                end_date = datetime.strptime(phase_data.end_date, "%Y-%m-%d").date()

        # 自动设置sequence（如果未提供）
        sequence = phase_data.sequence
        if sequence is None:
            max_sequence = (
                db.query(func.max(ProjectPhase.sequence)).filter(ProjectPhase.project_id == project_id).scalar() or 0
            )
            sequence = max_sequence + 1

        # 创建阶段（名称从基础数据同步）
        phase = ProjectPhase(
            project_id=project_id,
            category_id=category_id,
            name=category.name,  # 从基础数据同步名称
            description=phase_data.description,
            sequence=sequence,
            start_date=start_date,
            end_date=end_date,
            progress_percent=0.0,
        )

        db.add(phase)
        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="project_phase",
                resource_id=str(phase.id),
                details={"project_id": str(project_id), "category_id": str(category_id), "name": category.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        return PhaseResponse(
            id=str(phase.id),
            project_id=str(phase.project_id),
            category_id=str(phase.category_id),
            name=phase.name,
            description=phase.description,
            sequence=phase.sequence,
            start_date=phase.start_date.isoformat() if phase.start_date else None,
            end_date=phase.end_date.isoformat() if phase.end_date else None,
            progress_percent=phase.progress_percent or 0.0,
            project_name=project.name,
            created_at=phase.created_at.isoformat() if phase.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建阶段失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建阶段失败: {e!s}")


@router.put("/{phase_id}", response_model=PhaseResponse)
async def update_phase(
    phase_id: str, phase_data: PhaseUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """更新项目阶段"""
    try:
        from datetime import datetime

        from database.src.models.project_models import Project
        from database.src.models.system_models import AuditLog

        try:
            phase_uuid = UUID(phase_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的阶段ID")

        phase = db.query(ProjectPhase).filter(ProjectPhase.id == phase_uuid).first()
        if not phase:
            raise HTTPException(status_code=404, detail="阶段不存在")

        # 更新字段
        if phase_data.category_id is not None:
            # 验证并更新基础数据分类
            from database.src.models.basic_data_models import BasicDataCategory

            try:
                category_id = UUID(phase_data.category_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的分类ID")

            category = (
                db.query(BasicDataCategory)
                .filter(
                    BasicDataCategory.id == category_id,
                    BasicDataCategory.category_type == "project_phase",
                    BasicDataCategory.is_active,
                )
                .first()
            )

            if not category:
                raise HTTPException(status_code=404, detail="项目阶段分类不存在或已禁用")

            phase.category_id = category_id
            phase.name = category.name  # 同步名称

        if phase_data.description is not None:
            phase.description = phase_data.description
        if phase_data.sequence is not None:
            phase.sequence = phase_data.sequence
        if phase_data.start_date is not None:
            try:
                phase.start_date = datetime.fromisoformat(phase_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                phase.start_date = datetime.strptime(phase_data.start_date, "%Y-%m-%d").date()
        if phase_data.end_date is not None:
            try:
                phase.end_date = datetime.fromisoformat(phase_data.end_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                phase.end_date = datetime.strptime(phase_data.end_date, "%Y-%m-%d").date()
        if phase_data.progress_percent is not None:
            phase.progress_percent = phase_data.progress_percent

        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="project_phase",
                resource_id=str(phase.id),
                details={"category_id": str(phase.category_id) if phase.category_id else None},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        project = db.query(Project).filter(Project.id == phase.project_id).first()

        return PhaseResponse(
            id=str(phase.id),
            project_id=str(phase.project_id),
            name=phase.name,
            description=phase.description,
            sequence=phase.sequence,
            start_date=phase.start_date.isoformat() if phase.start_date else None,
            end_date=phase.end_date.isoformat() if phase.end_date else None,
            progress_percent=phase.progress_percent or 0.0,
            project_name=project.name if project else None,
            created_at=phase.created_at.isoformat() if phase.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新阶段失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新阶段失败: {e!s}")


@router.delete("/{phase_id}")
async def delete_phase(phase_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """删除项目阶段"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            phase_uuid = UUID(phase_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的阶段ID")

        phase = db.query(ProjectPhase).filter(ProjectPhase.id == phase_uuid).first()
        if not phase:
            raise HTTPException(status_code=404, detail="阶段不存在")

        phase_name = phase.name

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="project_phase",
                resource_id=str(phase.id),
                details={"name": phase_name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(phase)
        db.commit()

        return {"message": "阶段已删除", "id": phase_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除阶段失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除阶段失败: {e!s}")


@router.patch("/{phase_id}/reorder")
async def reorder_phase(
    phase_id: str,
    new_sequence: int = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """调整阶段顺序"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            phase_uuid = UUID(phase_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的阶段ID")

        phase = db.query(ProjectPhase).filter(ProjectPhase.id == phase_uuid).first()
        if not phase:
            raise HTTPException(status_code=404, detail="阶段不存在")

        old_sequence = phase.sequence
        project_id = phase.project_id

        # 如果新顺序大于旧顺序，需要将中间阶段的sequence减1
        # 如果新顺序小于旧顺序，需要将中间阶段的sequence加1
        if new_sequence > old_sequence:
            db.query(ProjectPhase).filter(
                ProjectPhase.project_id == project_id,
                ProjectPhase.sequence > old_sequence,
                ProjectPhase.sequence <= new_sequence,
                ProjectPhase.id != phase_uuid,
            ).update({ProjectPhase.sequence: ProjectPhase.sequence - 1})
        elif new_sequence < old_sequence:
            db.query(ProjectPhase).filter(
                ProjectPhase.project_id == project_id,
                ProjectPhase.sequence >= new_sequence,
                ProjectPhase.sequence < old_sequence,
                ProjectPhase.id != phase_uuid,
            ).update({ProjectPhase.sequence: ProjectPhase.sequence + 1})

        phase.sequence = new_sequence
        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="project_phase",
                resource_id=str(phase.id),
                details={"action": "reorder", "old_sequence": old_sequence, "new_sequence": new_sequence},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        return {"message": "阶段顺序已调整", "id": phase_id, "new_sequence": new_sequence}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调整阶段顺序失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"调整阶段顺序失败: {e!s}")

