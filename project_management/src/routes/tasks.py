"""
任务管理路由
"""

import contextlib
import logging
from datetime import datetime
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Project, Task, TaskStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission, get_user_projects
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class TaskResponse(BaseModel):
    """任务响应模型"""

    id: str
    project_id: str
    phase_id: str | None = None
    milestone_id: str | None = None
    name: str
    description: str | None = None
    status: str
    assignee_id: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    completed_date: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    progress_percent: float = 0.0
    project_name: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""

    total: int
    items: list[TaskResponse]


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: str | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取任务列表（只返回用户有权限的项目任务）"""
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

        query = db.query(Task)

        # 只查询用户有权限的项目任务
        # 如果 user_project_ids 是 None，表示管理员，不进行过滤
        if user_project_ids is not None:
            if user_project_ids:
                query = query.filter(Task.project_id.in_(user_project_ids))
            else:
                # 用户没有任何项目权限，返回空列表
                return TaskListResponse(total=0, items=[])

        if project_id:
            try:
                project_uuid = UUID(project_id)
                # 如果不是管理员，检查用户是否有该项目的权限
                if not is_admin and user_project_ids is not None:
                    if project_uuid not in user_project_ids:
                        raise HTTPException(status_code=403, detail="没有权限访问该项目")
                query = query.filter(Task.project_id == project_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        if status:
            try:
                task_status = TaskStatus(status.lower())
                query = query.filter(Task.status == task_status)
            except ValueError:
                pass

        if priority:
            query = query.filter(Task.priority == priority)

        total = query.count()
        tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

        # 获取项目名称
        project_ids = {str(t.project_id) for t in tasks}
        projects = {}
        if project_ids:
            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        items = []
        for task in tasks:
            items.append(
                TaskResponse(
                    id=str(task.id),
                    project_id=str(task.project_id),
                    phase_id=str(task.phase_id) if task.phase_id else None,
                    milestone_id=str(task.milestone_id) if task.milestone_id else None,
                    name=task.name,
                    description=task.description,
                    status=task.status.value if hasattr(task.status, "value") else str(task.status),
                    assignee_id=str(task.assignee_id) if task.assignee_id else None,
                    start_date=task.start_date.isoformat() if task.start_date else None,
                    due_date=task.due_date.isoformat() if task.due_date else None,
                    completed_date=task.completed_date.isoformat() if task.completed_date else None,
                    estimated_hours=task.estimated_hours,
                    actual_hours=task.actual_hours,
                    progress_percent=task.progress_percent or 0.0,
                    project_name=projects.get(str(task.project_id)),
                    priority=getattr(task, "priority", None),
                    assigned_to=None,  # TODO: 从用户表获取
                    created_at=task.created_at.isoformat() if task.created_at else "",
                )
            )

        return TaskListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"获取任务列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {e!s}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取任务详情（需要项目READ权限）"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            task_uuid = UUID(task_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的任务ID或用户ID")

        task = db.query(Task).filter(Task.id == task_uuid).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查用户是否有该项目的READ权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            task.project_id, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限访问该任务")

        project = db.query(Project).filter(Project.id == task.project_id).first()

        return TaskResponse(
            id=str(task.id),
            project_id=str(task.project_id),
            phase_id=str(task.phase_id) if task.phase_id else None,
            milestone_id=str(task.milestone_id) if task.milestone_id else None,
            name=task.name,
            description=task.description,
            status=task.status.value if hasattr(task.status, "value") else str(task.status),
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            start_date=task.start_date.isoformat() if task.start_date else None,
            due_date=task.due_date.isoformat() if task.due_date else None,
            completed_date=task.completed_date.isoformat() if task.completed_date else None,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            progress_percent=task.progress_percent or 0.0,
            project_name=project.name if project else None,
            priority=getattr(task, "priority", None),
            assigned_to=None,  # TODO: 从用户表获取
            created_at=task.created_at.isoformat() if task.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {e!s}")


class TaskCreate(BaseModel):
    """任务创建模型"""

    project_id: str
    phase_id: str | None = None
    milestone_id: str | None = None
    name: str
    description: str | None = None
    status: str | None = "todo"
    assignee_id: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    estimated_hours: float | None = None
    priority: str | None = None


class TaskUpdate(BaseModel):
    """任务更新模型"""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    assignee_id: str | None = None
    start_date: str | None = None
    due_date: str | None = None
    completed_date: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    progress_percent: float | None = None
    priority: str | None = None


@router.post("", response_model=TaskResponse)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """创建任务（需要项目CREATE权限）"""
    try:
        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 验证项目是否存在
        try:
            project_id = UUID(task_data.project_id)
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
            raise HTTPException(status_code=403, detail="没有权限在该项目中创建任务")

        # 解析状态
        status = TaskStatus.TODO
        if task_data.status:
            try:
                status = TaskStatus(task_data.status.lower())
            except ValueError:
                status = TaskStatus.TODO

        # 解析日期
        start_date = None
        due_date = None
        if task_data.start_date:
            try:
                start_date = datetime.fromisoformat(task_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                start_date = datetime.strptime(task_data.start_date, "%Y-%m-%d").date()
        if task_data.due_date:
            try:
                due_date = datetime.fromisoformat(task_data.due_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                due_date = datetime.strptime(task_data.due_date, "%Y-%m-%d").date()

        # 解析phase_id和milestone_id，并验证它们属于同一项目
        phase_id = None
        milestone_id = None

        if task_data.phase_id:
            try:
                phase_id = UUID(task_data.phase_id)
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

        if task_data.milestone_id:
            try:
                milestone_id = UUID(task_data.milestone_id)
                # 验证里程碑属于同一项目
                from database.src.models.project_models import Milestone

                milestone = (
                    db.query(Milestone).filter(Milestone.id == milestone_id, Milestone.project_id == project_id).first()
                )
                if not milestone:
                    raise HTTPException(status_code=400, detail="里程碑不属于该项目")

                # 如果同时设置了phase_id，验证里程碑是否属于该阶段
                if phase_id and milestone.phase_id and milestone.phase_id != phase_id:
                    raise HTTPException(status_code=400, detail="里程碑不属于指定的阶段")
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的里程碑ID")

        # 解析assignee_id
        assignee_id = None
        if task_data.assignee_id:
            with contextlib.suppress(ValueError):
                assignee_id = UUID(task_data.assignee_id)

        # 创建任务
        task = Task(
            project_id=project_id,
            phase_id=phase_id,
            milestone_id=milestone_id,
            name=task_data.name,
            description=task_data.description,
            status=status,
            assignee_id=assignee_id,
            start_date=start_date,
            due_date=due_date,
            estimated_hours=task_data.estimated_hours,
            progress_percent=0.0,
        )

        db.add(task)
        db.flush()

        # 自动更新相关进度
        try:
            from ..services.progress_calculator import ProgressCalculator

            ProgressCalculator.update_related_progresses(task, db)
        except Exception as e:
            logger.warning(f"自动更新进度失败: {e!s}")

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="task",
                resource_id=str(task.id),
                details={"project_id": str(project_id), "name": task_data.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        return TaskResponse(
            id=str(task.id),
            project_id=str(task.project_id),
            phase_id=str(task.phase_id) if task.phase_id else None,
            milestone_id=str(task.milestone_id) if task.milestone_id else None,
            name=task.name,
            description=task.description,
            status=task.status.value if hasattr(task.status, "value") else str(task.status),
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            start_date=task.start_date.isoformat() if task.start_date else None,
            due_date=task.due_date.isoformat() if task.due_date else None,
            completed_date=task.completed_date.isoformat() if task.completed_date else None,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            progress_percent=task.progress_percent or 0.0,
            project_name=project.name,
            priority=getattr(task, "priority", None),
            assigned_to=None,
            created_at=task.created_at.isoformat() if task.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建任务失败: {e!s}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, task_data: TaskUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """更新任务"""
    try:
        from database.src.models.project_models import Project
        from database.src.models.system_models import AuditLog

        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的任务ID")

        task = db.query(Task).filter(Task.id == task_uuid).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 更新字段
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            with contextlib.suppress(ValueError):
                task.status = TaskStatus(task_data.status.lower())
        if task_data.assignee_id is not None:
            with contextlib.suppress(ValueError):
                task.assignee_id = UUID(task_data.assignee_id) if task_data.assignee_id else None
        if task_data.start_date is not None:
            try:
                task.start_date = datetime.fromisoformat(task_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                task.start_date = datetime.strptime(task_data.start_date, "%Y-%m-%d").date()
        if task_data.due_date is not None:
            try:
                task.due_date = datetime.fromisoformat(task_data.due_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                task.due_date = datetime.strptime(task_data.due_date, "%Y-%m-%d").date()
        if task_data.completed_date is not None:
            try:
                task.completed_date = datetime.fromisoformat(task_data.completed_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                task.completed_date = datetime.strptime(task_data.completed_date, "%Y-%m-%d").date()
        if task_data.estimated_hours is not None:
            task.estimated_hours = task_data.estimated_hours
        if task_data.actual_hours is not None:
            task.actual_hours = task_data.actual_hours
        if task_data.progress_percent is not None:
            task.progress_percent = task_data.progress_percent

        db.flush()

        # 自动更新相关进度
        try:
            from ..services.progress_calculator import ProgressCalculator

            ProgressCalculator.update_related_progresses(task, db)
        except Exception as e:
            logger.warning(f"自动更新进度失败: {e!s}")

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="task",
                resource_id=str(task.id),
                details={"name": task_data.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        project = db.query(Project).filter(Project.id == task.project_id).first()

        return TaskResponse(
            id=str(task.id),
            project_id=str(task.project_id),
            phase_id=str(task.phase_id) if task.phase_id else None,
            milestone_id=str(task.milestone_id) if task.milestone_id else None,
            name=task.name,
            description=task.description,
            status=task.status.value if hasattr(task.status, "value") else str(task.status),
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            start_date=task.start_date.isoformat() if task.start_date else None,
            due_date=task.due_date.isoformat() if task.due_date else None,
            completed_date=task.completed_date.isoformat() if task.completed_date else None,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            progress_percent=task.progress_percent or 0.0,
            project_name=project.name if project else None,
            priority=getattr(task, "priority", None),
            assigned_to=None,
            created_at=task.created_at.isoformat() if task.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务失败: {e!s}")


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """删除任务"""
    try:
        from database.src.models.system_models import AuditLog

        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的任务ID")

        task = db.query(Task).filter(Task.id == task_uuid).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        task_name = task.name
        phase_id = task.phase_id
        project_id = task.project_id

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="task",
                resource_id=str(task.id),
                details={"name": task_name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(task)
        db.flush()

        # 自动更新相关进度（删除后）
        try:
            from ..services.progress_calculator import ProgressCalculator

            if phase_id:
                ProgressCalculator.update_phase_progress(phase_id, db)
            ProgressCalculator.update_project_progress(project_id, db)
        except Exception as e:
            logger.warning(f"自动更新进度失败: {e!s}")

        db.commit()

        return {"message": "任务已删除", "id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除任务失败: {e!s}")
