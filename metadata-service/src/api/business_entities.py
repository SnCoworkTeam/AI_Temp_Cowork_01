"""
业务实体API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.business_entity import BusinessEntitySchema, BusinessEntityCreate, BusinessEntityUpdate
from ..services.metadata_catalog import MetadataCatalogService
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


def get_catalog_service(db: Session = Depends(get_db)) -> MetadataCatalogService:
    """获取元数据目录服务"""
    return MetadataCatalogService(db)


@router.post(
    "/business-entities",
    response_model=BusinessEntitySchema,
    summary="创建业务实体",
    tags=["Business Entities"]
)
async def create_business_entity(
    entity_data: BusinessEntityCreate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """创建业务实体"""
    try:
        return service.create_business_entity(entity_data)
    except Exception as e:
        logger.error(f"Failed to create business entity: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/business-entities",
    response_model=List[BusinessEntitySchema],
    summary="列出业务实体",
    tags=["Business Entities"]
)
async def list_business_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    search: Optional[str] = None,
    business_domain: Optional[str] = Query(None, description="业务领域（classification_dimensions.business.domain）"),
    standardized_tag: Optional[str] = Query(None, description="标准化标签（standardized_tags）"),
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """列出业务实体"""
    try:
        return service.list_business_entities(
            skip=skip,
            limit=limit,
            entity_type=entity_type,
            parent_id=parent_id,
            search=search,
            business_domain=business_domain,
            standardized_tag=standardized_tag
        )
    except Exception as e:
        logger.error(f"Failed to list business entities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/business-entities/{entity_id}",
    response_model=BusinessEntitySchema,
    summary="获取业务实体",
    tags=["Business Entities"]
)
async def get_business_entity(
    entity_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """获取业务实体详情"""
    entity = service.get_business_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Business entity not found")
    return entity


@router.put(
    "/business-entities/{entity_id}",
    response_model=BusinessEntitySchema,
    summary="更新业务实体",
    tags=["Business Entities"]
)
async def update_business_entity(
    entity_id: int,
    entity_data: BusinessEntityUpdate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """更新业务实体"""
    entity = service.update_business_entity(entity_id, entity_data)
    if not entity:
        raise HTTPException(status_code=404, detail="Business entity not found")
    return entity


@router.delete(
    "/business-entities/{entity_id}",
    summary="删除业务实体",
    tags=["Business Entities"]
)
async def delete_business_entity(
    entity_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """删除业务实体"""
    success = service.delete_business_entity(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Business entity not found")
    return {"message": "Business entity deleted successfully"}


@router.post(
    "/business-entities/batch",
    summary="批量创建业务实体",
    tags=["Business Entities"]
)
async def create_business_entities_batch(
    request: dict,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """
    批量创建业务实体
    
    Request body:
    {
        "entities": [BusinessEntityCreate, ...],
        "skip_duplicates": true
    }
    """
    try:
        entities_data = request.get("entities", [])
        skip_duplicates = request.get("skip_duplicates", True)
        
        if not entities_data:
            raise HTTPException(status_code=400, detail="No entities provided")
        
        # 转换为BusinessEntityCreate对象
        entity_creates = [
            BusinessEntityCreate(**entity_data)
            for entity_data in entities_data
        ]
        
        result = service.create_business_entities_batch(
            entity_creates,
            skip_duplicates=skip_duplicates
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to create business entities batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
