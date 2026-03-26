"""
关键路径计算API路由
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import ProjectPlan
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission
from ..services.critical_path_calculator import CriticalPathCalculator
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/plans/{plan_id}/critical-path")
async def get_critical_path(
    project_id: str, plan_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """计算并获取项目计划的关键路径"""
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

        # 计算关键路径
        result = CriticalPathCalculator.calculate_critical_path(plan_uuid, db)

        return {"plan_id": plan_id, "project_id": project_id, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算关键路径失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"计算关键路径失败: {e!s}")


@router.post("/projects/{project_id}/plans/{plan_id}/calculate-schedule")
async def calculate_schedule(
    project_id: str, plan_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """重新计算计划时间表（包括关键路径）"""
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

        # 检查用户权限（需要UPDATE权限）
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            project_uuid, user_uuid, ProjectPermission.UPDATE, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限重新计算计划")

        # 重新计算关键路径
        result = CriticalPathCalculator.calculate_critical_path(plan_uuid, db)

        return {"message": "计划时间表已重新计算", "plan_id": plan_id, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新计算计划时间表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新计算计划时间表失败: {e!s}")
