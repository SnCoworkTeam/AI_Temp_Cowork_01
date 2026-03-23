"""
质量规则API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.metadata_catalog import MetadataCatalogService
from ..services.quality_rules_engine import QualityRulesEngine
from ..models.data_asset import DataAssetSchema
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response

router = APIRouter()
logger = setup_logger(__name__)


def get_catalog_service(db: Session = Depends(get_db)) -> MetadataCatalogService:
    """获取元数据目录服务"""
    return MetadataCatalogService(db)


def get_quality_engine(db: Session = Depends(get_db)) -> QualityRulesEngine:
    """获取质量规则引擎"""
    return QualityRulesEngine(db=db)


@router.post(
    "/quality/validate/{asset_id}",
    summary="验证数据资产质量",
    tags=["Quality"]
)
async def validate_asset_quality(
    asset_id: int,
    service: MetadataCatalogService = Depends(get_catalog_service),
    quality_engine: QualityRulesEngine = Depends(get_quality_engine)
):
    """验证数据资产质量"""
    try:
        # 获取数据资产
        asset = service.get_data_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Data asset not found")
        
        # 验证质量
        result = quality_engine.validate_asset(asset)
        
        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "validation_result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate asset quality: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/summary",
    summary="获取质量摘要",
    tags=["Quality"]
)
async def get_quality_summary(
    asset_type: Optional[str] = Query(None, description="资产类型"),
    classification: Optional[str] = Query(None, description="分类"),
    service: MetadataCatalogService = Depends(get_catalog_service),
    quality_engine: QualityRulesEngine = Depends(get_quality_engine)
):
    """获取数据资产质量摘要"""
    try:
        # 获取数据资产列表
        assets = service.list_data_assets(
            asset_type=asset_type,
            classification=classification,
            limit=10000  # 获取所有资产进行质量分析
        )
        
        # 计算质量摘要
        summary = quality_engine.get_quality_summary(assets)
        
        return summary
    except Exception as e:
        logger.error(f"Failed to get quality summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/quality/rules/execute/{asset_id}",
    summary="执行质量规则",
    tags=["Quality"]
)
async def execute_quality_rules(
    asset_id: int,
    rules: Optional[List[str]] = Query(None, description="规则ID列表（可选，不提供则执行所有规则）"),
    quality_engine: QualityRulesEngine = Depends(get_quality_engine)
):
    """执行质量规则并返回结果（支持向量化）"""
    try:
        result = await quality_engine.execute_rules(asset_id, rules)
        return result
    except Exception as e:
        logger.error(f"Failed to execute quality rules: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/quality/metrics/vectorize",
    summary="向量化质量指标",
    tags=["Quality"]
)
async def vectorize_quality_metrics(
    metrics: Dict[str, Any] = Body(..., description="质量指标字典"),
    quality_engine: QualityRulesEngine = Depends(get_quality_engine)
):
    """将质量指标向量化"""
    try:
        vector = await quality_engine.vectorize_metrics(metrics)
        return {
            "success": True,
            "vector": vector,
            "vector_dimension": len(vector)
        }
    except Exception as e:
        logger.error(f"Failed to vectorize metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/vectors/{asset_id}/history",
    summary="获取质量向量历史",
    tags=["Quality"]
)
async def get_quality_vector_history(
    asset_id: int,
    limit: int = 10,
    quality_engine: QualityRulesEngine = Depends(get_quality_engine)
):
    """获取指定资产的质量向量历史"""
    try:
        history = quality_engine.get_vector_history(asset_id, limit)
        return {
            "success": True,
            "asset_id": asset_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get vector history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


