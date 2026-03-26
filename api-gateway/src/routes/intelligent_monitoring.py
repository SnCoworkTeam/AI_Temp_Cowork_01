"""
智能化监控API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from ..services.intelligent_monitoring import IntelligentMonitoringService
import logging

router = APIRouter(prefix="/api/intelligent-monitoring", tags=["Intelligent Monitoring"])
logger = logging.getLogger(__name__)


class PerformanceAnalysisRequest(BaseModel):
    """性能分析请求"""
    metrics: Dict[str, Any] = Field(..., description="性能指标数据")
    time_range: Optional[Dict[str, str]] = Field(None, description="时间范围")


class PredictionRequest(BaseModel):
    """预测请求"""
    historical_data: List[Dict[str, Any]] = Field(..., description="历史数据")
    forecast_hours: int = Field(24, ge=1, le=168, description="预测时间范围（小时）")


@router.post("/analyze-performance", summary="分析性能数据")
async def analyze_performance(
    request: PerformanceAnalysisRequest
):
    """
    分析性能数据，生成优化建议
    """
    try:
        service = IntelligentMonitoringService()
        analysis = await service.analyze_performance(
            metrics=request.metrics,
            time_range=request.time_range
        )
        await service.close()
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-issues", summary="预测潜在问题")
async def predict_issues(
    request: PredictionRequest
):
    """
    基于历史数据预测潜在问题
    """
    try:
        service = IntelligentMonitoringService()
        predictions = await service.predict_issues(
            historical_data=request.historical_data,
            forecast_hours=request.forecast_hours
        )
        await service.close()
        
        return {
            "success": True,
            "predictions": predictions
        }
    except Exception as e:
        logger.error(f"Failed to predict issues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

