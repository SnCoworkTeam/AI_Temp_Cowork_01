"""
项目计划管理路由
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.src.core.session import get_db
from database.src.models.basic_data_models import BasicDataCategory
from database.src.models.project_models import (
    PlanTaskStatus,
    Project,
    ProjectPhase,
    ProjectPlan,
    ProjectPlanTask,
    ProjectTemplate,
)

from ..middleware.project_permissions import ProjectPermission, check_project_permission
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class ProjectPlanResponse(BaseModel):
    """项目计划响应模型"""

    id: str
    project_id: str
    project_name: str | None = None
    name: str
    description: str | None = None
    version: str
    is_active: bool
    is_baseline: bool
    start_date: str | None = None
    end_date: str | None = None
    baseline_start_date: str | None = None
    baseline_end_date: str | None = None
    template_id: str | None = None
    task_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectPlanListResponse(BaseModel):
    """项目计划列表响应"""

    total: int
    items: list[ProjectPlanResponse]


class ProjectPlanTaskResponse(BaseModel):
    """项目计划任务响应模型"""

    id: str
    plan_id: str
    phase_id: str | None = None
    phase_name: str | None = None
    milestone_id: str | None = None
    milestone_name: str | None = None
    category_id: str
    category_name: str | None = None
    category_code: str | None = None
    name: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    dependencies: list[dict] = []
    predecessors: list[str] = []
    successors: list[str] = []
    assignee_id: str | None = None
    assignee_name: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    estimated_effort: float | None = None
    progress_percent: float = 0.0
    status: str
    priority: str
    is_critical: bool
    early_start: str | None = None
    early_finish: str | None = None
    late_start: str | None = None
    late_finish: str | None = None
    total_float: float | None = None
    free_float: float | None = None
    actual_task_id: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectPlanCreate(BaseModel):
    """创建项目计划请求模型"""

    name: str
    description: str | None = None
    version: str | None = "1.0"
    start_date: str | None = None
    end_date: str | None = None
    template_id: str | None = None


class ProjectPlanUpdate(BaseModel):
    """更新项目计划请求模型"""

    name: str | None = None
    description: str | None = None
    version: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_active: bool | None = None
    is_baseline: bool | None = None
    template_id: str | None = None


class ProjectPlanTaskCreate(BaseModel):
    """创建项目计划任务请求模型"""

    phase_id: str | None = None
    milestone_id: str | None = None
    category_id: str
    name: str
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    assignee_id: str | None = None
    estimated_hours: float | None = None
    priority: str | None = "medium"
    status: str | None = "planned"


class ProjectPlanTaskUpdate(BaseModel):
    """更新项目计划任务请求模型"""

    phase_id: str | None = None
    milestone_id: str | None = None
    category_id: str | None = None
    name: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_days: int | None = None
    assignee_id: str | None = None
    estimated_hours: float | None = None
    priority: str | None = None
    status: str | None = None
    progress_percent: float | None = None


# 项目计划CRUD接口
@router.get("/projects/{project_id}/plans", response_model=ProjectPlanListResponse)
async def list_project_plans(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取项目计划列表"""
    try:
        project_uuid = UUID(project_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.READ, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限访问该项目")

        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 构建查询
        query = db.query(ProjectPlan).filter(ProjectPlan.project_id == project_uuid)

        if is_active is not None:
            query = query.filter(ProjectPlan.is_active == is_active)

        total = query.count()
        plans = query.order_by(ProjectPlan.created_at.desc()).offset(skip).limit(limit).all()

        # 构建响应
        items = []
        for plan in plans:
            # 统计任务数量
            task_count = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan.id).count()

            items.append(
                ProjectPlanResponse(
                    id=str(plan.id),
                    project_id=str(plan.project_id),
                    project_name=project.name,
                    name=plan.name,
                    description=plan.description,
                    version=plan.version,
                    is_active=plan.is_active,
                    is_baseline=plan.is_baseline,
                    start_date=plan.start_date.isoformat() if plan.start_date else None,
                    end_date=plan.end_date.isoformat() if plan.end_date else None,
                    baseline_start_date=plan.baseline_start_date.isoformat() if plan.baseline_start_date else None,
                    baseline_end_date=plan.baseline_end_date.isoformat() if plan.baseline_end_date else None,
                    template_id=str(plan.template_id) if plan.template_id else None,
                    task_count=task_count,
                    created_at=plan.created_at.isoformat() if plan.created_at else "",
                    updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
                )
            )

        return ProjectPlanListResponse(total=total, items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目计划列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目计划列表失败: {e!s}")


@router.get("/projects/{project_id}/plans/{plan_id}", response_model=ProjectPlanResponse)
async def get_project_plan(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取项目计划详情"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID或计划ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.READ, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限访问该项目")

        # 检查计划是否存在
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_uuid, ProjectPlan.project_id == project_uuid).first()
        if not plan:
            raise HTTPException(status_code=404, detail="项目计划不存在")

        # 获取项目信息
        project = db.query(Project).filter(Project.id == project_uuid).first()

        # 统计任务数量
        task_count = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan.id).count()

        return ProjectPlanResponse(
            id=str(plan.id),
            project_id=str(plan.project_id),
            project_name=project.name if project else None,
            name=plan.name,
            description=plan.description,
            version=plan.version,
            is_active=plan.is_active,
            is_baseline=plan.is_baseline,
            start_date=plan.start_date.isoformat() if plan.start_date else None,
            end_date=plan.end_date.isoformat() if plan.end_date else None,
            baseline_start_date=plan.baseline_start_date.isoformat() if plan.baseline_start_date else None,
            baseline_end_date=plan.baseline_end_date.isoformat() if plan.baseline_end_date else None,
            template_id=str(plan.template_id) if plan.template_id else None,
            task_count=task_count,
            created_at=plan.created_at.isoformat() if plan.created_at else "",
            updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目计划详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目计划详情失败: {e!s}")


@router.post("/projects/{project_id}/plans", response_model=ProjectPlanResponse, status_code=201)
async def create_project_plan(
    project_id: str,
    plan_data: ProjectPlanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """创建项目计划（支持基于模板）"""
    try:
        project_uuid = UUID(project_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.CREATE, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限创建项目计划")

        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 解析日期
        start_date = None
        end_date = None
        if plan_data.start_date:
            try:
                start_date = datetime.strptime(plan_data.start_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的开始日期格式") from err
        if plan_data.end_date:
            try:
                end_date = datetime.strptime(plan_data.end_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的结束日期格式") from err

        # 解析模板ID
        template_id = None
        if plan_data.template_id:
            try:
                template_id = UUID(plan_data.template_id)
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的模板ID") from err

        # 创建计划
        plan = ProjectPlan(
            project_id=project_uuid,
            name=plan_data.name,
            description=plan_data.description,
            version=plan_data.version or "1.0",
            start_date=start_date,
            end_date=end_date,
            template_id=template_id,
            is_active=True,
            is_baseline=False,
        )

        db.add(plan)
        db.flush()

        # 如果提供了模板ID，从模板创建阶段
        if template_id:
            template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
            if template and template.template_structure:
                phases_data = template.template_structure.get("phases", [])

                for phase_data in phases_data:
                    try:
                        category_id = UUID(phase_data["category_id"])
                    except (ValueError, KeyError):
                        logger.warning(f"跳过无效的阶段分类ID: {phase_data.get('category_id')}")
                        continue

                    category = (
                        db.query(BasicDataCategory)
                        .filter(
                            BasicDataCategory.id == category_id,
                            BasicDataCategory.category_type == "project_phase",
                        )
                        .first()
                    )

                    if category:
                        # 检查阶段是否已存在（避免重复创建）
                        existing_phase = (
                            db.query(ProjectPhase)
                            .filter(
                                ProjectPhase.project_id == project_uuid,
                                ProjectPhase.category_id == category_id,
                            )
                            .first()
                        )

                        if not existing_phase:
                            # 创建项目阶段
                            phase = ProjectPhase(
                                project_id=project_uuid,
                                category_id=category_id,
                                name=category.name,
                                sequence=phase_data.get("sequence", 0),
                                description=f"从模板'{template.name}'自动创建",
                            )
                            db.add(phase)

                # 更新模板使用次数
                template.usage_count = (template.usage_count or 0) + 1

        db.commit()
        db.refresh(plan)

        # 统计任务数量
        task_count = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan.id).count()

        return ProjectPlanResponse(
            id=str(plan.id),
            project_id=str(plan.project_id),
            project_name=project.name,
            name=plan.name,
            description=plan.description,
            version=plan.version,
            is_active=plan.is_active,
            is_baseline=plan.is_baseline,
            start_date=plan.start_date.isoformat() if plan.start_date else None,
            end_date=plan.end_date.isoformat() if plan.end_date else None,
            baseline_start_date=plan.baseline_start_date.isoformat() if plan.baseline_start_date else None,
            baseline_end_date=plan.baseline_end_date.isoformat() if plan.baseline_end_date else None,
            template_id=str(plan.template_id) if plan.template_id else None,
            task_count=task_count,
            created_at=plan.created_at.isoformat() if plan.created_at else "",
            updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目计划失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建项目计划失败: {e!s}")


@router.put("/projects/{project_id}/plans/{plan_id}", response_model=ProjectPlanResponse)
async def update_project_plan(
    project_id: str,
    plan_id: str,
    plan_data: ProjectPlanUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新项目计划"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID或计划ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.UPDATE, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限更新项目计划")

        # 检查计划是否存在
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_uuid, ProjectPlan.project_id == project_uuid).first()
        if not plan:
            raise HTTPException(status_code=404, detail="项目计划不存在")

        # 更新字段
        if plan_data.name is not None:
            plan.name = plan_data.name
        if plan_data.description is not None:
            plan.description = plan_data.description
        if plan_data.version is not None:
            plan.version = plan_data.version
        if plan_data.start_date is not None:
            try:
                plan.start_date = datetime.strptime(plan_data.start_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的开始日期格式") from err
        if plan_data.end_date is not None:
            try:
                plan.end_date = datetime.strptime(plan_data.end_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的结束日期格式") from err
        if plan_data.is_active is not None:
            plan.is_active = plan_data.is_active
        if plan_data.is_baseline is not None:
            plan.is_baseline = plan_data.is_baseline
        if plan_data.template_id is not None:
            try:
                template_uuid = UUID(plan_data.template_id)
                # 验证模板是否存在
                template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_uuid).first()
                if not template:
                    raise HTTPException(status_code=404, detail="模板不存在")
                plan.template_id = template_uuid
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的模板ID") from err

        db.commit()
        db.refresh(plan)

        # 获取项目信息
        project = db.query(Project).filter(Project.id == project_uuid).first()

        # 统计任务数量
        task_count = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan.id).count()

        return ProjectPlanResponse(
            id=str(plan.id),
            project_id=str(plan.project_id),
            project_name=project.name if project else None,
            name=plan.name,
            description=plan.description,
            version=plan.version,
            is_active=plan.is_active,
            is_baseline=plan.is_baseline,
            start_date=plan.start_date.isoformat() if plan.start_date else None,
            end_date=plan.end_date.isoformat() if plan.end_date else None,
            baseline_start_date=plan.baseline_start_date.isoformat() if plan.baseline_start_date else None,
            baseline_end_date=plan.baseline_end_date.isoformat() if plan.baseline_end_date else None,
            template_id=str(plan.template_id) if plan.template_id else None,
            task_count=task_count,
            created_at=plan.created_at.isoformat() if plan.created_at else "",
            updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目计划失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新项目计划失败: {e!s}")


@router.delete("/projects/{project_id}/plans/{plan_id}", status_code=204)
async def delete_project_plan(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """删除项目计划"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID或计划ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.DELETE, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限删除该项目")

        # 检查计划是否存在
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_uuid, ProjectPlan.project_id == project_uuid).first()
        if not plan:
            raise HTTPException(status_code=404, detail="项目计划不存在")

        # 删除计划（级联删除任务）
        db.delete(plan)
        db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目计划失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除项目计划失败: {e!s}")


# 添加任务管理接口
@router.post("/projects/{project_id}/plans/{plan_id}/tasks", response_model=ProjectPlanTaskResponse, status_code=201)
async def create_plan_task(
    project_id: str,
    plan_id: str,
    task_data: ProjectPlanTaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """创建项目计划任务"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID或计划ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.CREATE, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限创建项目计划")

        # 检查计划是否存在
        plan = (
            db.query(ProjectPlan)
            .filter(
                ProjectPlan.id == plan_uuid,
                ProjectPlan.project_id == project_uuid,
            )
            .first()
        )
        if not plan:
            raise HTTPException(status_code=404, detail="项目计划不存在")

        # 检查阶段是否存在(如果提供了phase_id)
        phase_uuid = None
        phase = None
        if task_data.phase_id:
            try:
                phase_uuid = UUID(task_data.phase_id)
                phase = (
                    db.query(ProjectPhase)
                    .filter(
                        ProjectPhase.id == phase_uuid,
                        ProjectPhase.project_id == project_uuid,
                    )
                    .first()
                )
                if not phase:
                    raise HTTPException(status_code=404, detail="项目阶段不存在")
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的阶段ID") from err

        # 检查任务分类是否存在
        try:
            category_uuid = UUID(task_data.category_id)
            category = (
                db.query(BasicDataCategory)
                .filter(
                    BasicDataCategory.id == category_uuid,
                )
                .first()
            )
            if not category:
                raise HTTPException(status_code=404, detail="任务分类不存在")
        except ValueError as err:
            raise HTTPException(status_code=400, detail="无效的分类ID") from err

        # 解析日期
        start_date = None
        end_date = None
        if task_data.start_date:
            try:
                start_date = datetime.strptime(task_data.start_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的开始日期格式") from err
        if task_data.end_date:
            try:
                end_date = datetime.strptime(task_data.end_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的结束日期格式") from err

        # 创建任务
        task = ProjectPlanTask(
            plan_id=plan_uuid,
            phase_id=phase_uuid,
            category_id=category_uuid,
            name=task_data.name,
            description=task_data.description,
            start_date=start_date,
            end_date=end_date,
            duration_days=task_data.duration_days,
            assignee_id=UUID(task_data.assignee_id) if task_data.assignee_id else None,
            estimated_hours=task_data.estimated_hours,
            priority=task_data.priority or "medium",
            status=PlanTaskStatus(task_data.status or "planned"),
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 构建响应
        return ProjectPlanTaskResponse(
            id=str(task.id),
            plan_id=str(task.plan_id),
            phase_id=str(task.phase_id) if task.phase_id else None,
            phase_name=phase.name if phase_uuid and phase else None,
            category_id=str(task.category_id),
            category_name=category.name if category else None,
            category_code=category.code if category else None,
            name=task.name,
            description=task.description,
            start_date=task.start_date.isoformat() if task.start_date else None,
            end_date=task.end_date.isoformat() if task.end_date else None,
            duration_days=task.duration_days,
            status=task.status.value,
            priority=task.priority,
            is_critical=task.is_critical,
            progress_percent=task.progress_percent,
            estimated_hours=task.estimated_hours,
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            dependencies=task.dependencies or [],
            predecessors=task.predecessors or [],
            successors=task.successors or [],
            created_at=task.created_at.isoformat() if task.created_at else "",
            updated_at=task.updated_at.isoformat() if task.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目计划任务失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建项目计划任务失败: {e!s}")


@router.put("/projects/{project_id}/plans/{plan_id}/tasks/{task_id}", response_model=ProjectPlanTaskResponse)
async def update_plan_task(
    project_id: str,
    plan_id: str,
    task_id: str,
    task_data: ProjectPlanTaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新项目计划任务"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
        task_uuid = UUID(task_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.CREATE, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限创建项目计划")

        # 检查任务是否存在
        task = (
            db.query(ProjectPlanTask)
            .filter(
                ProjectPlanTask.id == task_uuid,
                ProjectPlanTask.plan_id == plan_uuid,
            )
            .join(ProjectPlan)
            .filter(ProjectPlan.project_id == project_uuid)
            .first()
        )

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 更新字段
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.category_id is not None:
            try:
                category_uuid = UUID(task_data.category_id)
                category = (
                    db.query(BasicDataCategory)
                    .filter(
                        BasicDataCategory.id == category_uuid,
                    )
                    .first()
                )
                if not category:
                    raise HTTPException(status_code=404, detail="任务分类不存在")
                task.category_id = category_uuid
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的分类ID") from err
        if task_data.start_date is not None:
            try:
                task.start_date = datetime.strptime(task_data.start_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的开始日期格式") from err
        if task_data.end_date is not None:
            try:
                task.end_date = datetime.strptime(task_data.end_date, "%Y-%m-%d").date()
            except ValueError as err:
                raise HTTPException(status_code=400, detail="无效的结束日期格式") from err
        if task_data.duration_days is not None:
            task.duration_days = task_data.duration_days
        if task_data.assignee_id is not None:
            task.assignee_id = UUID(task_data.assignee_id) if task_data.assignee_id else None
        if task_data.estimated_hours is not None:
            task.estimated_hours = task_data.estimated_hours
        if task_data.priority is not None:
            task.priority = task_data.priority
        if task_data.status is not None:
            task.status = PlanTaskStatus(task_data.status)
        if task_data.progress_percent is not None:
            task.progress_percent = task_data.progress_percent

        db.commit()
        db.refresh(task)

        # 获取关联数据
        phase = db.query(ProjectPhase).filter(ProjectPhase.id == task.phase_id).first() if task.phase_id else None
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == task.category_id).first()

        # 构建响应
        return ProjectPlanTaskResponse(
            id=str(task.id),
            plan_id=str(task.plan_id),
            phase_id=str(task.phase_id) if task.phase_id else None,
            phase_name=phase.name if phase else None,
            category_id=str(task.category_id),
            category_name=category.name if category else None,
            category_code=category.code if category else None,
            name=task.name,
            description=task.description,
            start_date=task.start_date.isoformat() if task.start_date else None,
            end_date=task.end_date.isoformat() if task.end_date else None,
            duration_days=task.duration_days,
            status=task.status.value,
            priority=task.priority,
            is_critical=task.is_critical,
            progress_percent=task.progress_percent,
            estimated_hours=task.estimated_hours,
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            dependencies=task.dependencies or [],
            predecessors=task.predecessors or [],
            successors=task.successors or [],
            created_at=task.created_at.isoformat() if task.created_at else "",
            updated_at=task.updated_at.isoformat() if task.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目计划任务失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新项目计划任务失败: {e!s}")


@router.delete("/projects/{project_id}/plans/{plan_id}/tasks/{task_id}", status_code=204)
async def delete_plan_task(
    project_id: str,
    plan_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """删除项目计划任务"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
        task_uuid = UUID(task_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的ID") from err

    # 检查项目权限
    user_id_str = current_user.get("user_id") or current_user.get("id")
    if not user_id_str or user_id_str == "anonymous":
        raise HTTPException(status_code=401, detail="需要登录")
    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="无效的用户ID")

    username = current_user.get("username", "").lower()
    user_roles = current_user.get("roles", [])
    is_admin = (
        username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
    )

    if not check_project_permission(project_uuid, user_uuid, ProjectPermission.UPDATE, db, is_admin=is_admin):
        raise HTTPException(status_code=403, detail="没有权限更新项目计划任务")

    # 检查任务是否存在
    task = (
        db.query(ProjectPlanTask)
        .filter(
            ProjectPlanTask.id == task_uuid,
            ProjectPlanTask.plan_id == plan_uuid,
        )
        .join(ProjectPlan)
        .filter(ProjectPlan.project_id == project_uuid)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()


# 计划树形结构API
class PlanTreeNode(BaseModel):
    """计划树节点模型"""

    id: str
    type: str  # 'phase' or 'task'
    name: str
    category_id: Optional[str] = None
    category_code: Optional[str] = None
    sequence: Optional[int] = None
    is_readonly: bool = False
    phase_id: Optional[str] = None
    status: Optional[str] = None
    progress_percent: Optional[float] = None
    children: List["PlanTreeNode"] = []


class PlanTreeResponse(BaseModel):
    """计划树形结构响应模型"""

    plan_id: str
    plan_name: str
    tree: List[PlanTreeNode]


@router.get("/projects/{project_id}/plans/{plan_id}/tree", response_model=PlanTreeResponse)
async def get_plan_tree(
    project_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取计划树形结构"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的项目ID或计划ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.READ, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限访问该项目")

        # 检查计划是否存在
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_uuid, ProjectPlan.project_id == project_uuid).first()
        if not plan:
            raise HTTPException(status_code=404, detail="项目计划不存在")

        # 如果计划没有关联模板，尝试查找"标准信息化项目管理模板"并关联
        if not plan.template_id:
            default_template = (
                db.query(ProjectTemplate)
                .filter(
                    ProjectTemplate.name.like('%标准信息化项目管理模板%'),
                    ProjectTemplate.is_active == True
                )
                .first()
            )
            if default_template:
                plan.template_id = default_template.id
                db.commit()
                db.refresh(plan)
                logger.info(f"计划 {plan.id} 已自动关联模板 {default_template.name}")

        # 优先从模板获取阶段结构
        tree = []
        if plan.template_id:
            template = db.query(ProjectTemplate).filter(ProjectTemplate.id == plan.template_id).first()
            if template and template.template_structure:
                phases_data = template.template_structure.get("phases", [])

                # 获取计划的所有任务
                tasks = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan_uuid).all()

                # 从模板构建树形结构
                for phase_data in phases_data:
                    try:
                        category_id = UUID(phase_data["category_id"])
                    except (ValueError, KeyError):
                        logger.warning(f"跳过无效的阶段分类ID: {phase_data.get('category_id')}")
                        continue

                    category = (
                        db.query(BasicDataCategory)
                        .filter(BasicDataCategory.id == category_id)
                        .first()
                    )

                    if category:
                        # 查找对应的项目阶段（如果存在）
                        project_phase = (
                            db.query(ProjectPhase)
                            .filter(
                                ProjectPhase.project_id == project_uuid,
                                ProjectPhase.category_id == category_id,
                            )
                            .first()
                        )

                        # 创建阶段节点（只读，从模板获取）
                        phase_node = PlanTreeNode(
                            id=str(project_phase.id) if project_phase else f"phase_{category_id}",
                            type="phase",
                            name=category.name,
                            category_id=str(category_id),
                            category_code=category.code,
                            sequence=phase_data.get("sequence", 0),
                            is_readonly=True,
                            children=[],
                        )

                        # 添加该阶段下的任务（如果有项目阶段）
                        if project_phase:
                            phase_tasks = [t for t in tasks if t.phase_id == project_phase.id]
                            for task in phase_tasks:
                                task_category = (
                                    db.query(BasicDataCategory).filter(BasicDataCategory.id == task.category_id).first()
                                    if task.category_id
                                    else None
                                )

                                task_node = PlanTreeNode(
                                    id=str(task.id),
                                    type="task",
                                    name=task.name,
                                    phase_id=str(task.phase_id) if task.phase_id else None,
                                    status=task.status.value if task.status else None,
                                    progress_percent=task.progress_percent,
                                    category_id=str(task.category_id) if task.category_id else None,
                                    category_code=task_category.code if task_category else None,
                                    is_readonly=False,
                                    children=[],
                                )
                                phase_node.children.append(task_node)

                        tree.append(phase_node)
        else:
            # 如果没有模板，从ProjectPhase表获取阶段
            phases = (
                db.query(ProjectPhase)
                .filter(ProjectPhase.project_id == project_uuid)
                .order_by(ProjectPhase.sequence.asc())
                .all()
            )

            # 获取计划的所有任务
            tasks = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan_uuid).all()

            # 构建树形结构
            for phase in phases:
                # 获取阶段关联的基础数据分类
                category = (
                    db.query(BasicDataCategory).filter(BasicDataCategory.id == phase.category_id).first()
                    if phase.category_id
                    else None
                )

                # 创建阶段节点（只读）
                phase_node = PlanTreeNode(
                    id=str(phase.id),
                    type="phase",
                    name=phase.name,
                    category_id=str(phase.category_id) if phase.category_id else None,
                    category_code=category.code if category else None,
                    sequence=phase.sequence,
                    is_readonly=True,
                    children=[],
                )

                # 添加该阶段下的任务
                phase_tasks = [t for t in tasks if t.phase_id == phase.id]
                for task in phase_tasks:
                    task_category = (
                        db.query(BasicDataCategory).filter(BasicDataCategory.id == task.category_id).first()
                        if task.category_id
                        else None
                    )

                    task_node = PlanTreeNode(
                        id=str(task.id),
                        type="task",
                        name=task.name,
                        phase_id=str(task.phase_id) if task.phase_id else None,
                        status=task.status.value if task.status else None,
                        progress_percent=task.progress_percent,
                        category_id=str(task.category_id) if task.category_id else None,
                        category_code=task_category.code if task_category else None,
                        is_readonly=False,
                        children=[],
                    )
                    phase_node.children.append(task_node)

                tree.append(phase_node)

        return PlanTreeResponse(plan_id=str(plan.id), plan_name=plan.name, tree=tree)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取计划树形结构失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取计划树形结构失败: {e!s}")


# 任务移动接口
class TaskMoveRequest(BaseModel):
    """任务移动请求模型"""

    new_phase_id: str


@router.patch("/projects/{project_id}/plans/{plan_id}/tasks/{task_id}/move", response_model=ProjectPlanTaskResponse)
async def move_plan_task(
    project_id: str,
    plan_id: str,
    task_id: str,
    move_data: TaskMoveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """移动任务到新阶段"""
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id)
        task_uuid = UUID(task_id)
        new_phase_uuid = UUID(move_data.new_phase_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="无效的ID") from err

    try:
        # 检查项目权限
        user_id_str = current_user.get("user_id") or current_user.get("id")
        if not user_id_str or user_id_str == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")
        try:
            user_uuid = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="无效的用户ID")

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not check_project_permission(project_uuid, user_uuid, ProjectPermission.CREATE, db, is_admin=is_admin):
            raise HTTPException(status_code=403, detail="没有权限创建项目计划")

        # 检查任务是否存在
        task = (
            db.query(ProjectPlanTask)
            .filter(
                ProjectPlanTask.id == task_uuid,
                ProjectPlanTask.plan_id == plan_uuid,
            )
            .join(ProjectPlan)
            .filter(ProjectPlan.project_id == project_uuid)
            .first()
        )

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查新阶段是否存在
        new_phase = (
            db.query(ProjectPhase)
            .filter(ProjectPhase.id == new_phase_uuid, ProjectPhase.project_id == project_uuid)
            .first()
        )

        if not new_phase:
            raise HTTPException(status_code=404, detail="新阶段不存在")

        # 更新任务的阶段ID
        task.phase_id = new_phase_uuid

        db.commit()
        db.refresh(task)

        # 获取关联数据
        phase = db.query(ProjectPhase).filter(ProjectPhase.id == task.phase_id).first() if task.phase_id else None
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == task.category_id).first()

        # 构建响应
        return ProjectPlanTaskResponse(
            id=str(task.id),
            plan_id=str(task.plan_id),
            phase_id=str(task.phase_id) if task.phase_id else None,
            phase_name=phase.name if phase else None,
            category_id=str(task.category_id),
            category_name=category.name if category else None,
            category_code=category.code if category else None,
            name=task.name,
            description=task.description,
            start_date=task.start_date.isoformat() if task.start_date else None,
            end_date=task.end_date.isoformat() if task.end_date else None,
            duration_days=task.duration_days,
            status=task.status.value,
            priority=task.priority,
            is_critical=task.is_critical,
            progress_percent=task.progress_percent,
            estimated_hours=task.estimated_hours,
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            dependencies=task.dependencies or [],
            predecessors=task.predecessors or [],
            successors=task.successors or [],
            created_at=task.created_at.isoformat() if task.created_at else "",
            updated_at=task.updated_at.isoformat() if task.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移动任务失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"移动任务失败: {e!s}")

