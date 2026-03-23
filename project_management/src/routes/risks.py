"""
风险管理路由
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.project_models import Project, Risk
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..middleware.project_permissions import ProjectPermission, check_project_permission, get_user_projects
from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


class RiskResponse(BaseModel):
    """风险响应模型"""

    id: str
    project_id: str
    title: str | None = None
    name: str | None = None
    description: str | None = None
    severity: str | None = None
    risk_level: str | None = None
    status: str
    mitigation_plan: str | None = None
    identified_date: str | None = None
    project_name: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class RiskListResponse(BaseModel):
    """风险列表响应"""

    total: int
    items: list[RiskResponse]


@router.get("", response_model=RiskListResponse)
async def list_risks(
    project_id: str | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取风险列表（只返回用户有权限的项目风险）"""
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

        query = db.query(Risk)

        # 只查询用户有权限的项目风险
        if user_project_ids:
            query = query.filter(Risk.project_id.in_(user_project_ids))
        else:
            # 用户没有任何项目权限，返回空列表
            return RiskListResponse(total=0, items=[])

        if project_id:
            try:
                project_uuid = UUID(project_id)
                # 检查用户是否有该项目的权限
                if project_uuid not in user_project_ids:
                    raise HTTPException(status_code=403, detail="没有权限访问该项目")
                query = query.filter(Risk.project_id == project_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        if severity:
            query = query.filter(Risk.risk_level == severity)

        if status:
            query = query.filter(Risk.status == status)

        total = query.count()
        # 使用 created_at 排序，因为 Risk 模型中没有 identified_date 字段
        risks = query.order_by(Risk.created_at.desc()).offset(skip).limit(limit).all()

        # 获取项目名称
        project_ids = {str(r.project_id) for r in risks}
        projects = {}
        if project_ids:
            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        items = []
        for risk in risks:
            items.append(
                RiskResponse(
                    id=str(risk.id),
                    project_id=str(risk.project_id),
                    title=risk.name,  # 使用name字段作为title
                    name=risk.name,
                    description=risk.description,
                    severity=risk.risk_level,  # 使用risk_level作为severity
                    risk_level=risk.risk_level,
                    status=risk.status,
                    mitigation_plan=risk.mitigation_plan,
                    identified_date=risk.created_at.isoformat() if risk.created_at else None,  # 使用created_at作为identified_date
                    project_name=projects.get(str(risk.project_id)),
                    created_at=risk.created_at.isoformat() if risk.created_at else "",
                )
            )

        return RiskListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"获取风险列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取风险列表失败: {e!s}")


