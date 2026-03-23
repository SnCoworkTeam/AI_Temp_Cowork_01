"""
数据质量模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from shared_libs.src.models.metadata_models import DataQualityMetrics, QualityLevel


class QualityCheckResult(BaseModel):
    """质量检查结果"""
    asset_id: str
    asset_type: str
    asset_name: str
    check_time: datetime
    status: str  # passed, failed, warning
    overall_score: float
    metrics: DataQualityMetrics
    checks: List[Dict[str, Any]]  # 各项检查结果
    issues: List[Dict[str, Any]]  # 发现的问题
    recommendations: List[str]  # 改进建议
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class QualityDashboard(BaseModel):
    """质量监控仪表板"""
    summary: Dict[str, Any]  # 总体统计
    quality_distribution: Dict[str, int]  # 质量分布（按等级）
    recent_checks: List[Dict[str, Any]]  # 最近检查记录
    top_issues: List[Dict[str, Any]]  # 主要问题
    trends: Dict[str, List[Dict[str, Any]]]  # 趋势数据
    assets_by_quality: Dict[str, List[Dict[str, Any]]]  # 按质量分组的资产
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

