"""
周报管理路由
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Project, WeeklyReport
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission, get_user_projects
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class WeeklyReportResponse(BaseModel):
    """周报响应模型"""

    id: str
    project_id: str
    week_number: int | None = None
    report_date: str
    content_plan: str | None = None
    content_achievement: str | None = None
    key_tasks_completed: list | None = None
    issues_risks: str | None = None
    next_week_plan: str | None = None
    project_name: str | None = None
    week_start_date: str | None = None
    week_end_date: str | None = None
    progress_summary: str | None = None
    completed_tasks: str | None = None
    ongoing_tasks: str | None = None
    planned_tasks: str | None = None
    risks: str | None = None
    progress_percent: float = 0.0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class WeeklyReportListResponse(BaseModel):
    """周报列表响应"""

    total: int
    items: list[WeeklyReportResponse]


@router.get("", response_model=WeeklyReportListResponse)
async def list_weekly_reports(
    project_id: str | None = Query(None),
    month: str | None = Query(None),
    week_start_date: str | None = Query(None),
    week_end_date: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取周报列表（只返回用户有权限的项目周报）"""
    try:
        from datetime import timedelta

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

        query = db.query(WeeklyReport)

        # 只查询用户有权限的项目周报
        # 如果 user_project_ids 是 None，表示管理员，不进行过滤
        if user_project_ids is not None:
            if user_project_ids:
                query = query.filter(WeeklyReport.project_id.in_(user_project_ids))
            else:
                # 用户没有任何项目权限，返回空列表
                return WeeklyReportListResponse(total=0, items=[])

        if project_id:
            try:
                project_uuid = UUID(project_id)
                # 如果不是管理员，检查用户是否有该项目的权限
                if not is_admin and user_project_ids is not None:
                    if project_uuid not in user_project_ids:
                        raise HTTPException(status_code=403, detail="没有权限访问该项目")
                query = query.filter(WeeklyReport.project_id == project_uuid)
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        if month:
            try:
                # month格式: YYYY-MM
                year, month_num = map(int, month.split("-"))
                query = query.filter(
                    db.extract("year", WeeklyReport.report_date) == year,
                    db.extract("month", WeeklyReport.report_date) == month_num,
                )
            except (ValueError, AttributeError):
                pass

        # 支持按周的开始和结束日期过滤
        if week_start_date:
            try:
                from datetime import datetime
                start_date = datetime.fromisoformat(week_start_date.replace("Z", "+00:00")).date()
                query = query.filter(WeeklyReport.report_date >= start_date)
            except (ValueError, AttributeError):
                pass

        if week_end_date:
            try:
                from datetime import datetime
                end_date = datetime.fromisoformat(week_end_date.replace("Z", "+00:00")).date()
                query = query.filter(WeeklyReport.report_date <= end_date)
            except (ValueError, AttributeError):
                pass

        total = query.count()
        reports = query.order_by(WeeklyReport.report_date.desc()).offset(skip).limit(limit).all()

        # 获取项目名称
        project_ids = {str(r.project_id) for r in reports}
        projects = {}
        if project_ids:
            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        items = []
        for report in reports:
            # 计算周的开始和结束日期
            week_start = None
            week_end = None
            if report.report_date:
                # 简单计算：报告日期所在周
                days_since_monday = report.report_date.weekday()
                from datetime import timedelta

                week_start = report.report_date - timedelta(days=days_since_monday)
                week_end = week_start + timedelta(days=6)

            items.append(
                WeeklyReportResponse(
                    id=str(report.id),
                    project_id=str(report.project_id),
                    week_number=report.week_number,
                    report_date=report.report_date.isoformat() if report.report_date else "",
                    content_plan=report.content_plan,
                    content_achievement=report.content_achievement,
                    key_tasks_completed=report.key_tasks_completed if report.key_tasks_completed else [],
                    issues_risks=report.issues_risks,
                    next_week_plan=report.next_week_plan,
                    project_name=projects.get(str(report.project_id)),
                    week_start_date=week_start.isoformat() if week_start else None,
                    week_end_date=week_end.isoformat() if week_end else None,
                    progress_summary=report.content_achievement or report.content_plan,
                    completed_tasks=report.content_achievement,
                    ongoing_tasks=report.content_plan,
                    planned_tasks=report.next_week_plan,
                    risks=report.issues_risks,
                    progress_percent=0.0,  # TODO: 从项目进度计算
                    created_at=report.created_at.isoformat() if report.created_at else "",
                    updated_at=report.updated_at.isoformat() if report.updated_at else "",
                )
            )

        return WeeklyReportListResponse(total=total, items=items)
    except HTTPException as e:
        # 确保 HTTPException 直接抛出，不被包装
        raise
    except Exception as e:
        # 检查是否是 HTTPException 的字符串表示
        error_str = str(e)
        if "403" in error_str and "没有权限" in error_str:
            # 如果错误信息包含 403 权限错误，直接抛出 403
            raise HTTPException(status_code=403, detail="没有权限访问该项目")
        logger.error(f"获取周报列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取周报列表失败: {e!s}")


