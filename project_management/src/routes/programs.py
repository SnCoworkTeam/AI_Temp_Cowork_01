"""
项目群管理路由
"""

import contextlib
import logging
from datetime import datetime
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Program, ProgramStatus, Project
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class ProgramResponse(BaseModel):
    """项目群响应模型"""

    id: str
    program_code: str
    name: str
    description: str | None = None
    status: str
    manager_id: str | None = None
    manager_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    budget: float | None = None
    actual_cost: float | None = None
    progress_percent: float = 0.0
    health_score: float = 0.0
    category_id: str | None = None
    category_name: str | None = None
    project_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProgramListResponse(BaseModel):
    """项目群列表响应"""

    total: int
    items: list[ProgramResponse]


class ProgramCreate(BaseModel):
    """创建项目群请求模型"""

    program_code: str | None = None
    name: str
    description: str | None = None
    status: str | None = "planning"
    manager_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    budget: float | None = None
    category_id: str | None = None


class ProgramUpdate(BaseModel):
    """更新项目群请求模型"""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    manager_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    actual_start_date: str | None = None
    actual_end_date: str | None = None
    budget: float | None = None
    actual_cost: float | None = None
    progress_percent: float | None = None
    health_score: float | None = None
    category_id: str | None = None


@router.get("", response_model=ProgramListResponse)
async def list_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取项目群列表"""
    try:
        query = db.query(Program)

        if status:
            try:
                program_status = ProgramStatus(status.lower())
                query = query.filter(Program.status == program_status)
            except ValueError:
                pass

        total = query.count()
        programs = query.order_by(Program.created_at.desc()).offset(skip).limit(limit).all()

        # 获取项目群经理信息和项目数量
        from database.src.models.basic_data_models import BasicDataCategory
        from database.src.models.user_models import User

        items = []
        for p in programs:
            manager_name = None
            if p.manager_id:
                manager = db.query(User).filter(User.id == p.manager_id).first()
                if manager:
                    manager_name = manager.full_name or manager.username

            category_name = None
            if p.category_id:
                category = db.query(BasicDataCategory).filter(BasicDataCategory.id == p.category_id).first()
                if category:
                    category_name = category.name

            # 统计项目数量
            project_count = db.query(Project).filter(Project.program_id == p.id).count()

            items.append(
                ProgramResponse(
                    id=str(p.id),
                    program_code=p.program_code,
                    name=p.name,
                    description=p.description,
                    status=p.status.value if hasattr(p.status, "value") else str(p.status),
                    manager_id=str(p.manager_id) if p.manager_id else None,
                    manager_name=manager_name,
                    start_date=p.start_date.isoformat() if p.start_date else None,
                    end_date=p.end_date.isoformat() if p.end_date else None,
                    actual_start_date=p.actual_start_date.isoformat() if p.actual_start_date else None,
                    actual_end_date=p.actual_end_date.isoformat() if p.actual_end_date else None,
                    budget=p.budget,
                    actual_cost=p.actual_cost,
                    progress_percent=p.progress_percent or 0.0,
                    health_score=p.health_score or 0.0,
                    category_id=str(p.category_id) if p.category_id else None,
                    category_name=category_name,
                    project_count=project_count,
                    created_at=p.created_at.isoformat() if p.created_at else "",
                    updated_at=p.updated_at.isoformat() if p.updated_at else "",
                )
            )

        return ProgramListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"获取项目群列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目群列表失败: {e!s}")


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_program(program_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取项目群详情"""
    try:
        program = db.query(Program).filter(Program.id == UUID(program_id)).first()
        if not program:
            raise HTTPException(status_code=404, detail="项目群不存在")

        from database.src.models.basic_data_models import BasicDataCategory
        from database.src.models.user_models import User

        manager_name = None
        if program.manager_id:
            manager = db.query(User).filter(User.id == program.manager_id).first()
            if manager:
                manager_name = manager.full_name or manager.username

        category_name = None
        if program.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == program.category_id).first()
            if category:
                category_name = category.name

        project_count = db.query(Project).filter(Project.program_id == program.id).count()

        return ProgramResponse(
            id=str(program.id),
            program_code=program.program_code,
            name=program.name,
            description=program.description,
            status=program.status.value if hasattr(program.status, "value") else str(program.status),
            manager_id=str(program.manager_id) if program.manager_id else None,
            manager_name=manager_name,
            start_date=program.start_date.isoformat() if program.start_date else None,
            end_date=program.end_date.isoformat() if program.end_date else None,
            actual_start_date=program.actual_start_date.isoformat() if program.actual_start_date else None,
            actual_end_date=program.actual_end_date.isoformat() if program.actual_end_date else None,
            budget=program.budget,
            actual_cost=program.actual_cost,
            progress_percent=program.progress_percent or 0.0,
            health_score=program.health_score or 0.0,
            category_id=str(program.category_id) if program.category_id else None,
            category_name=category_name,
            project_count=project_count,
            created_at=program.created_at.isoformat() if program.created_at else "",
            updated_at=program.updated_at.isoformat() if program.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目群详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目群详情失败: {e!s}")


@router.post("", response_model=ProgramResponse, status_code=201)
async def create_program(
    program_data: ProgramCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """创建项目群"""
    try:
        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 生成项目群编码
        program_code = program_data.program_code
        if not program_code:
            # 自动生成编码
            import random
            import string

            program_code = f"PRG{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

        # 检查编码是否已存在
        existing = db.query(Program).filter(Program.program_code == program_code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"项目群编码 {program_code} 已存在")

        # 解析状态
        status = ProgramStatus.PLANNING
        if program_data.status:
            try:
                status = ProgramStatus(program_data.status.lower())
            except ValueError:
                status = ProgramStatus.PLANNING

        # 解析日期
        start_date = None
        end_date = None
        if program_data.start_date:
            try:
                start_date = datetime.fromisoformat(program_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                start_date = datetime.strptime(program_data.start_date, "%Y-%m-%d").date()
        if program_data.end_date:
            try:
                end_date = datetime.fromisoformat(program_data.end_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                end_date = datetime.strptime(program_data.end_date, "%Y-%m-%d").date()

        # 解析manager_id和category_id
        manager_id = None
        if program_data.manager_id:
            with contextlib.suppress(ValueError):
                manager_id = UUID(program_data.manager_id)

        category_id = None
        if program_data.category_id:
            with contextlib.suppress(ValueError):
                category_id = UUID(program_data.category_id)

        # 创建项目群
        program = Program(
            program_code=program_code,
            name=program_data.name,
            description=program_data.description,
            status=status,
            manager_id=manager_id,
            start_date=start_date,
            end_date=end_date,
            budget=program_data.budget,
            category_id=category_id,
        )

        db.add(program)
        db.flush()

        # 记录审计日志
        try:
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="program",
                resource_id=str(program.id),
                details={"program_code": program_code, "name": program_data.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()
        db.refresh(program)

        # 返回响应
        from database.src.models.basic_data_models import BasicDataCategory
        from database.src.models.user_models import User

        manager_name = None
        if program.manager_id:
            manager = db.query(User).filter(User.id == program.manager_id).first()
            if manager:
                manager_name = manager.full_name or manager.username

        category_name = None
        if program.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == program.category_id).first()
            if category:
                category_name = category.name

        return ProgramResponse(
            id=str(program.id),
            program_code=program.program_code,
            name=program.name,
            description=program.description,
            status=program.status.value if hasattr(program.status, "value") else str(program.status),
            manager_id=str(program.manager_id) if program.manager_id else None,
            manager_name=manager_name,
            start_date=program.start_date.isoformat() if program.start_date else None,
            end_date=program.end_date.isoformat() if program.end_date else None,
            actual_start_date=program.actual_start_date.isoformat() if program.actual_start_date else None,
            actual_end_date=program.actual_end_date.isoformat() if program.actual_end_date else None,
            budget=program.budget,
            actual_cost=program.actual_cost,
            progress_percent=program.progress_percent or 0.0,
            health_score=program.health_score or 0.0,
            category_id=str(program.category_id) if program.category_id else None,
            category_name=category_name,
            project_count=0,
            created_at=program.created_at.isoformat() if program.created_at else "",
            updated_at=program.updated_at.isoformat() if program.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目群失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建项目群失败: {e!s}")


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: str,
    program_data: ProgramUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新项目群"""
    try:
        from database.src.models.system_models import AuditLog

        program = db.query(Program).filter(Program.id == UUID(program_id)).first()
        if not program:
            raise HTTPException(status_code=404, detail="项目群不存在")

        # 更新字段
        if program_data.name is not None:
            program.name = program_data.name
        if program_data.description is not None:
            program.description = program_data.description
        if program_data.status is not None:
            with contextlib.suppress(ValueError):
                program.status = ProgramStatus(program_data.status.lower())
        if program_data.manager_id is not None:
            with contextlib.suppress(ValueError):
                program.manager_id = UUID(program_data.manager_id) if program_data.manager_id else None
        if program_data.start_date is not None:
            try:
                program.start_date = datetime.fromisoformat(program_data.start_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                program.start_date = datetime.strptime(program_data.start_date, "%Y-%m-%d").date()
        if program_data.end_date is not None:
            try:
                program.end_date = datetime.fromisoformat(program_data.end_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                program.end_date = datetime.strptime(program_data.end_date, "%Y-%m-%d").date()
        if program_data.actual_start_date is not None:
            try:
                program.actual_start_date = datetime.fromisoformat(
                    program_data.actual_start_date.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                program.actual_start_date = datetime.strptime(program_data.actual_start_date, "%Y-%m-%d").date()
        if program_data.actual_end_date is not None:
            try:
                program.actual_end_date = datetime.fromisoformat(
                    program_data.actual_end_date.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                program.actual_end_date = datetime.strptime(program_data.actual_end_date, "%Y-%m-%d").date()
        if program_data.budget is not None:
            program.budget = program_data.budget
        if program_data.actual_cost is not None:
            program.actual_cost = program_data.actual_cost
        if program_data.progress_percent is not None:
            program.progress_percent = program_data.progress_percent
        if program_data.health_score is not None:
            program.health_score = program_data.health_score
        if program_data.category_id is not None:
            with contextlib.suppress(ValueError):
                program.category_id = UUID(program_data.category_id) if program_data.category_id else None

        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="program",
                resource_id=str(program.id),
                details={"name": program_data.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()
        db.refresh(program)

        # 返回响应
        from database.src.models.basic_data_models import BasicDataCategory
        from database.src.models.user_models import User

        manager_name = None
        if program.manager_id:
            manager = db.query(User).filter(User.id == program.manager_id).first()
            if manager:
                manager_name = manager.full_name or manager.username

        category_name = None
        if program.category_id:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == program.category_id).first()
            if category:
                category_name = category.name

        project_count = db.query(Project).filter(Project.program_id == program.id).count()

        return ProgramResponse(
            id=str(program.id),
            program_code=program.program_code,
            name=program.name,
            description=program.description,
            status=program.status.value if hasattr(program.status, "value") else str(program.status),
            manager_id=str(program.manager_id) if program.manager_id else None,
            manager_name=manager_name,
            start_date=program.start_date.isoformat() if program.start_date else None,
            end_date=program.end_date.isoformat() if program.end_date else None,
            actual_start_date=program.actual_start_date.isoformat() if program.actual_start_date else None,
            actual_end_date=program.actual_end_date.isoformat() if program.actual_end_date else None,
            budget=program.budget,
            actual_cost=program.actual_cost,
            progress_percent=program.progress_percent or 0.0,
            health_score=program.health_score or 0.0,
            category_id=str(program.category_id) if program.category_id else None,
            category_name=category_name,
            project_count=project_count,
            created_at=program.created_at.isoformat() if program.created_at else "",
            updated_at=program.updated_at.isoformat() if program.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目群失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新项目群失败: {e!s}")


@router.delete("/{program_id}")
async def delete_program(program_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """删除项目群"""
    try:
        from database.src.models.system_models import AuditLog

        program = db.query(Program).filter(Program.id == UUID(program_id)).first()
        if not program:
            raise HTTPException(status_code=404, detail="项目群不存在")

        program_name = program.name

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="program",
                resource_id=str(program.id),
                details={"name": program_name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(program)
        db.commit()

        return {"message": "项目群已删除", "id": program_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目群失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目群失败: {e!s}")


@router.get("/{program_id}/projects")
async def get_program_projects(
    program_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取项目群下的项目列表"""
    try:
        program = db.query(Program).filter(Program.id == UUID(program_id)).first()
        if not program:
            raise HTTPException(status_code=404, detail="项目群不存在")

        query = db.query(Project).filter(Project.program_id == UUID(program_id))
        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

        from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
        from database.src.models.user_models import User
        from project_management.src.routes.projects import ProjectResponse

        items = []
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

            # 查询填报人和项目经理信息
            reporter_name = None
            if p.reporter_id:
                reporter = db.query(User).filter(User.id == p.reporter_id).first()
                if reporter:
                    reporter_name = reporter.full_name or reporter.username

            manager_name = None
            if p.manager_id:
                manager = db.query(User).filter(User.id == p.manager_id).first()
                if manager:
                    manager_name = manager.full_name or manager.username

            items.append(
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
                    created_at=p.created_at.isoformat() if p.created_at else "",
                    updated_at=p.updated_at.isoformat() if p.updated_at else "",
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
                    requires_weekly_report=p.requires_weekly_report or False,
                )
            )

        return {"total": total, "items": items}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目群项目列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目群项目列表失败: {e!s}")
