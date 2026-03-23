"""
项目模板管理路由
"""

import logging
from datetime import datetime
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.basic_data_models import BasicDataCategory
from database.src.models.project_models import ProjectTemplate
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import require_auth, require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


class ProjectTemplateResponse(BaseModel):
    """项目模板响应模型"""

    id: str
    template_code: str
    name: str
    description: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    template_structure: dict
    is_active: bool
    usage_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectTemplateListResponse(BaseModel):
    """项目模板列表响应"""

    total: int
    items: list[ProjectTemplateResponse]


class ProjectTemplateCreate(BaseModel):
    """创建项目模板请求模型"""

    template_code: str
    name: str
    description: str | None = None
    category_id: str | None = None
    phase_category_ids: list[str]  # 阶段分类ID列表（从基础数据获取）


class ProjectTemplateUpdate(BaseModel):
    """更新项目模板请求模型"""

    name: str | None = None
    description: str | None = None
    category_id: str | None = None
    phase_category_ids: list[str] | None = None  # 更新阶段结构
    is_active: bool | None = None


@router.get("/project-templates", response_model=ProjectTemplateListResponse)
async def list_templates(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取模板列表"""
    try:
        query = db.query(ProjectTemplate)

        if is_active is not None:
            query = query.filter(ProjectTemplate.is_active == is_active)

        total = query.count()
        templates = query.order_by(ProjectTemplate.created_at.desc()).offset(skip).limit(limit).all()

        items = []
        for template in templates:
            category_name = None
            if template.category_id and template.category:
                category_name = template.category.name

            items.append(
                ProjectTemplateResponse(
                    id=str(template.id),
                    template_code=template.template_code,
                    name=template.name,
                    description=template.description,
                    category_id=str(template.category_id) if template.category_id else None,
                    category_name=category_name,
                    template_structure=template.template_structure or {},
                    is_active=template.is_active,
                    usage_count=template.usage_count,
                    created_at=template.created_at.isoformat() if template.created_at else "",
                    updated_at=template.updated_at.isoformat() if template.updated_at else "",
                )
            )

        return ProjectTemplateListResponse(total=total, items=items)
    except Exception as e:
        logger.error(f"获取模板列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {e!s}")


@router.get("/project-templates/{template_id}", response_model=ProjectTemplateResponse)
async def get_template(template_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取模板详情"""
    try:
        try:
            template_uuid = UUID(template_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的模板ID")

        template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_uuid).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        category_name = None
        if template.category_id and template.category:
            category_name = template.category.name

        return ProjectTemplateResponse(
            id=str(template.id),
            template_code=template.template_code,
            name=template.name,
            description=template.description,
            category_id=str(template.category_id) if template.category_id else None,
            category_name=category_name,
            template_structure=template.template_structure or {},
            is_active=template.is_active,
            usage_count=template.usage_count,
            created_at=template.created_at.isoformat() if template.created_at else "",
            updated_at=template.updated_at.isoformat() if template.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {e!s}")


@router.post("/project-templates", response_model=ProjectTemplateResponse, status_code=201)
async def create_template(
    template_data: ProjectTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """创建模板（需要管理员权限）"""
    try:
        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        # 检查模板编码是否已存在
        existing_template = (
            db.query(ProjectTemplate).filter(ProjectTemplate.template_code == template_data.template_code).first()
        )
        if existing_template:
            raise HTTPException(status_code=400, detail=f"模板编码 '{template_data.template_code}' 已存在")

        # 验证阶段分类ID并构建阶段结构
        phases = []
        for idx, category_id in enumerate(template_data.phase_category_ids):
            try:
                category_uuid = UUID(category_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的阶段分类ID: {category_id}")

            category = (
                db.query(BasicDataCategory)
                .filter(
                    BasicDataCategory.id == category_uuid,
                    BasicDataCategory.category_type == "project_phase",
                )
                .first()
            )

            if not category:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的阶段分类ID: {category_id}，该分类不存在或不是项目阶段类型",
                )

            phases.append(
                {
                    "category_id": str(category.id),
                    "category_code": category.code,
                    "category_name": category.name,
                    "sequence": idx + 1,
                    "tasks": [],  # 预定义任务模板（可选）
                }
            )

        # 解析category_id
        category_id = None
        if template_data.category_id:
            try:
                category_id = UUID(template_data.category_id)
                # 验证分类是否存在
                category = db.query(BasicDataCategory).filter(BasicDataCategory.id == category_id).first()
                if not category:
                    raise HTTPException(status_code=400, detail=f"无效的模板分类ID: {template_data.category_id}")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的模板分类ID: {template_data.category_id}")

        # 创建模板
        template = ProjectTemplate(
            template_code=template_data.template_code,
            name=template_data.name,
            description=template_data.description,
            category_id=category_id,
            template_structure={"phases": phases},
            is_active=True,
            usage_count=0,
        )

        db.add(template)
        db.flush()

        # 记录审计日志
        try:
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="create",
                resource_type="project_template",
                resource_id=str(template.id),
                details={"template_code": template_data.template_code, "name": template_data.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()
        db.refresh(template)

        category_name = None
        if template.category_id and template.category:
            category_name = template.category.name

        return ProjectTemplateResponse(
            id=str(template.id),
            template_code=template.template_code,
            name=template.name,
            description=template.description,
            category_id=str(template.category_id) if template.category_id else None,
            category_name=category_name,
            template_structure=template.template_structure or {},
            is_active=template.is_active,
            usage_count=template.usage_count,
            created_at=template.created_at.isoformat() if template.created_at else "",
            updated_at=template.updated_at.isoformat() if template.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建模板失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建模板失败: {e!s}")


@router.put("/project-templates/{template_id}", response_model=ProjectTemplateResponse)
async def update_template(
    template_id: str,
    template_data: ProjectTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """更新模板（需要管理员权限）"""
    try:
        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            template_uuid = UUID(template_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的模板ID")

        template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_uuid).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 更新字段
        if template_data.name is not None:
            template.name = template_data.name
        if template_data.description is not None:
            template.description = template_data.description
        if template_data.is_active is not None:
            template.is_active = template_data.is_active

        # 更新分类
        if template_data.category_id is not None:
            if template_data.category_id:
                try:
                    category_uuid = UUID(template_data.category_id)
                    category = db.query(BasicDataCategory).filter(BasicDataCategory.id == category_uuid).first()
                    if not category:
                        raise HTTPException(status_code=400, detail=f"无效的模板分类ID: {template_data.category_id}")
                    template.category_id = category_uuid
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"无效的模板分类ID: {template_data.category_id}")
            else:
                template.category_id = None

        # 更新阶段结构
        if template_data.phase_category_ids is not None:
            phases = []
            for idx, category_id in enumerate(template_data.phase_category_ids):
                try:
                    category_uuid = UUID(category_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"无效的阶段分类ID: {category_id}")

                category = (
                    db.query(BasicDataCategory)
                    .filter(
                        BasicDataCategory.id == category_uuid,
                        BasicDataCategory.category_type == "project_phase",
                    )
                    .first()
                )

                if not category:
                    raise HTTPException(status_code=400, detail=f"无效的阶段分类ID: {category_id}")

                phases.append(
                    {
                        "category_id": str(category.id),
                        "category_code": category.code,
                        "category_name": category.name,
                        "sequence": idx + 1,
                        "tasks": [],
                    }
                )

            # 更新模板结构
            current_structure = template.template_structure or {}
            current_structure["phases"] = phases
            template.template_structure = current_structure

        db.flush()

        # 记录审计日志
        try:
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="update",
                resource_type="project_template",
                resource_id=str(template.id),
                details={"name": template.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.commit()
        db.refresh(template)

        category_name = None
        if template.category_id and template.category:
            category_name = template.category.name

        return ProjectTemplateResponse(
            id=str(template.id),
            template_code=template.template_code,
            name=template.name,
            description=template.description,
            category_id=str(template.category_id) if template.category_id else None,
            category_name=category_name,
            template_structure=template.template_structure or {},
            is_active=template.is_active,
            usage_count=template.usage_count,
            created_at=template.created_at.isoformat() if template.created_at else "",
            updated_at=template.updated_at.isoformat() if template.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新模板失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新模板失败: {e!s}")


@router.delete("/project-templates/{template_id}", status_code=204)
async def delete_template(template_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    """删除模板（需要管理员权限）"""
    try:
        from database.src.models.system_models import AuditLog

        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            template_uuid = UUID(template_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的模板ID")

        template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_uuid).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 检查模板是否被使用
        if template.usage_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"模板已被使用 {template.usage_count} 次，无法删除。请先删除使用该模板的计划。",
            )

        # 记录审计日志
        try:
            audit_log = AuditLog(
                user_id=UUID(user_id) if user_id != "anonymous" else None,
                action="delete",
                resource_type="project_template",
                resource_id=str(template.id),
                details={"template_code": template.template_code, "name": template.name},
                timestamp=datetime.utcnow(),
                result="success",
            )
            db.add(audit_log)
            db.flush()
        except Exception as e:
            logger.warning(f"记录审计日志失败: {e!s}")

        db.delete(template)
        db.commit()

        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模板失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除模板失败: {e!s}")
