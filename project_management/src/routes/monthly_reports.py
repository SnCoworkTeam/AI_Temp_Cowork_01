"""
月报管理路由
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import MonthlyReport, Project, WeeklyReport
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission, get_user_projects
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class MonthlyReportResponse(BaseModel):
    """月报响应模型"""

    id: str
    project_id: str
    report_month: str
    project_name: str | None = None
    summary: str | None = None
    achievements: str | None = None
    challenges: str | None = None
    next_month_plan: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MonthlyReportListResponse(BaseModel):
    """月报列表响应"""

    total: int
    items: list[MonthlyReportResponse]


@router.get("", response_model=MonthlyReportListResponse)
async def list_monthly_reports(
    project_id: str | None = Query(None),
    year: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取月报列表（只返回用户有权限的项目月报）"""
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

        query = db.query(MonthlyReport)

        # 只查询用户有权限的项目月报
        # 如果 user_project_ids 是 None，表示管理员，不进行过滤
        if user_project_ids is not None:
            if user_project_ids:
                query = query.filter(MonthlyReport.project_id.in_(user_project_ids))
            else:
                # 用户没有任何项目权限，返回空列表
                return MonthlyReportListResponse(total=0, items=[])

        if project_id:
            try:
                project_uuid = UUID(project_id)
                # 如果不是管理员，检查用户是否有该项目的权限
                if not is_admin and user_project_ids is not None:
                    if project_uuid not in user_project_ids:
                        raise HTTPException(status_code=403, detail="没有权限访问该项目")
                query = query.filter(MonthlyReport.project_id == project_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        if year:
            try:
                year_int = int(year)
                query = query.filter(MonthlyReport.report_year == year_int)
            except (ValueError, AttributeError):
                pass

        total = query.count()
        monthly_reports = (
            query.order_by(MonthlyReport.report_year.desc(), MonthlyReport.report_month.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # 获取项目名称
        project_ids = {str(r.project_id) for r in monthly_reports}
        projects = {}
        if project_ids:
            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        # 转换为月报响应
        items = []
        for report in monthly_reports:
            report_month = f"{report.report_year}-{report.report_month:02d}"
            items.append(
                MonthlyReportResponse(
                    id=str(report.id),
                    project_id=str(report.project_id),
                    report_month=report_month,
                    project_name=projects.get(str(report.project_id)),
                    summary=report.summary,
                    achievements=report.achievements,
                    challenges=report.challenges,
                    next_month_plan=report.next_month_plan,
                    created_at=report.created_at.isoformat() if report.created_at else "",
                    updated_at=report.updated_at.isoformat() if report.updated_at else "",
                )
            )

        return MonthlyReportListResponse(total=total, items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取月报列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取月报列表失败: {e!s}")


class MonthlyReportCreate(BaseModel):
    """月报创建模型（基于周报聚合，也可以独立创建）"""

    project_id: str
    report_month: str  # YYYY-MM格式
    summary: str | None = None
    achievements: str | None = None
    challenges: str | None = None
    next_month_plan: str | None = None


@router.post("", response_model=MonthlyReportResponse)
async def create_monthly_report(
    report_data: MonthlyReportCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """创建月报（需要项目CREATE权限）"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 验证项目是否存在
        try:
            project_id = UUID(report_data.project_id)
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
            raise HTTPException(status_code=403, detail="没有权限在该项目中创建月报")

        # 解析月份
        try:
            year, month = map(int, report_data.report_month.split("-"))
            if month < 1 or month > 12:
                msg = "月份必须在1-12之间"
                raise ValueError(msg)
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="无效的月份格式，应为YYYY-MM")

        # 检查是否已存在该月的月报
        existing = (
            db.query(MonthlyReport)
            .filter(
                MonthlyReport.project_id == project_id,
                MonthlyReport.report_year == year,
                MonthlyReport.report_month == month,
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail=f"该项目{year}年{month}月的月报已存在")

        # 可选：从周报聚合数据（如果未提供独立内容）
        if not report_data.achievements or not report_data.challenges:
            from sqlalchemy import extract

            weekly_reports = (
                db.query(WeeklyReport)
                .filter(
                    WeeklyReport.project_id == project_id,
                    extract("year", WeeklyReport.report_date) == year,
                    extract("month", WeeklyReport.report_date) == month,
                )
                .all()
            )

            achievements_list = []
            challenges_list = []
            next_plans_list = []

            for wr in weekly_reports:
                if wr.content_achievement:
                    achievements_list.append(wr.content_achievement)
                if wr.issues_risks:
                    challenges_list.append(wr.issues_risks)
                if wr.next_week_plan:
                    next_plans_list.append(wr.next_week_plan)
        else:
            achievements_list = []
            challenges_list = []
            next_plans_list = []

        # 创建月报
        monthly_report = MonthlyReport(
            project_id=project_id,
            report_year=year,
            report_month=month,
            summary=report_data.summary or f"{year}年{month}月项目进展总结",
            achievements=report_data.achievements or "\n".join(achievements_list[:3]) or "本月完成相关工作",
            challenges=report_data.challenges or "\n".join(challenges_list[:2]) or "无重大挑战",
            next_month_plan=report_data.next_month_plan or "\n".join(next_plans_list[:2]) or "继续推进项目",
            progress_percent=0.0,
        )

        db.add(monthly_report)
        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="monthly_report",
                resource_id=str(monthly_report.id),
                details={"project_id": str(project_id), "report_month": report_data.report_month},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        report_month_str = f"{year}-{month:02d}"
        return MonthlyReportResponse(
            id=str(monthly_report.id),
            project_id=str(monthly_report.project_id),
            report_month=report_month_str,
            project_name=project.name,
            summary=monthly_report.summary,
            achievements=monthly_report.achievements,
            challenges=monthly_report.challenges,
            next_month_plan=monthly_report.next_month_plan,
            created_at=monthly_report.created_at.isoformat() if monthly_report.created_at else "",
            updated_at=monthly_report.updated_at.isoformat() if monthly_report.updated_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建月报失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建月报失败: {e!s}")


@router.get("/{report_id}", response_model=MonthlyReportResponse)
async def get_monthly_report(report_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取月报详情（需要项目READ权限）"""
    try:
        from ..middleware.project_permissions import ProjectPermission, check_project_permission

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            report_uuid = UUID(report_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的月报ID或用户ID")

        report = db.query(MonthlyReport).filter(MonthlyReport.id == report_uuid).first()
        if not report:
            raise HTTPException(status_code=404, detail="月报不存在")

        # 检查用户是否有该项目的READ权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            report.project_id, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限查看该月报")

        project = db.query(Project).filter(Project.id == report.project_id).first()
        report_month_str = f"{report.report_year}-{report.report_month:02d}"

        return MonthlyReportResponse(
            id=str(report.id),
            project_id=str(report.project_id),
            report_month=report_month_str,
            project_name=project.name if project else None,
            summary=report.summary,
            achievements=report.achievements,
            challenges=report.challenges,
            next_month_plan=report.next_month_plan,
            created_at=report.created_at.isoformat() if report.created_at else "",
            updated_at=report.updated_at.isoformat() if report.updated_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取月报详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取月报详情失败: {e!s}")


class MonthlyReportUpdate(BaseModel):
    """月报更新模型"""

    summary: str | None = None
    achievements: str | None = None
    challenges: str | None = None
    next_month_plan: str | None = None


@router.put("/{report_id}", response_model=MonthlyReportResponse)
async def update_monthly_report(
    report_id: str,
    report_data: MonthlyReportUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新月报（使用独立的月报表）"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的月报ID")

        report = db.query(MonthlyReport).filter(MonthlyReport.id == report_uuid).first()
        if not report:
            raise HTTPException(status_code=404, detail="月报不存在")

        # 更新字段
        if report_data.summary is not None:
            report.summary = report_data.summary
        if report_data.achievements is not None:
            report.achievements = report_data.achievements
        if report_data.challenges is not None:
            report.challenges = report_data.challenges
        if report_data.next_month_plan is not None:
            report.next_month_plan = report_data.next_month_plan

        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="monthly_report",
                resource_id=str(report.id),
                details={"report_month": f"{report.report_year}-{report.report_month:02d}"},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        project = db.query(Project).filter(Project.id == report.project_id).first()
        report_month_str = f"{report.report_year}-{report.report_month:02d}"

        return MonthlyReportResponse(
            id=str(report.id),
            project_id=str(report.project_id),
            report_month=report_month_str,
            project_name=project.name if project else None,
            summary=report.summary,
            achievements=report.achievements,
            challenges=report.challenges,
            next_month_plan=report.next_month_plan,
            created_at=report.created_at.isoformat() if report.created_at else "",
            updated_at=report.updated_at.isoformat() if report.updated_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新月报失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新月报失败: {e!s}")


@router.delete("/{report_id}")
async def delete_monthly_report(
    report_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """删除月报（使用独立的月报表）"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的月报ID")

        report = db.query(MonthlyReport).filter(MonthlyReport.id == report_uuid).first()
        if not report:
            raise HTTPException(status_code=404, detail="月报不存在")

        report_month_str = f"{report.report_year}-{report.report_month:02d}"

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="monthly_report",
                resource_id=str(report.id),
                details={"report_month": report_month_str},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(report)
        db.commit()

        return {"message": "月报已删除", "id": report_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除月报失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除月报失败: {e!s}")
