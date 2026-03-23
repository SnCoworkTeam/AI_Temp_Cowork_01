"""
基础数据管理API
"""

import logging
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
from database.src.models.project_models import Project
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic模型
class BasicDataCategoryCreate(BaseModel):
    category_type: str
    code: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    sort_order: int = 0
    is_active: bool = True
    metadata: dict | None = None


class BasicDataCategoryUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    parent_id: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    metadata: dict | None = None


class BasicDataCategoryResponse(BaseModel):
    id: str
    category_type: str
    code: str
    name: str
    description: str | None
    parent_id: str | None
    sort_order: int
    is_active: bool
    metadata: dict | None = None
    extra_metadata: dict | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BasicDataCategoryListResponse(BaseModel):
    total: int
    items: list[BasicDataCategoryResponse]


class ProjectBasicDataMappingCreate(BaseModel):
    category_id: str


class ProjectBasicDataMappingResponse(BaseModel):
    id: str
    project_id: str
    category_id: str
    category_name: str
    category_type: str
    category_code: str
    created_at: str

    class Config:
        from_attributes = True


class ProjectBasicDataMappingListResponse(BaseModel):
    total: int
    items: list[ProjectBasicDataMappingResponse]


# 基础数据分类CRUD
@router.get("/categories", response_model=BasicDataCategoryListResponse)
async def list_categories(
    category_type: str | None = Query(None, description="分类类型过滤"),
    is_active: bool | None = Query(None, description="是否启用过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取基础数据分类列表"""
    try:
        query = db.query(BasicDataCategory)

        if category_type:
            query = query.filter(BasicDataCategory.category_type == category_type)

        if is_active is not None:
            query = query.filter(BasicDataCategory.is_active == is_active)

        total = query.count()
        categories = (
            query.order_by(BasicDataCategory.category_type, BasicDataCategory.sort_order, BasicDataCategory.code)
            .offset(skip)
            .limit(limit)
            .all()
        )

        return BasicDataCategoryListResponse(
            total=total,
            items=[
                BasicDataCategoryResponse(
                    id=str(c.id),
                    category_type=c.category_type,
                    code=c.code,
                    name=c.name,
                    description=c.description,
                    parent_id=str(c.parent_id) if c.parent_id else None,
                    sort_order=c.sort_order,
                    is_active=c.is_active,
                    metadata=c.extra_metadata,
                    extra_metadata=c.extra_metadata,
                    created_at=c.created_at.isoformat() if c.created_at else "",
                    updated_at=c.updated_at.isoformat() if c.updated_at else "",
                )
                for c in categories
            ],
        )
    except Exception as e:
        logger.error(f"获取基础数据分类列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取基础数据分类列表失败: {e!s}")


@router.post("/categories", response_model=BasicDataCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: BasicDataCategoryCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """创建基础数据分类"""
    try:
        # 检查编码是否已存在
        existing = (
            db.query(BasicDataCategory)
            .filter(
                BasicDataCategory.category_type == category_data.category_type,
                BasicDataCategory.code == category_data.code,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400, detail=f"分类编码 {category_data.code} 在类型 {category_data.category_type} 中已存在"
            )

        # 解析parent_id
        parent_id = None
        if category_data.parent_id:
            try:
                parent_id = UUID(category_data.parent_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的父分类ID")

        # 创建分类
        category = BasicDataCategory(
            category_type=category_data.category_type,
            code=category_data.code,
            name=category_data.name,
            description=category_data.description,
            parent_id=parent_id,
            sort_order=category_data.sort_order,
            is_active=category_data.is_active,
            extra_metadata=category_data.metadata or {},
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return BasicDataCategoryResponse(
            id=str(category.id),
            category_type=category.category_type,
            code=category.code,
            name=category.name,
            description=category.description,
            parent_id=str(category.parent_id) if category.parent_id else None,
            sort_order=category.sort_order,
            is_active=category.is_active,
            metadata=category.extra_metadata,
            extra_metadata=category.extra_metadata,
            created_at=category.created_at.isoformat() if category.created_at else "",
            updated_at=category.updated_at.isoformat() if category.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建基础数据分类失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建基础数据分类失败: {e!s}")


@router.get("/categories/{category_id}", response_model=BasicDataCategoryResponse)
async def get_category(category_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取基础数据分类详情"""
    try:
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == UUID(category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        return BasicDataCategoryResponse(
            id=str(category.id),
            category_type=category.category_type,
            code=category.code,
            name=category.name,
            description=category.description,
            parent_id=str(category.parent_id) if category.parent_id else None,
            sort_order=category.sort_order,
            is_active=category.is_active,
            metadata=category.extra_metadata,
            extra_metadata=category.extra_metadata,
            created_at=category.created_at.isoformat() if category.created_at else "",
            updated_at=category.updated_at.isoformat() if category.updated_at else "",
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的分类ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基础数据分类详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取基础数据分类详情失败: {e!s}")


@router.put("/categories/{category_id}", response_model=BasicDataCategoryResponse)
async def update_category(
    category_id: str,
    category_data: BasicDataCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """更新基础数据分类"""
    try:
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == UUID(category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 如果更新code，检查是否冲突
        if category_data.code and category_data.code != category.code:
            existing = (
                db.query(BasicDataCategory)
                .filter(
                    BasicDataCategory.category_type == category.category_type,
                    BasicDataCategory.code == category_data.code,
                    BasicDataCategory.id != category.id,
                )
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail=f"分类编码 {category_data.code} 已存在")

        # 更新字段
        if category_data.code is not None:
            category.code = category_data.code
        if category_data.name is not None:
            category.name = category_data.name
        if category_data.description is not None:
            category.description = category_data.description
        if category_data.parent_id is not None:
            category.parent_id = UUID(category_data.parent_id) if category_data.parent_id else None
        if category_data.sort_order is not None:
            category.sort_order = category_data.sort_order
        if category_data.is_active is not None:
            category.is_active = category_data.is_active
        if category_data.metadata is not None:
            category.extra_metadata = category_data.metadata

        db.commit()
        db.refresh(category)

        return BasicDataCategoryResponse(
            id=str(category.id),
            category_type=category.category_type,
            code=category.code,
            name=category.name,
            description=category.description,
            parent_id=str(category.parent_id) if category.parent_id else None,
            sort_order=category.sort_order,
            is_active=category.is_active,
            metadata=category.extra_metadata,
            extra_metadata=category.extra_metadata,
            created_at=category.created_at.isoformat() if category.created_at else "",
            updated_at=category.updated_at.isoformat() if category.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新基础数据分类失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新基础数据分类失败: {e!s}")


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """删除基础数据分类"""
    try:
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == UUID(category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 检查是否有子分类
        children = db.query(BasicDataCategory).filter(BasicDataCategory.parent_id == category.id).count()
        if children > 0:
            raise HTTPException(status_code=400, detail="存在子分类，无法删除")

        # 检查是否有关联的项目
        mappings = db.query(ProjectBasicDataMapping).filter(ProjectBasicDataMapping.category_id == category.id).count()
        if mappings > 0:
            raise HTTPException(status_code=400, detail="存在项目关联，无法删除")

        db.delete(category)
        db.commit()

        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除基础数据分类失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除基础数据分类失败: {e!s}")


# 项目基础数据关联
@router.get("/projects/{project_id}/basic-data", response_model=ProjectBasicDataMappingListResponse)
async def get_project_basic_data(
    project_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """获取项目的基础数据分类"""
    try:
        mappings = (
            db.query(ProjectBasicDataMapping).filter(ProjectBasicDataMapping.project_id == UUID(project_id)).all()
        )

        items = []
        for mapping in mappings:
            category = db.query(BasicDataCategory).filter(BasicDataCategory.id == mapping.category_id).first()

            if category:
                items.append(
                    ProjectBasicDataMappingResponse(
                        id=str(mapping.id),
                        project_id=str(mapping.project_id),
                        category_id=str(mapping.category_id),
                        category_name=category.name,
                        category_type=category.category_type,
                        category_code=category.code,
                        created_at=mapping.created_at.isoformat() if mapping.created_at else "",
                    )
                )

        return ProjectBasicDataMappingListResponse(total=len(items), items=items)
    except Exception as e:
        logger.error(f"获取项目基础数据失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取项目基础数据失败: {e!s}")


@router.post(
    "/projects/{project_id}/basic-data",
    response_model=ProjectBasicDataMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_basic_data(
    project_id: str,
    mapping_data: ProjectBasicDataMappingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """为项目添加基础数据分类"""
    try:
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 检查分类是否存在
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == UUID(mapping_data.category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 检查是否已存在
        existing = (
            db.query(ProjectBasicDataMapping)
            .filter(
                ProjectBasicDataMapping.project_id == UUID(project_id),
                ProjectBasicDataMapping.category_id == UUID(mapping_data.category_id),
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="项目已关联该分类")

        # 创建关联
        mapping = ProjectBasicDataMapping(project_id=UUID(project_id), category_id=UUID(mapping_data.category_id))

        db.add(mapping)
        db.commit()
        db.refresh(mapping)

        return ProjectBasicDataMappingResponse(
            id=str(mapping.id),
            project_id=str(mapping.project_id),
            category_id=str(mapping.category_id),
            category_name=category.name,
            category_type=category.category_type,
            category_code=category.code,
            created_at=mapping.created_at.isoformat() if mapping.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加项目基础数据失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加项目基础数据失败: {e!s}")


@router.delete("/projects/{project_id}/basic-data/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_basic_data(
    project_id: str, mapping_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """移除项目的基础数据分类"""
    try:
        mapping = (
            db.query(ProjectBasicDataMapping)
            .filter(
                ProjectBasicDataMapping.id == UUID(mapping_id), ProjectBasicDataMapping.project_id == UUID(project_id)
            )
            .first()
        )

        if not mapping:
            raise HTTPException(status_code=404, detail="关联不存在")

        db.delete(mapping)
        db.commit()

        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除项目基础数据失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"移除项目基础数据失败: {e!s}")
