"""
数据质量服务
提供数据质量指标的管理和监控
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.data_asset import DataAsset, DataAssetSchema
from ..models.quality import QualityCheckResult, QualityDashboard
from shared_libs.src.models.metadata_models import DataQualityMetrics, QualityLevel, QualityScore

logger = logging.getLogger(__name__)


class QualityService:
    """数据质量服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_quality_metrics(
        self,
        asset_id: int,
        metrics: Dict[str, Any]
    ) -> Optional[DataAssetSchema]:
        """更新数据质量指标"""
        asset = self.db.query(DataAsset).filter(DataAsset.id == asset_id).first()
        if not asset:
            return None
        
        # 合并质量指标
        if asset.data_quality_metrics:
            asset.data_quality_metrics.update(metrics)
        else:
            asset.data_quality_metrics = metrics
        
        # 更新时间戳
        asset.last_updated = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(asset)
        return DataAssetSchema.model_validate(asset)
    
    def get_quality_metrics(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """获取数据质量指标"""
        asset = self.db.query(DataAsset).filter(DataAsset.id == asset_id).first()
        if not asset:
            return None
        
        return asset.data_quality_metrics or {}
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """获取质量摘要统计"""
        total_assets = self.db.query(func.count(DataAsset.id)).scalar()
        
        # 统计有质量指标的资产
        assets_with_metrics = self.db.query(DataAsset).filter(
            DataAsset.data_quality_metrics.isnot(None)
        ).count()
        
        # 统计各状态的资产
        active_assets = self.db.query(DataAsset).filter(
            DataAsset.status == "active"
        ).count()
        
        deprecated_assets = self.db.query(DataAsset).filter(
            DataAsset.status == "deprecated"
        ).count()
        
        # 计算平均质量分数（如果有）
        quality_scores = []
        assets = self.db.query(DataAsset).filter(
            DataAsset.data_quality_metrics.isnot(None)
        ).all()
        
        for asset in assets:
            if asset.data_quality_metrics and "quality_score" in asset.data_quality_metrics:
                try:
                    score = float(asset.data_quality_metrics["quality_score"])
                    quality_scores.append(score)
                except (ValueError, TypeError):
                    pass
        
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        return {
            "total_assets": total_assets,
            "assets_with_metrics": assets_with_metrics,
            "active_assets": active_assets,
            "deprecated_assets": deprecated_assets,
            "average_quality_score": avg_quality_score,
            "metrics_coverage": (
                assets_with_metrics / total_assets * 100 if total_assets > 0 else 0
            )
        }
    
    def get_quality_issues(self, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """获取质量问题的资产列表"""
        issues = []
        
        assets = self.db.query(DataAsset).filter(
            DataAsset.data_quality_metrics.isnot(None)
        ).all()
        
        for asset in assets:
            if asset.data_quality_metrics:
                quality_score = asset.data_quality_metrics.get("quality_score")
                if quality_score is not None:
                    try:
                        score = float(quality_score)
                        if score < threshold:
                            issues.append({
                                "asset_id": asset.id,
                                "asset_name": asset.name,
                                "display_name": asset.display_name,
                                "quality_score": score,
                                "metrics": asset.data_quality_metrics,
                                "status": asset.status.value if asset.status else None
                            })
                    except (ValueError, TypeError):
                        pass
        
        # 按质量分数排序
        issues.sort(key=lambda x: x.get("quality_score", 1.0))
        
        return issues
    
    def validate_quality_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """验证质量指标格式"""
        errors = []
        warnings = []
        
        # 检查必需字段
        if "quality_score" not in metrics:
            warnings.append("Missing quality_score field")
        
        # 验证质量分数范围
        if "quality_score" in metrics:
            try:
                score = float(metrics["quality_score"])
                if score < 0 or score > 1:
                    errors.append("quality_score must be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("quality_score must be a number")
        
        # 验证其他指标
        valid_metrics = [
            "completeness",
            "accuracy",
            "consistency",
            "timeliness",
            "validity",
            "uniqueness"
        ]
        
        for key in metrics:
            if key not in valid_metrics and key != "quality_score":
                warnings.append(f"Unknown metric: {key}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def run_quality_check(self, asset_id: str) -> QualityCheckResult:
        """执行质量检查"""
        # 解析asset_id
        if ":" in asset_id:
            entity_type, entity_id = asset_id.split(":", 1)
        else:
            entity_type = "data_asset"
            entity_id = asset_id
        
        # 目前只支持data_asset
        if entity_type != "data_asset":
            raise ValueError(f"Unsupported entity type: {entity_type}")
        
        try:
            asset_id_int = int(entity_id)
        except ValueError:
            raise ValueError(f"Invalid asset_id format: {entity_id}")
        
        # 获取资产
        asset = self.db.query(DataAsset).filter(DataAsset.id == asset_id_int).first()
        if not asset:
            raise ValueError(f"Data asset not found: {asset_id}")
        
        # 获取或初始化质量指标
        metrics_dict = asset.data_quality_metrics or {}
        
        # 转换为DataQualityMetrics
        try:
            metrics = DataQualityMetrics.from_dict(metrics_dict)
        except Exception as e:
            logger.warning(f"Failed to parse quality metrics, using defaults: {str(e)}")
            # 使用默认值
            metrics = DataQualityMetrics(
                completeness=0.0,
                accuracy=0.0,
                consistency=0.0,
                timeliness=0.0,
                validity=0.0,
                uniqueness=0.0,
                overall_score=0.0
            )
        
        # 执行各项检查
        checks = []
        issues = []
        recommendations = []
        
        # 检查完整性
        completeness_check = {
            "check_name": "completeness",
            "status": "passed" if metrics.completeness >= 0.8 else "failed",
            "value": metrics.completeness,
            "threshold": 0.8,
            "message": f"完整性: {metrics.completeness:.2%}"
        }
        checks.append(completeness_check)
        if metrics.completeness < 0.8:
            issues.append({
                "type": "completeness",
                "severity": "high" if metrics.completeness < 0.5 else "medium",
                "message": f"数据完整性不足: {metrics.completeness:.2%}",
                "recommendation": "检查数据源，确保所有必需字段都有值"
            })
            recommendations.append("提高数据完整性：检查数据源，补充缺失数据")
        
        # 检查准确性
        accuracy_check = {
            "check_name": "accuracy",
            "status": "passed" if metrics.accuracy >= 0.9 else "failed",
            "value": metrics.accuracy,
            "threshold": 0.9,
            "message": f"准确性: {metrics.accuracy:.2%}"
        }
        checks.append(accuracy_check)
        if metrics.accuracy < 0.9:
            issues.append({
                "type": "accuracy",
                "severity": "high" if metrics.accuracy < 0.7 else "medium",
                "message": f"数据准确性不足: {metrics.accuracy:.2%}",
                "recommendation": "验证数据准确性，检查数据验证规则"
            })
            recommendations.append("提高数据准确性：实施数据验证规则，定期审核数据")
        
        # 检查一致性
        consistency_check = {
            "check_name": "consistency",
            "status": "passed" if metrics.consistency >= 0.85 else "failed",
            "value": metrics.consistency,
            "threshold": 0.85,
            "message": f"一致性: {metrics.consistency:.2%}"
        }
        checks.append(consistency_check)
        if metrics.consistency < 0.85:
            issues.append({
                "type": "consistency",
                "severity": "medium",
                "message": f"数据一致性不足: {metrics.consistency:.2%}",
                "recommendation": "检查数据格式和标准，确保数据一致性"
            })
            recommendations.append("提高数据一致性：统一数据格式和标准")
        
        # 检查及时性
        timeliness_check = {
            "check_name": "timeliness",
            "status": "passed" if metrics.timeliness >= 0.8 else "warning",
            "value": metrics.timeliness,
            "threshold": 0.8,
            "message": f"及时性: {metrics.timeliness:.2%}"
        }
        checks.append(timeliness_check)
        if metrics.timeliness < 0.8:
            issues.append({
                "type": "timeliness",
                "severity": "low",
                "message": f"数据及时性不足: {metrics.timeliness:.2%}",
                "recommendation": "优化数据更新频率，确保数据及时更新"
            })
            recommendations.append("提高数据及时性：优化数据更新流程")
        
        # 检查有效性
        validity_check = {
            "check_name": "validity",
            "status": "passed" if metrics.validity >= 0.9 else "failed",
            "value": metrics.validity,
            "threshold": 0.9,
            "message": f"有效性: {metrics.validity:.2%}"
        }
        checks.append(validity_check)
        if metrics.validity < 0.9:
            issues.append({
                "type": "validity",
                "severity": "high" if metrics.validity < 0.7 else "medium",
                "message": f"数据有效性不足: {metrics.validity:.2%}",
                "recommendation": "实施数据验证规则，清理无效数据"
            })
            recommendations.append("提高数据有效性：实施严格的数据验证规则")
        
        # 检查唯一性
        uniqueness_check = {
            "check_name": "uniqueness",
            "status": "passed" if metrics.uniqueness >= 0.95 else "failed",
            "value": metrics.uniqueness,
            "threshold": 0.95,
            "message": f"唯一性: {metrics.uniqueness:.2%}"
        }
        checks.append(uniqueness_check)
        if metrics.uniqueness < 0.95:
            issues.append({
                "type": "uniqueness",
                "severity": "high" if metrics.uniqueness < 0.8 else "medium",
                "message": f"数据唯一性不足: {metrics.uniqueness:.2%}",
                "recommendation": "检查重复数据，实施去重策略"
            })
            recommendations.append("提高数据唯一性：识别并清理重复数据")
        
        # 确定总体状态
        failed_checks = [c for c in checks if c["status"] == "failed"]
        warning_checks = [c for c in checks if c["status"] == "warning"]
        
        if len(failed_checks) > 0:
            status = "failed"
        elif len(warning_checks) > 0:
            status = "warning"
        else:
            status = "passed"
        
        # 如果没有建议，添加通用建议
        if not recommendations:
            recommendations.append("数据质量良好，继续保持")
        
        return QualityCheckResult(
            asset_id=asset_id,
            asset_type=entity_type,
            asset_name=asset.name or asset_id,
            check_time=datetime.utcnow(),
            status=status,
            overall_score=metrics.overall_score,
            metrics=metrics,
            checks=checks,
            issues=issues,
            recommendations=recommendations,
            metadata={
                "asset_display_name": asset.display_name,
                "asset_type": asset.asset_type.value if asset.asset_type else None,
                "last_updated": asset.last_updated.isoformat() if asset.last_updated else None
            }
        )
    
    def get_quality_dashboard(self) -> QualityDashboard:
        """获取质量监控仪表板"""
        # 获取总体统计
        summary = self.get_quality_summary()
        
        # 获取所有资产的质量指标
        assets = self.db.query(DataAsset).filter(
            DataAsset.data_quality_metrics.isnot(None)
        ).all()
        
        # 按质量等级分组
        quality_distribution = {
            "excellent": 0,  # >= 0.9
            "good": 0,      # 0.7-0.9
            "fair": 0,      # 0.5-0.7
            "poor": 0      # < 0.5
        }
        
        assets_by_quality = {
            "excellent": [],
            "good": [],
            "fair": [],
            "poor": []
        }
        
        top_issues = []
        recent_checks = []
        
        for asset in assets:
            if asset.data_quality_metrics:
                score = asset.data_quality_metrics.get("overall_score")
                if score is not None:
                    try:
                        score_float = float(score)
                        
                        # 分类
                        if score_float >= 0.9:
                            quality_level = "excellent"
                        elif score_float >= 0.7:
                            quality_level = "good"
                        elif score_float >= 0.5:
                            quality_level = "fair"
                        else:
                            quality_level = "poor"
                        
                        quality_distribution[quality_level] += 1
                        
                        asset_info = {
                            "asset_id": asset.id,
                            "asset_name": asset.name,
                            "display_name": asset.display_name,
                            "quality_score": score_float,
                            "asset_type": asset.asset_type.value if asset.asset_type else None
                        }
                        assets_by_quality[quality_level].append(asset_info)
                        
                        # 收集问题资产
                        if score_float < 0.7:
                            top_issues.append({
                                "asset_id": asset.id,
                                "asset_name": asset.name,
                                "display_name": asset.display_name,
                                "quality_score": score_float,
                                "issues": self._identify_quality_issues(asset.data_quality_metrics)
                            })
                    except (ValueError, TypeError):
                        pass
        
        # 按质量分数排序问题资产
        top_issues.sort(key=lambda x: x.get("quality_score", 1.0))
        top_issues = top_issues[:10]  # 取前10个
        
        # 生成趋势数据（简化版，实际应该从历史数据中获取）
        trends = {
            "quality_score": [
                {"date": (datetime.utcnow() - timedelta(days=i)).isoformat(), "value": summary.get("average_quality_score", 0.0)}
                for i in range(7, 0, -1)
            ]
        }
        
        return QualityDashboard(
            summary=summary,
            quality_distribution=quality_distribution,
            recent_checks=recent_checks,
            top_issues=top_issues,
            trends=trends,
            assets_by_quality=assets_by_quality,
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "total_assets_analyzed": len(assets)
            }
        )
    
    def _identify_quality_issues(self, metrics: Dict[str, Any]) -> List[str]:
        """识别质量问题"""
        issues = []
        
        if metrics.get("completeness", 1.0) < 0.8:
            issues.append("完整性不足")
        if metrics.get("accuracy", 1.0) < 0.9:
            issues.append("准确性不足")
        if metrics.get("consistency", 1.0) < 0.85:
            issues.append("一致性不足")
        if metrics.get("validity", 1.0) < 0.9:
            issues.append("有效性不足")
        if metrics.get("uniqueness", 1.0) < 0.95:
            issues.append("唯一性不足")
        
        return issues

