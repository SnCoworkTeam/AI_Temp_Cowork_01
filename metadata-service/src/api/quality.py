"""
数据质量API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from ..models.data_asset import DataAssetSchema
from ..models.quality import QualityCheckResult, QualityDashboard
from ..services.quality_service import QualityService
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger
from shared_libs.src.models.metadata_models import DataQualityMetrics

router = APIRouter()
logger = setup_logger(__name__)


def get_quality_service(db: Session = Depends(get_db)) -> QualityService:
    """获取数据质量服务"""
    return QualityService(db)


@router.put(
    "/quality/assets/{asset_id}/metrics",
    response_model=DataAssetSchema,
    summary="更新质量指标",
    tags=["Quality"]
)
async def update_quality_metrics(
    asset_id: int,
    metrics: Dict[str, Any],
    service: QualityService = Depends(get_quality_service)
):
    """更新数据资产的质量指标"""
    try:
        # 验证指标格式
        validation = service.validate_quality_metrics(metrics)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail={"message": "Invalid quality metrics", "errors": validation["errors"]}
            )
        
        asset = service.update_quality_metrics(asset_id, metrics)
        if not asset:
            raise HTTPException(status_code=404, detail="Data asset not found")
        return asset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update quality metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/assets/{asset_id}/metrics",
    summary="获取质量指标",
    tags=["Quality"]
)
async def get_quality_metrics(
    asset_id: int,
    service: QualityService = Depends(get_quality_service)
):
    """获取数据资产的质量指标"""
    metrics = service.get_quality_metrics(asset_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail="Data asset not found")
    return metrics


@router.get(
    "/quality/summary",
    summary="获取质量摘要",
    tags=["Quality"]
)
async def get_quality_summary(
    service: QualityService = Depends(get_quality_service)
):
    """获取数据质量摘要统计"""
    try:
        return service.get_quality_summary()
    except Exception as e:
        logger.error(f"Failed to get quality summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/issues",
    summary="获取质量问题",
    tags=["Quality"]
)
async def get_quality_issues(
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="质量分数阈值"),
    service: QualityService = Depends(get_quality_service)
):
    """获取质量问题的资产列表"""
    try:
        return service.get_quality_issues(threshold=threshold)
    except Exception as e:
        logger.error(f"Failed to get quality issues: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/quality/validate",
    summary="验证质量指标",
    tags=["Quality"]
)
async def validate_quality_metrics(
    metrics: Dict[str, Any],
    service: QualityService = Depends(get_quality_service)
):
    """验证质量指标格式"""
    try:
        return service.validate_quality_metrics(metrics)
    except Exception as e:
        logger.error(f"Failed to validate quality metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/metrics/{asset_id}",
    response_model=DataQualityMetrics,
    summary="获取数据质量指标",
    tags=["Quality"]
)
async def get_quality_metrics(
    asset_id: str,
    service: QualityService = Depends(get_quality_service)
):
    """获取数据质量指标（返回标准化的DataQualityMetrics）"""
    try:
        # 解析asset_id
        if ":" in asset_id:
            entity_type, entity_id = asset_id.split(":", 1)
        else:
            entity_type = "data_asset"
            entity_id = asset_id
        
        # 如果是data_asset，使用int ID
        if entity_type == "data_asset":
            try:
                asset_id_int = int(entity_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid asset_id format for data_asset")
            
            metrics_dict = service.get_quality_metrics(asset_id_int)
            if metrics_dict is None:
                raise HTTPException(status_code=404, detail="Data asset not found")
            
            # 转换为DataQualityMetrics
            return DataQualityMetrics.from_dict(metrics_dict)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported entity type: {entity_type}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/quality/checks/{asset_id}",
    response_model=QualityCheckResult,
    summary="执行质量检查",
    tags=["Quality"]
)
async def run_quality_check(
    asset_id: str,
    service: QualityService = Depends(get_quality_service)
):
    """执行质量检查（运行完整的质量评估）"""
    try:
        return service.run_quality_check(asset_id)
    except Exception as e:
        logger.error(f"Failed to run quality check: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality/dashboard",
    response_model=QualityDashboard,
    summary="质量监控仪表板",
    tags=["Quality"]
)
async def get_quality_dashboard(
    service: QualityService = Depends(get_quality_service)
):
    """获取质量监控仪表板数据"""
    try:
        return service.get_quality_dashboard()
    except Exception as e:
        logger.error(f"Failed to get quality dashboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

