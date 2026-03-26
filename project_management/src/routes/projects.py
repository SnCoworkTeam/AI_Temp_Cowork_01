"""
项目管理路由
"""

import contextlib
import logging
from datetime import date, datetime
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import (
    Project,
    ProjectMember,
    ProjectMemberRole,
    ProjectStatus,
)
from database.src.models.system_models import AuditLog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import (
    ProjectPermission,
    require_project_permission,
)
from .auth import require_auth
from .services.excel_parser import ExcelParser

router = APIRouter()
logger = logging.getLogger(__name__)


class ProjectResponse(BaseModel):
    """项目响应模型"""

    id: str
    project_code: str
    name: str
    description: str | None = None
    status: str
    priority: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    progress_percent: float = 0.0
    health_score: float = 0.0
    created_at: str
    updated_at: str
    basic_data_categories: list[dict] | None = []  # 基础数据分类列表
    reporter_id: str | None = None  # 填报人ID
    reporter_name: str | None = None  # 填报人姓名
    manager_id: str | None = None  # 项目经理ID
    manager_name: str | None = None  # 项目经理姓名
    milestone_implementation_start: str | None = None  # 实施启动日期
    milestone_solution_confirmation: str | None = None  # 方案确认日期
    milestone_delivery_online: str | None = None  # 交付上线日期
    milestone_project_acceptance: str | None = None  # 项目验收日期
    requires_weekly_report: bool | None = False  # 是否编写周报

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""

    total: int
    items: list[ProjectResponse]


class ProjectCreate(BaseModel):
    """创建项目请求模型"""

    project_code: str | None = None  # 可选，如果不提供则自动生成
    name: str
    description: str | None = None
    status: str | None = "planning"
    priority: str | None = "medium"
    manager_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    budget: float | None = None
    requires_weekly_report: bool | None = False  # 是否编写周报


class ProjectUpdate(BaseModel):
    """更新项目请求模型"""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    manager_id: str | None = None
    reporter_id: str | None = None  # 填报人ID
    start_date: str | None = None
    end_date: str | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    budget: float | None = None
    actual_cost: float | None = None
    progress_percent: float | None = None
    health_score: float | None = None
    milestone_implementation_start: str | None = None  # 实施启动日期
    milestone_solution_confirmation: str | None = None  # 方案确认日期
    milestone_delivery_online: str | None = None  # 交付上线日期
    milestone_project_acceptance: str | None = None  # 项目验收日期
    requires_weekly_report: bool | None = None  # 是否编写周报