class WeeklyReportCreate(BaseModel):
    """周报创建模型"""

    project_id: str
    week_number: int | None = None
    report_date: str
    content_plan: str | None = None
    content_achievement: str | None = None
    key_tasks_completed: list | None = None
    issues_risks: str | None = None
    next_week_plan: str | None = None


@router.post("", response_model=WeeklyReportResponse)
async def create_weekly_report(
    report_data: WeeklyReportCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """创建周报（需要项目CREATE权限）"""
    try:
        from datetime import datetime

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
            raise HTTPException(status_code=403, detail="没有权限在该项目中创建周报")

        # 解析报告日期
        try:
            report_date = datetime.fromisoformat(report_data.report_date.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            report_date = datetime.strptime(report_data.report_date, "%Y-%m-%d").date()

        # 创建周报
        weekly_report = WeeklyReport(
            project_id=project_id,
            week_number=report_data.week_number,
            report_date=report_date,
            content_plan=report_data.content_plan,
            content_achievement=report_data.content_achievement,
            key_tasks_completed=report_data.key_tasks_completed or [],
            issues_risks=report_data.issues_risks,
            next_week_plan=report_data.next_week_plan,
        )

        db.add(weekly_report)
        db.flush()

        # 记录审计日志
        from datetime import datetime as dt

        from database.src.models.system_models import AuditLog

        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="weekly_report",
                resource_id=str(weekly_report.id),
                details={"project_id": str(project_id), "report_date": report_data.report_date},
                timestamp=dt.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        # 计算周的开始和结束日期
        from datetime import timedelta

        days_since_monday = report_date.weekday()
        week_start = report_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)

        return WeeklyReportResponse(
            id=str(weekly_report.id),
            project_id=str(weekly_report.project_id),
            week_number=weekly_report.week_number,
            report_date=weekly_report.report_date.isoformat() if weekly_report.report_date else "",
            content_plan=weekly_report.content_plan,
            content_achievement=weekly_report.content_achievement,
            key_tasks_completed=weekly_report.key_tasks_completed if weekly_report.key_tasks_completed else [],
            issues_risks=weekly_report.issues_risks,
            next_week_plan=weekly_report.next_week_plan,
            project_name=project.name,
            week_start_date=week_start.isoformat() if week_start else None,
            week_end_date=week_end.isoformat() if week_end else None,
            progress_summary=weekly_report.content_achievement or weekly_report.content_plan,
            completed_tasks=weekly_report.content_achievement,
            ongoing_tasks=weekly_report.content_plan,
            planned_tasks=weekly_report.next_week_plan,
            risks=weekly_report.issues_risks,
            progress_percent=0.0,
            created_at=weekly_report.created_at.isoformat() if weekly_report.created_at else "",
            updated_at=weekly_report.updated_at.isoformat() if weekly_report.updated_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建周报失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建周报失败: {e!s}")


@router.get("/{report_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(report_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取周报详情（需要项目READ权限）"""
    try:
        from datetime import timedelta

        from database.src.models.project_models import Project

        from ..middleware.project_permissions import ProjectPermission, check_project_permission

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            report_uuid = UUID(report_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的周报ID或用户ID")

        report = db.query(WeeklyReport).filter(WeeklyReport.id == report_uuid).first()
        if not report:
            raise HTTPException(status_code=404, detail="周报不存在")

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
            raise HTTPException(status_code=403, detail="没有权限查看该周报")

        project = db.query(Project).filter(Project.id == report.project_id).first()

        # 计算周的开始和结束日期
        week_start = None
        week_end = None
        if report.report_date:
            days_since_monday = report.report_date.weekday()
            week_start = report.report_date - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)

        return WeeklyReportResponse(
            id=str(report.id),
            project_id=str(report.project_id),
            week_number=report.week_number,
            report_date=report.report_date.isoformat() if report.report_date else "",
            content_plan=report.content_plan,
            content_achievement=report.content_achievement,
            key_tasks_completed=report.key_tasks_completed if report.key_tasks_completed else [],
            issues_risks=report.issues_risks,
            next_week_plan=report.next_week_plan,
            project_name=project.name if project else None,
            week_start_date=week_start.isoformat() if week_start else None,
            week_end_date=week_end.isoformat() if week_end else None,
            progress_summary=report.content_achievement or report.content_plan,
            completed_tasks=report.content_achievement,
            ongoing_tasks=report.content_plan,
            planned_tasks=report.next_week_plan,
            risks=report.issues_risks,
            progress_percent=0.0,
            created_at=report.created_at.isoformat() if report.created_at else "",
            updated_at=report.updated_at.isoformat() if report.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取周报详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取周报详情失败: {e!s}")


class WeeklyReportUpdate(BaseModel):
    """周报更新模型"""

    report_date: str | None = None
    week_number: int | None = None
    content_plan: str | None = None
    content_achievement: str | None = None
    key_tasks_completed: list | None = None
    issues_risks: str | None = None
    next_week_plan: str | None = None


@router.put("/{report_id}", response_model=WeeklyReportResponse)
async def update_weekly_report(
    report_id: str,
    report_data: WeeklyReportUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新周报"""
    try:
        from datetime import datetime, timedelta

        from database.src.models.project_models import Project
        from database.src.models.system_models import AuditLog

        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的周报ID")

        report = db.query(WeeklyReport).filter(WeeklyReport.id == report_uuid).first()
        if not report:
            raise HTTPException(status_code=404, detail="周报不存在")

        # 更新字段
        if report_data.report_date is not None:
            try:
                report.report_date = datetime.fromisoformat(report_data.report_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                report.report_date = datetime.strptime(report_data.report_date, "%Y-%m-%d").date()
        if report_data.week_number is not None:
            report.week_number = report_data.week_number
        if report_data.content_plan is not None:
            report.content_plan = report_data.content_plan
        if report_data.content_achievement is not None:
            report.content_achievement = report_data.content_achievement
        if report_data.key_tasks_completed is not None:
            report.key_tasks_completed = report_data.key_tasks_completed
        if report_data.issues_risks is not None:
            report.issues_risks = report_data.issues_risks
        if report_data.next_week_plan is not None:
            report.next_week_plan = report_data.next_week_plan

        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="weekly_report",
                resource_id=str(report.id),
                details={"report_date": report_data.report_date},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        project = db.query(Project).filter(Project.id == report.project_id).first()

        # 计算周的开始和结束日期
        week_start = None
        week_end = None
        if report.report_date:
            days_since_monday = report.report_date.weekday()
            week_start = report.report_date - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)

        return WeeklyReportResponse(
            id=str(report.id),
            project_id=str(report.project_id),
            week_number=report.week_number,
            report_date=report.report_date.isoformat() if report.report_date else "",
            content_plan=report.content_plan,
            content_achievement=report.content_achievement,
            key_tasks_completed=report.key_tasks_completed if report.key_tasks_completed else [],
            issues_risks=report.issues_risks,
            next_week_plan=report.next_week_plan,
            project_name=project.name if project else None,
            week_start_date=week_start.isoformat() if week_start else None,
            week_end_date=week_end.isoformat() if week_end else None,
            progress_summary=report.content_achievement or report.content_plan,
            completed_tasks=report.content_achievement,
            ongoing_tasks=report.content_plan,
            planned_tasks=report.next_week_plan,
            risks=report.issues_risks,
            progress_percent=0.0,
            created_at=report.created_at.isoformat() if report.created_at else "",
            updated_at=report.updated_at.isoformat() if report.updated_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新周报失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新周报失败: {e!s}")


@router.delete("/{report_id}")
async def delete_weekly_report(
    report_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """删除周报"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的周报ID")

        report = db.query(WeeklyReport).filter(WeeklyReport.id == report_uuid).first()
        if not report:
            raise HTTPException(status_code=404, detail="周报不存在")

        report_date = report.report_date.isoformat() if report.report_date else ""

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="weekly_report",
                resource_id=str(report.id),
                details={"report_date": report_date},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(report)
        db.commit()

        return {"message": "周报已删除", "id": report_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除周报失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除周报失败: {e!s}")

