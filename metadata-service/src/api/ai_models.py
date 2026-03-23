"""
AI模型API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.ai_model import AIModelSchema, AIModelCreate, AIModelUpdate
from ..services.metadata_catalog import MetadataCatalogService
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


def get_catalog_service(db: Session = Depends(get_db)) -> MetadataCatalogService:
    """获取元数据目录服务"""
    return MetadataCatalogService(db)


@router.post(
    "/ai-models",
    response_model=AIModelSchema,
    summary="创建AI模型",
    tags=["AI Models"]
)
async def create_ai_model(
    model_data: AIModelCreate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """创建AI模型"""
    try:
        return service.create_ai_model(model_data)
    except Exception as e:
        logger.error(f"Failed to create AI model: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ai-models",
    response_model=List[AIModelSchema],
    summary="列出AI模型",
    tags=["AI Models"]
)
async def list_ai_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    business_domain: Optional[str] = Query(None, description="业务领域（classification_dimensions.business.domain）"),
    lifecycle_status: Optional[str] = Query(None, description="生命周期状态（classification_dimensions.lifecycle.status）"),
    standardized_tag: Optional[str] = Query(None, description="标准化标签（standardized_tags）"),
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """列出AI模型"""
    try:
        return service.list_ai_models(
            skip=skip,
            limit=limit,
            model_type=model_type,
            status=status,
            search=search,
            business_domain=business_domain,
            lifecycle_status=lifecycle_status,
            standardized_tag=standardized_tag
        )
    except Exception as e:
        logger.error(f"Failed to list AI models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ai-models/{model_id}",
    response_model=AIModelSchema,
    summary="获取AI模型",
    tags=["AI Models"]
)
async def get_ai_model(
    model_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """获取AI模型详情"""
    model = service.get_ai_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="AI model not found")
    return model


@router.put(
    "/ai-models/{model_id}",
    response_model=AIModelSchema,
    summary="更新AI模型",
    tags=["AI Models"]
)
async def update_ai_model(
    model_id: int,
    model_data: AIModelUpdate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """更新AI模型"""
    model = service.update_ai_model(model_id, model_data)
    if not model:
        raise HTTPException(status_code=404, detail="AI model not found")
    return model


@router.delete(
    "/ai-models/{model_id}",
    summary="删除AI模型",
    tags=["AI Models"]
)
async def delete_ai_model(
    model_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """删除AI模型"""
    success = service.delete_ai_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="AI model not found")
    return {"message": "AI model deleted successfully"}