@router.get("/{risk_id}", response_model=RiskResponse)
async def get_risk(risk_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取风险详情（需要项目READ权限）"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            risk_uuid = UUID(risk_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的风险ID或用户ID")

        risk = db.query(Risk).filter(Risk.id == risk_uuid).first()
        if not risk:
            raise HTTPException(status_code=404, detail="风险不存在")

        # 检查用户是否有该项目的READ权限
        username = current_user.get("username", "").lower()
        user_roles = current_user.get("roles", [])
        is_admin = (
            username == "admin" or "admin" in [r.lower() for r in user_roles] if isinstance(user_roles, list) else False
        )

        has_permission = check_project_permission(
            risk.project_id, user_uuid, ProjectPermission.READ, db, is_admin=is_admin
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="没有权限访问该风险")

        project = db.query(Project).filter(Project.id == risk.project_id).first()

        return RiskResponse(
            id=str(risk.id),
            project_id=str(risk.project_id),
            title=risk.name,
            name=risk.name,
            description=risk.description,
            severity=risk.risk_level,
            risk_level=risk.risk_level,
            status=risk.status,
            mitigation_plan=risk.mitigation_plan,
            identified_date=(
                risk.identified_date.isoformat() if hasattr(risk, "identified_date") and risk.identified_date else None
            ),
            project_name=project.name if project else None,
            created_at=risk.created_at.isoformat() if risk.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取风险详情失败: {e!s}")


class RiskCreate(BaseModel):
    """风险创建模型"""

    project_id: str
    name: str
    description: str | None = None
    risk_level: str | None = "medium"  # low, medium, high
    status: str | None = "open"  # open, in_progress, resolved, closed
    mitigation_plan: str | None = None
    identified_date: str | None = None


class RiskUpdate(BaseModel):
    """风险更新模型"""

    name: str | None = None
    description: str | None = None
    risk_level: str | None = None
    status: str | None = None
    mitigation_plan: str | None = None
    identified_date: str | None = None


@router.post("", response_model=RiskResponse)
async def create_risk(risk_data: RiskCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """创建风险（需要项目CREATE权限）"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 验证项目是否存在
        try:
            project_id = UUID(risk_data.project_id)
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
            raise HTTPException(status_code=403, detail="没有权限在该项目中创建风险")

        # 解析日期
        identified_date = None
        if risk_data.identified_date:
            try:
                identified_date = datetime.fromisoformat(risk_data.identified_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                identified_date = datetime.strptime(risk_data.identified_date, "%Y-%m-%d").date()
        else:
            identified_date = datetime.utcnow().date()

        # 创建风险
        risk = Risk(
            project_id=project_id,
            name=risk_data.name,
            description=risk_data.description,
            risk_level=risk_data.risk_level or "medium",
            status=risk_data.status or "open",
            mitigation_plan=risk_data.mitigation_plan,
        )

        # 如果Risk模型有identified_date字段，设置它
        if hasattr(risk, "identified_date"):
            risk.identified_date = identified_date

        db.add(risk)
        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="risk",
                resource_id=str(risk.id),
                details={"project_id": str(project_id), "name": risk_data.name, "risk_level": risk_data.risk_level},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        return RiskResponse(
            id=str(risk.id),
            project_id=str(risk.project_id),
            title=risk.name,
            name=risk.name,
            description=risk.description,
            severity=risk.risk_level,
            risk_level=risk.risk_level,
            status=risk.status,
            mitigation_plan=risk.mitigation_plan,
            identified_date=identified_date.isoformat() if identified_date else None,
            project_name=project.name,
            created_at=risk.created_at.isoformat() if risk.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建风险失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建风险失败: {e!s}")


@router.put("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: str, risk_data: RiskUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """更新风险"""
    try:
        from datetime import datetime

        from database.src.models.project_models import Project
        from database.src.models.system_models import AuditLog

        try:
            risk_uuid = UUID(risk_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的风险ID")

        risk = db.query(Risk).filter(Risk.id == risk_uuid).first()
        if not risk:
            raise HTTPException(status_code=404, detail="风险不存在")

        # 更新字段
        if risk_data.name is not None:
            risk.name = risk_data.name
        if risk_data.description is not None:
            risk.description = risk_data.description
        if risk_data.risk_level is not None:
            risk.risk_level = risk_data.risk_level
        if risk_data.status is not None:
            risk.status = risk_data.status
        if risk_data.mitigation_plan is not None:
            risk.mitigation_plan = risk_data.mitigation_plan
        if risk_data.identified_date is not None:
            try:
                identified_date = datetime.fromisoformat(risk_data.identified_date.replace("Z", "+00:00")).date()
            except (ValueError, AttributeError):
                identified_date = datetime.strptime(risk_data.identified_date, "%Y-%m-%d").date()
            if hasattr(risk, "identified_date"):
                risk.identified_date = identified_date

        db.flush()

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="risk",
                resource_id=str(risk.id),
                details={"name": risk_data.name, "status": risk_data.status},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()

        project = db.query(Project).filter(Project.id == risk.project_id).first()

        identified_date = None
        if hasattr(risk, "identified_date") and risk.identified_date:
            identified_date = risk.identified_date.isoformat()

        return RiskResponse(
            id=str(risk.id),
            project_id=str(risk.project_id),
            title=risk.name,
            name=risk.name,
            description=risk.description,
            severity=risk.risk_level,
            risk_level=risk.risk_level,
            status=risk.status,
            mitigation_plan=risk.mitigation_plan,
            identified_date=identified_date,
            project_name=project.name if project else None,
            created_at=risk.created_at.isoformat() if risk.created_at else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新风险失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新风险失败: {e!s}")


@router.delete("/{risk_id}")
async def delete_risk(risk_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """删除风险"""
    try:
        from datetime import datetime

        from database.src.models.system_models import AuditLog

        try:
            risk_uuid = UUID(risk_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的风险ID")

        risk = db.query(Risk).filter(Risk.id == risk_uuid).first()
        if not risk:
            raise HTTPException(status_code=404, detail="风险不存在")

        risk_name = risk.name

        # 记录审计日志
        try:
            user_id = current_user.get("user_id", "anonymous")
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="risk",
                resource_id=str(risk.id),
                details={"name": risk_name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(risk)
        db.commit()

        return {"message": "风险已删除", "id": risk_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除风险失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除风险失败: {e!s}")