async def log_audit(
    db: Session,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict | None = None,
):
    """记录审计日志"""
    try:
        from datetime import datetime

        audit_log = AuditLog(
            user_id=UUID(user_id) if user_id != "anonymous" else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            timestamp=datetime.utcnow(),
            result="success",
        )
        db.add(audit_log)
        db.flush()
    except Exception as e:
        logger.warning(f"记录审计日志失败: {e!s}")


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取项目列表（管理员可以看到所有项目，普通用户只能看到有权限的项目）"""
    try:
        from ..middleware.project_permissions import get_user_projects

        # 安全地解析user_id
        user_id_str = current_user.get("user_id")
        if not user_id_str or user_id_str == "anonymous":
            # 匿名用户，返回空列表
            return ProjectListResponse(total=0, items=[])

        try:
            user_id = UUID(user_id_str)
        except (ValueError, TypeError):
            logger.warning(f"无效的user_id格式: {user_id_str}")
            return ProjectListResponse(total=0, items=[])

        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])

        # 检查是否是管理员（admin账号或roles中包含admin）
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        # 获取用户有权限的项目ID列表
        user_project_ids = get_user_projects(user_id, db, is_admin=is_admin)

        # 如果是管理员，返回所有项目
        if user_project_ids is None:
            query = db.query(Project)
        # 如果没有权限的项目，返回空列表
        elif not user_project_ids:
            return ProjectListResponse(total=0, items=[])
        else:
            query = db.query(Project).filter(Project.id.in_(user_project_ids))

        if status:
            query = query.filter(Project.status == status)

        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

        # 获取项目的基础数据分类
        from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
        from database.src.models.user_models import User

        project_responses = []
        for p in projects:
            # 查询项目关联的基础数据分类
            mappings = db.query(ProjectBasicDataMapping).filter(ProjectBasicDataMapping.project_id == p.id).all()

            basic_data_categories = []
            for mapping in mappings:
                category = db.query(BasicDataCategory).filter(BasicDataCategory.id == mapping.category_id).first()
                if category:
                    basic_data_categories.append(
                        {
                            "id": str(category.id),
                            "category_type": category.category_type,
                            "code": category.code,
                            "name": category.name,
                            "description": category.description,
                        }
                    )

            # 查询填报人信息
            reporter_name = None
            if p.reporter_id:
                reporter = db.query(User).filter(User.id == p.reporter_id).first()
                if reporter:
                    reporter_name = reporter.full_name or reporter.username

            # 查询项目经理信息
            manager_name = None
            if p.manager_id:
                manager = db.query(User).filter(User.id == p.manager_id).first()
                if manager:
                    manager_name = manager.full_name or manager.username

            project_responses.append(
                ProjectResponse(
                    id=str(p.id),
                    project_code=p.project_code,
                    name=p.name,
                    description=p.description,
                    status=p.status.value if hasattr(p.status, "value") else str(p.status),
                    priority=p.priority,
                    start_date=p.start_date.isoformat() if p.start_date else None,
                    end_date=p.end_date.isoformat() if p.end_date else None,
                    progress_percent=p.progress_percent or 0.0,
                    health_score=p.health_score or 0.0,
                    created_at=(p.created_at.isoformat() if p.created_at else datetime.utcnow().isoformat()),
                    updated_at=(p.updated_at.isoformat() if p.updated_at else datetime.utcnow().isoformat()),
                    basic_data_categories=basic_data_categories,
                    reporter_id=str(p.reporter_id) if p.reporter_id else None,
                    reporter_name=reporter_name,
                    manager_id=str(p.manager_id) if p.manager_id else None,
                    manager_name=manager_name,
                    milestone_implementation_start=(
                        p.milestone_implementation_start.isoformat() if p.milestone_implementation_start else None
                    ),
                    milestone_solution_confirmation=(
                        p.milestone_solution_confirmation.isoformat() if p.milestone_solution_confirmation else None
                    ),
                    milestone_delivery_online=(
                        p.milestone_delivery_online.isoformat() if p.milestone_delivery_online else None
                    ),
                    milestone_project_acceptance=(
                        p.milestone_project_acceptance.isoformat() if p.milestone_project_acceptance else None
                    ),
                    requires_weekly_report=(
                        getattr(p, "requires_weekly_report", False) if hasattr(p, "requires_weekly_report") else False
                    ),
                )
            )

        return ProjectListResponse(total=total, items=project_responses)
    except Exception as e:
        logger.error(f"获取项目列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {e!s}")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.READ)),
):
    """获取项目详情（需要项目查看权限）"""
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 查询项目关联的基础数据分类
        from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
        from database.src.models.user_models import User

        mappings = db.query(ProjectBasicDataMapping).filter(ProjectBasicDataMapping.project_id == project.id).all()

        basic_data_categories = []
        for mapping in mappings:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == mapping.category_id).first()
            if category:
                basic_data_categories.append(
                    {
                        "id": str(category.id),
                        "category_type": category.category_type,
                        "code": category.code,
                        "name": category.name,
                        "description": category.description,
                    }
                )

        # 查询填报人信息
        reporter_name = None
        if project.reporter_id:
            reporter = db.query(User).filter(User.id == project.reporter_id).first()
            if reporter:
                reporter_name = reporter.full_name or reporter.username

        # 查询项目经理信息
        manager_name = None
        if project.manager_id:
            manager = db.query(User).filter(User.id == project.manager_id).first()
            if manager:
                manager_name = manager.full_name or manager.username

        return ProjectResponse(
            id=str(project.id),
            project_code=project.project_code,
            name=project.name,
            description=project.description,
            status=(project.status.value if hasattr(project.status, "value") else str(project.status)),
            priority=project.priority,
            start_date=project.start_date.isoformat() if project.start_date else None,
            end_date=project.end_date.isoformat() if project.end_date else None,
            progress_percent=project.progress_percent or 0.0,
            health_score=project.health_score or 0.0,
            created_at=(project.created_at.isoformat() if project.created_at else datetime.utcnow().isoformat()),
            updated_at=(project.updated_at.isoformat() if project.updated_at else datetime.utcnow().isoformat()),
            basic_data_categories=basic_data_categories,
            reporter_id=str(project.reporter_id) if project.reporter_id else None,
            reporter_name=reporter_name,
            manager_id=str(project.manager_id) if project.manager_id else None,
            manager_name=manager_name,
            milestone_implementation_start=(
                project.milestone_implementation_start.isoformat() if project.milestone_implementation_start else None
            ),
            milestone_solution_confirmation=(
                project.milestone_solution_confirmation.isoformat() if project.milestone_solution_confirmation else None
            ),
            milestone_delivery_online=(
                project.milestone_delivery_online.isoformat() if project.milestone_delivery_online else None
            ),
            milestone_project_acceptance=(
                project.milestone_project_acceptance.isoformat() if project.milestone_project_acceptance else None
            ),
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    except Exception as e:
        logger.error(f"获取项目详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {e!s}")


def generate_project_code(db: Session) -> str:
    """自动生成项目编码：ZHGJ-年-4位数字编号"""
    from datetime import datetime

    current_year = datetime.now().year
    prefix = f"ZHGJ-{current_year}-"

    # 查询当前年份的最大编号
    # 使用正则表达式或字符串匹配查找当前年份的项目编码

    # 查找所有以当前年份前缀开头的项目编码
    projects = db.query(Project).filter(Project.project_code.like(f"{prefix}%")).all()

    max_number = 0
    for project in projects:
        try:
            # 提取编号部分（例如：ZHGJ-2025-0001 -> 0001）
            code_part = project.project_code.replace(prefix, "")
            number = int(code_part)
            max_number = max(max_number, number)
        except (ValueError, AttributeError):
            continue

    # 生成下一个编号（4位数字，补零）
    next_number = max_number + 1
    return f"{prefix}{next_number:04d}"



@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """创建新项目"""
    try:
        # 如果没有提供项目编码，自动生成
        project_code = project_data.project_code
        if not project_code:
            project_code = generate_project_code(db)

        # 检查项目编码是否已存在
        existing = db.query(Project).filter(Project.project_code == project_code).first()

        if existing:
            # 如果自动生成的编码已存在，重新生成
            if not project_data.project_code:
                project_code = generate_project_code(db)
                existing = db.query(Project).filter(Project.project_code == project_code).first()
                if existing:
                    raise HTTPException(status_code=400, detail="无法生成唯一的项目编码，请稍后重试")
            else:
                raise HTTPException(status_code=400, detail=f"项目编码 {project_code} 已存在")

        # 解析日期
        start_date = None
        end_date = None
        if project_data.start_date:
            try:
                start_date = datetime.fromisoformat(project_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                start_date = datetime.strptime(project_data.start_date, "%Y-%m-%d").date()
        if project_data.end_date:
            try:
                end_date = datetime.fromisoformat(project_data.end_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                end_date = datetime.strptime(project_data.end_date, "%Y-%m-%d").date()

        # 解析状态
        status = ProjectStatus.PLANNING
        if project_data.status:
            try:
                status = ProjectStatus(project_data.status.lower())
            except ValueError:
                status = ProjectStatus.PLANNING

        # 解析manager_id
        manager_id = None
        if project_data.manager_id:
            with contextlib.suppress(ValueError):
                manager_id = UUID(project_data.manager_id)

        # 创建项目
        project = Project(
            project_code=project_code,
            name=project_data.name,
            description=project_data.description,
            status=status,
            priority=project_data.priority or "medium",
            manager_id=manager_id,
            start_date=start_date,
            end_date=end_date,
            requires_weekly_report=(
                project_data.requires_weekly_report if project_data.requires_weekly_report is not None else False
            ),
        )

        db.add(project)
        db.flush()

        # 关联基础数据分类
        basic_data_category_ids = getattr(project_data, "basic_data_category_ids", None)
        if basic_data_category_ids and len(basic_data_category_ids) > 0:
            from database.src.models.basic_data_models import (
                BasicDataCategory,
                ProjectBasicDataMapping,
            )

            for category_id_str in basic_data_category_ids:
                try:
                    category_id = UUID(category_id_str)
                    # 验证分类是否存在
                    category = db.query(BasicDataCategory).filter(BasicDataCategory.id == category_id).first()
                    if category:
                        mapping = ProjectBasicDataMapping(project_id=project.id, category_id=category_id)
                        db.add(mapping)
                except (ValueError, Exception) as e:
                    logger.warning(f"添加基础数据分类失败: {category_id_str}, {e!s}")

        db.flush()

        # 自动将创建者添加为项目经理
        if current_user.get("user_id") and current_user.get("user_id") != "anonymous":
            try:
                creator_id = UUID(current_user.get("user_id"))
                project_member = ProjectMember(
                    project_id=project.id,
                    user_id=creator_id,
                    role=ProjectMemberRole.MANAGER.value,
                    joined_at=date.today(),
                )
                db.add(project_member)
                db.flush()
            except Exception as e:
                logger.warning(f"添加项目创建者为成员失败: {e!s}")

        # 如果指定了manager_id，也将其添加为项目经理
        if manager_id and manager_id != creator_id:
            try:
                existing_manager = (
                    db.query(ProjectMember)
                    .filter(ProjectMember.project_id == project.id, ProjectMember.user_id == manager_id)
                    .first()
                )
                if not existing_manager:
                    manager_member = ProjectMember(
                        project_id=project.id,
                        user_id=manager_id,
                        role=ProjectMemberRole.MANAGER,
                        joined_at=date.today(),
                    )
                    db.add(manager_member)
                    db.flush()
            except Exception as e:
                logger.warning(f"添加项目经理为成员失败: {e!s}")

        # 记录审计日志
        await log_audit(
            db=db,
            user_id=current_user.get("user_id", "anonymous"),
            action="create",
            resource_type="project",
            resource_id=str(project.id),
            details={"project_code": project.project_code, "name": project.name},
        )

        db.commit()
        db.refresh(project)

        # 自动创建项目计划和阶段（从基础数据获取项目阶段分类）
        try:
            from database.src.models.basic_data_models import BasicDataCategory
            from database.src.models.project_models import ProjectPlan, ProjectPhase, ProjectTemplate

            # 获取所有启用的项目阶段分类（按code或name排序）
            phase_categories = (
                db.query(BasicDataCategory)
                .filter(
                    BasicDataCategory.category_type == "project_phase",
                    BasicDataCategory.is_active == True
                )
                .order_by(BasicDataCategory.code.asc(), BasicDataCategory.name.asc())
                .all()
            )

            if phase_categories:
                # 创建项目阶段
                for idx, category in enumerate(phase_categories):
                    # 检查阶段是否已存在
                    existing_phase = (
                        db.query(ProjectPhase)
                        .filter(
                            ProjectPhase.project_id == project.id,
                            ProjectPhase.category_id == category.id,
                        )
                        .first()
                    )

                    if not existing_phase:
                        phase = ProjectPhase(
                            project_id=project.id,
                            category_id=category.id,
                            name=category.name,
                            sequence=idx + 1,
                            description=f"从基础数据自动创建",
                        )
                        db.add(phase)

                db.flush()

                # 查找"标准信息化项目管理模板"或使用第一个启用的模板
                default_template = (
                    db.query(ProjectTemplate)
                    .filter(
                        ProjectTemplate.name.like('%标准信息化项目管理模板%'),
                        ProjectTemplate.is_active == True
                    )
                    .first()
                )

                if not default_template:
                    # 如果没有找到默认模板，使用第一个启用的模板
                    default_template = (
                        db.query(ProjectTemplate)
                        .filter(ProjectTemplate.is_active == True)
                        .first()
                    )

                # 创建项目计划
                if default_template:
                    plan = ProjectPlan(
                        project_id=project.id,
                        name=f"{project.name}项目计划",
                        description=f"基于模板'{default_template.name}'自动创建",
                        version="1.0",
                        template_id=default_template.id,
                        is_active=True,
                        is_baseline=False,
                    )
                    db.add(plan)
                    db.flush()

                    # 更新模板使用次数
                    default_template.usage_count = (default_template.usage_count or 0) + 1
                else:
                    # 如果没有模板，创建一个不带模板的计划
                    plan = ProjectPlan(
                        project_id=project.id,
                        name=f"{project.name}项目计划",
                        description="自动创建的项目计划",
                        version="1.0",
                        is_active=True,
                        is_baseline=False,
                    )
                    db.add(plan)

                db.commit()
                logger.info(f"项目 {project.id} 已自动创建计划和阶段")
        except Exception as e:
            logger.warning(f"为项目 {project.id} 自动创建计划和阶段失败: {e!s}", exc_info=True)
            # 不影响项目创建，只记录警告

        return ProjectResponse(
            id=str(project.id),
            project_code=project.project_code,
            name=project.name,
            description=project.description,
            status=(project.status.value if hasattr(project.status, "value") else str(project.status)),
            priority=project.priority,
            start_date=project.start_date.isoformat() if project.start_date else None,
            end_date=project.end_date.isoformat() if project.end_date else None,
            progress_percent=project.progress_percent or 0.0,
            health_score=project.health_score or 0.0,
            created_at=(project.created_at.isoformat() if project.created_at else datetime.utcnow().isoformat()),
            updated_at=(project.updated_at.isoformat() if project.updated_at else datetime.utcnow().isoformat()),
            requires_weekly_report=(
                getattr(project, "requires_weekly_report", False)
                if hasattr(project, "requires_weekly_report")
                else False
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建项目失败: {e!s}")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.UPDATE)),
):
    """更新项目（需要项目编辑权限）"""
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 更新字段
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.status is not None:
            with contextlib.suppress(ValueError):
                project.status = ProjectStatus(project_data.status.lower())
        if project_data.priority is not None:
            project.priority = project_data.priority
        if project_data.manager_id is not None:
            with contextlib.suppress(ValueError):
                project.manager_id = UUID(project_data.manager_id) if project_data.manager_id else None
        if project_data.reporter_id is not None:
            with contextlib.suppress(ValueError):
                project.reporter_id = UUID(project_data.reporter_id) if project_data.reporter_id else None
        if project_data.start_date is not None:
            try:
                project.start_date = datetime.fromisoformat(project_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                with contextlib.suppress(ValueError, AttributeError):
                    project.start_date = datetime.strptime(project_data.start_date, "%Y-%m-%d").date()
        if project_data.end_date is not None:
            try:
                project.end_date = datetime.fromisoformat(project_data.end_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                with contextlib.suppress(ValueError, AttributeError):
                    project.end_date = datetime.strptime(project_data.end_date, "%Y-%m-%d").date()
        if project_data.actual_start_date is not None:
            try:
                project.actual_start_date = datetime.fromisoformat(
                    project_data.actual_start_date.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                with contextlib.suppress(ValueError, AttributeError):
                    project.actual_start_date = datetime.strptime(project_data.actual_start_date, "%Y-%m-%d").date()
        if project_data.actual_end_date is not None:
            try:
                project.actual_end_date = datetime.fromisoformat(
                    project_data.actual_end_date.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                with contextlib.suppress(ValueError, AttributeError):
                    project.actual_end_date = datetime.strptime(project_data.actual_end_date, "%Y-%m-%d").date()
        if project_data.budget is not None:
            project.budget = project_data.budget
        if project_data.actual_cost is not None:
            project.actual_cost = project_data.actual_cost
        if project_data.progress_percent is not None:
            project.progress_percent = project_data.progress_percent
        if project_data.health_score is not None:
            project.health_score = project_data.health_score
        if project_data.milestone_implementation_start is not None:
            try:
                project.milestone_implementation_start = (
                    datetime.fromisoformat(project_data.milestone_implementation_start.replace("Z", "+00:00")).date()
                    if project_data.milestone_implementation_start
                    else None
                )
            except (ValueError, AttributeError):
                try:
                    project.milestone_implementation_start = (
                        datetime.strptime(project_data.milestone_implementation_start, "%Y-%m-%d").date()
                        if project_data.milestone_implementation_start
                        else None
                    )
                except (ValueError, AttributeError):
                    project.milestone_implementation_start = None
        if project_data.milestone_solution_confirmation is not None:
            try:
                project.milestone_solution_confirmation = (
                    datetime.fromisoformat(project_data.milestone_solution_confirmation.replace("Z", "+00:00")).date()
                    if project_data.milestone_solution_confirmation
                    else None
                )
            except (ValueError, AttributeError):
                try:
                    project.milestone_solution_confirmation = (
                        datetime.strptime(project_data.milestone_solution_confirmation, "%Y-%m-%d").date()
                        if project_data.milestone_solution_confirmation
                        else None
                    )
                except (ValueError, AttributeError):
                    project.milestone_solution_confirmation = None
        if project_data.milestone_delivery_online is not None:
            try:
                project.milestone_delivery_online = (
                    datetime.fromisoformat(project_data.milestone_delivery_online.replace("Z", "+00:00")).date()
                    if project_data.milestone_delivery_online
                    else None
                )
            except (ValueError, AttributeError):
                try:
                    project.milestone_delivery_online = (
                        datetime.strptime(project_data.milestone_delivery_online, "%Y-%m-%d").date()
                        if project_data.milestone_delivery_online
                        else None
                    )
                except (ValueError, AttributeError):
                    project.milestone_delivery_online = None
        if project_data.milestone_project_acceptance is not None:
            try:
                project.milestone_project_acceptance = (
                    datetime.fromisoformat(project_data.milestone_project_acceptance.replace("Z", "+00:00")).date()
                    if project_data.milestone_project_acceptance
                    else None
                )
            except (ValueError, AttributeError):
                try:
                    project.milestone_project_acceptance = (
                        datetime.strptime(project_data.milestone_project_acceptance, "%Y-%m-%d").date()
                        if project_data.milestone_project_acceptance
                        else None
                    )
                except (ValueError, AttributeError):
                    project.milestone_project_acceptance = None
        if project_data.requires_weekly_report is not None:
            project.requires_weekly_report = project_data.requires_weekly_report

        project.updated_at = datetime.utcnow()

        # 记录审计日志
        await log_audit(
            db=db,
            user_id=current_user.get("user_id", "anonymous"),
            action="update",
            resource_type="project",
            resource_id=str(project.id),
            details={"changes": project_data.model_dump(exclude_unset=True)},
        )

        db.commit()
        db.refresh(project)

        # 查询项目关联的基础数据分类
        from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
        from database.src.models.user_models import User

        mappings = db.query(ProjectBasicDataMapping).filter(ProjectBasicDataMapping.project_id == project.id).all()

        basic_data_categories = []
        for mapping in mappings:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == mapping.category_id).first()
            if category:
                basic_data_categories.append(
                    {
                        "id": str(category.id),
                        "category_type": category.category_type,
                        "code": category.code,
                        "name": category.name,
                        "description": category.description,
                    }
                )

        # 查询填报人信息
        reporter_name = None
        if project.reporter_id:
            reporter = db.query(User).filter(User.id == project.reporter_id).first()
            if reporter:
                reporter_name = reporter.full_name or reporter.username

        # 查询项目经理信息
        manager_name = None
        if project.manager_id:
            manager = db.query(User).filter(User.id == project.manager_id).first()
            if manager:
                manager_name = manager.full_name or manager.username

        return ProjectResponse(
            id=str(project.id),
            project_code=project.project_code,
            name=project.name,
            description=project.description,
            status=(project.status.value if hasattr(project.status, "value") else str(project.status)),
            priority=project.priority,
            start_date=project.start_date.isoformat() if project.start_date else None,
            end_date=project.end_date.isoformat() if project.end_date else None,
            progress_percent=project.progress_percent or 0.0,
            health_score=project.health_score or 0.0,
            created_at=(project.created_at.isoformat() if project.created_at else datetime.utcnow().isoformat()),
            updated_at=(project.updated_at.isoformat() if project.updated_at else datetime.utcnow().isoformat()),
            basic_data_categories=basic_data_categories,
            reporter_id=str(project.reporter_id) if project.reporter_id else None,
            reporter_name=reporter_name,
            manager_id=str(project.manager_id) if project.manager_id else None,
            manager_name=manager_name,
            milestone_implementation_start=(
                getattr(project, "milestone_implementation_start", None).isoformat()
                if getattr(project, "milestone_implementation_start", None)
                else None
            ),
            milestone_solution_confirmation=(
                getattr(project, "milestone_solution_confirmation", None).isoformat()
                if getattr(project, "milestone_solution_confirmation", None)
                else None
            ),
            milestone_delivery_online=(
                getattr(project, "milestone_delivery_online", None).isoformat()
                if getattr(project, "milestone_delivery_online", None)
                else None
            ),
            milestone_project_acceptance=(
                getattr(project, "milestone_project_acceptance", None).isoformat()
                if getattr(project, "milestone_project_acceptance", None)
                else None
            ),
            requires_weekly_report=(
                getattr(project, "requires_weekly_report", False)
                if hasattr(project, "requires_weekly_report")
                else False
            ),
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    except Exception as e:
        logger.error(f"更新项目失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新项目失败: {e!s}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_project_permission(ProjectPermission.DELETE)),
):
    """删除项目（需要项目删除权限）"""
    try:
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        project_id_str = str(project.id)
        project_code = project.project_code
        project_name = project.name

        # 记录审计日志（在删除前）
        await log_audit(
            db=db,
            user_id=current_user.get("user_id", "anonymous"),
            action="delete",
            resource_type="project",
            resource_id=project_id_str,
            details={"project_code": project_code, "name": project_name},
        )

        db.delete(project)
        db.commit()

        return {
            "success": True,
            "message": f"项目 {project_name} 已删除",
            "project_id": project_id_str,
        }

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID")
    except Exception as e:
        logger.error(f"删除项目失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {e!s}")


@router.post("/import/excel")
async def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """导入Excel文件创建项目"""
    try:
        # 验证文件类型
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="只支持Excel文件 (.xlsx, .xls)")

        # 读取文件内容
        file_content = await file.read()

        # 解析Excel
        parser = ExcelParser()
        projects_data = parser.parse_excel(file_content)

        if not projects_data:
            raise HTTPException(status_code=400, detail="Excel文件中未找到项目数据")

        # 创建项目
        created_count = 0
        created_projects = []

        for project_data in projects_data:
            try:
                # 检查项目编码是否已存在
                existing = db.query(Project).filter(Project.project_code == project_data.get("project_code")).first()

                if existing:
                    logger.info(f"项目编码 {project_data.get('project_code')} 已存在，跳过")
                    continue

                # 创建新项目
                project = Project(
                    project_code=project_data.get("project_code", ""),
                    name=project_data.get("name", ""),
                    description=project_data.get("description"),
                    status=(
                        ProjectStatus.ACTIVE if project_data.get("status") != "completed" else ProjectStatus.COMPLETED
                    ),
                    priority=project_data.get("priority", "medium"),
                    start_date=project_data.get("start_date"),
                    end_date=project_data.get("end_date"),
                    progress_percent=project_data.get("progress_percent", 0.0),
                    health_score=project_data.get("health_score", 0.0),
                )

                db.add(project)
                db.flush()

                created_count += 1
                created_projects.append(
                    {
                        "id": str(project.id),
                        "name": project.name,
                        "project_code": project.project_code,
                    }
                )

            except Exception as e:
                logger.error(f"创建项目失败: {e!s}", exc_info=True)
                continue

        db.commit()

        # 记录审计日志
        await log_audit(
            db=db,
            user_id=current_user.get("user_id", "anonymous"),
            action="create",
            resource_type="project",
            resource_id="batch_import",
            details={
                "total_found": len(projects_data),
                "created": created_count,
                "filename": file.filename,
            },
        )

        return {
            "success": True,
            "total_found": len(projects_data),
            "created": created_count,
            "projects": created_projects,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel导入失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Excel导入失败: {e!s}")


@router.post("/batch-create-plans", response_model=dict)
async def batch_create_plans_for_projects(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """为所有现有项目批量创建计划和阶段（管理员功能）"""
    try:
        from database.src.models.basic_data_models import BasicDataCategory
        from database.src.models.project_models import ProjectPlan, ProjectPhase, ProjectTemplate

        # 检查是否为管理员
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        # 获取所有项目
        all_projects = db.query(Project).all()

        # 获取所有启用的项目阶段分类
        phase_categories = (
            db.query(BasicDataCategory)
            .filter(
                BasicDataCategory.category_type == "project_phase",
                BasicDataCategory.is_active == True
            )
            .order_by(BasicDataCategory.code.asc(), BasicDataCategory.name.asc())
            .all()
        )

        if not phase_categories:
            return {
                "message": "未找到项目阶段分类，请先在基础数据中创建项目阶段分类",
                "processed": 0,
                "created_plans": 0,
                "created_phases": 0,
            }

        # 查找默认模板
        default_template = (
            db.query(ProjectTemplate)
            .filter(
                ProjectTemplate.name.like('%标准信息化项目管理模板%'),
                ProjectTemplate.is_active == True
            )
            .first()
        )

        if not default_template:
            default_template = (
                db.query(ProjectTemplate)
                .filter(ProjectTemplate.is_active == True)
                .first()
            )

        created_plans = 0
        created_phases = 0
        processed = 0

        for project in all_projects:
            try:
                processed += 1

                # 检查是否已有计划
                existing_plan = (
                    db.query(ProjectPlan)
                    .filter(ProjectPlan.project_id == project.id, ProjectPlan.is_active == True)
                    .first()
                )

                if existing_plan:
                    logger.info(f"项目 {project.id} ({project.name}) 已有计划，跳过")
                    continue

                # 创建项目阶段
                phases_created = 0
                for idx, category in enumerate(phase_categories):
                    existing_phase = (
                        db.query(ProjectPhase)
                        .filter(
                            ProjectPhase.project_id == project.id,
                            ProjectPhase.category_id == category.id,
                        )
                        .first()
                    )

                    if not existing_phase:
                        phase = ProjectPhase(
                            project_id=project.id,
                            category_id=category.id,
                            name=category.name,
                            sequence=idx + 1,
                            description=f"从基础数据自动创建",
                        )
                        db.add(phase)
                        phases_created += 1

                db.flush()

                # 创建项目计划
                if default_template:
                    plan = ProjectPlan(
                        project_id=project.id,
                        name=f"{project.name}项目计划",
                        description=f"基于模板'{default_template.name}'自动创建",
                        version="1.0",
                        template_id=default_template.id,
                        is_active=True,
                        is_baseline=False,
                    )
                    default_template.usage_count = (default_template.usage_count or 0) + 1
                else:
                    plan = ProjectPlan(
                        project_id=project.id,
                        name=f"{project.name}项目计划",
                        description="自动创建的项目计划",
                        version="1.0",
                        is_active=True,
                        is_baseline=False,
                    )

                db.add(plan)
                db.flush()

                created_plans += 1
                created_phases += phases_created

                # 每10个项目提交一次，避免事务过大
                if processed % 10 == 0:
                    db.commit()
                    logger.info(f"已处理 {processed} 个项目")

            except Exception as e:
                logger.error(f"为项目 {project.id} 创建计划和阶段失败: {e!s}", exc_info=True)
                db.rollback()
                continue

        # 最终提交
        db.commit()

        return {
            "message": "批量创建完成",
            "processed": processed,
            "created_plans": created_plans,
            "created_phases": created_phases,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量创建计划失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量创建计划失败: {e!s}")
