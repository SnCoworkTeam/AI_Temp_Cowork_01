"""
计划变更历史API路由
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import PlanChangeLog, ProjectPlan
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/plans/{plan_id}/change-logs")
async def get_plan_change_logs(
    project_id: str,
    plan_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    change_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取计划变更历史"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            project_uuid = UUID(project_id)
            plan_uuid = UUID(plan_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的ID")

        # 检查计划是否存在
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_uuid).first()
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        if plan.project_id != project_uuid:
            raise HTTPException(status_code=400, detail="计划不属于该项目")

        # 检查用户权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            project_uuid, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限访问该计划")

        # 查询变更日志
        query = db.query(PlanChangeLog).filter(PlanChangeLog.plan_id == plan_uuid)

        if change_type:
            query = query.filter(PlanChangeLog.change_type == change_type)

        total = query.count()
        logs = query.order_by(PlanChangeLog.timestamp.desc()).offset(skip).limit(limit).all()

        # 构建响应
        items = []
        for log in logs:
            items.append(
                {
                    "id": str(log.id),
                    "plan_id": str(log.plan_id),
                    "changed_by": str(log.changed_by) if log.changed_by else None,
                    "change_type": log.change_type,
                    "change_details": log.change_details or {},
                    "before_snapshot": log.before_snapshot,
                    "after_snapshot": log.after_snapshot,
                    "critical_path_changed": log.critical_path_changed,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                }
            )

        return {"total": total, "items": items, "page": skip // limit + 1, "page_size": limit}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取计划变更历史失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取计划变更历史失败: {e!s}")


@router.get("/projects/{project_id}/plans/{plan_id}/change-logs/{log_id}")
async def get_plan_change_log(
    project_id: str,
    plan_id: str,
    log_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取单个变更日志详情"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            project_uuid = UUID(project_id)
            plan_uuid = UUID(plan_id)
            log_uuid = UUID(log_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的ID")

        # 检查计划是否存在
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_uuid).first()
        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        if plan.project_id != project_uuid:
            raise HTTPException(status_code=400, detail="计划不属于该项目")

        # 检查用户权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            project_uuid, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限访问该计划")

        # 查询变更日志
        log = db.query(PlanChangeLog).filter(PlanChangeLog.id == log_uuid, PlanChangeLog.plan_id == plan_uuid).first()

        if not log:
            raise HTTPException(status_code=404, detail="变更日志不存在")

        return {
            "id": str(log.id),
            "plan_id": str(log.plan_id),
            "changed_by": str(log.changed_by) if log.changed_by else None,
            "change_type": log.change_type,
            "change_details": log.change_details or {},
            "before_snapshot": log.before_snapshot,
            "after_snapshot": log.after_snapshot,
            "critical_path_changed": log.critical_path_changed,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取变更日志详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取变更日志详情失败: {e!s}")
