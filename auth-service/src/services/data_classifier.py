"""
数据分类器
从metadata-service获取数据资产，基于敏感度和业务价值分类
支持结果持久化和自动更新
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.data_classification import DataClassificationResult

logger = logging.getLogger(__name__)


class DataClassifier:
    """数据分类器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def classify_data_assets(self, persist: bool = True) -> Dict[str, Any]:
        """
        从metadata-service获取数据资产，基于敏感度和业务价值分类
        
        Args:
            persist: 是否持久化分类结果到数据库
        
        Returns:
            分类结果
        """
        try:
            # 1. 获取数据资产
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/data-assets",
                params={"limit": 1000}
            )
            response.raise_for_status()
            assets_data = response.json()
            
            # 处理不同的响应格式
            if isinstance(assets_data, list):
                assets = assets_data
            elif isinstance(assets_data, dict):
                assets = assets_data.get("items", assets_data.get("data", []))
            else:
                assets = []
            
            # 2. 基于敏感度和业务价值分类
            classifications = {}
            persisted_count = 0
            
            for asset in assets:
                asset_id = asset.get("id")
                asset_name = asset.get("name", "")
                if asset_id:
                    classification = self._classify_asset(asset)
                    classifications[asset_id] = classification
                    
                    # 3. 持久化分类结果
                    if persist:
                        try:
                            self._persist_classification(asset_id, asset_name, classification)
                            persisted_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to persist classification for asset {asset_id}: {e}")
            
            # 4. 构建数据分类图谱
            classification_graph = self._build_classification_graph(classifications)
            
            return {
                "success": True,
                "classified_assets": len(classifications),
                "persisted_assets": persisted_count,
                "classification_graph": classification_graph,
                "classifications": classifications
            }
            
        except Exception as e:
            logger.error(f"Failed to classify data assets: {e}", exc_info=True)
            raise
    
    def _persist_classification(
        self,
        asset_id: int,
        asset_name: str,
        classification: Dict[str, Any]
    ):
        """持久化分类结果到数据库"""
        try:
            # 检查是否已存在该资产的最新分类
            existing = self.db.query(DataClassificationResult).filter(
                DataClassificationResult.asset_id == asset_id
            ).order_by(DataClassificationResult.classified_at.desc()).first()
            
            # 如果分类结果相同，不重复存储
            if existing and existing.sensitivity == classification.get("sensitivity") and \
               existing.business_value == classification.get("business_value"):
                logger.debug(f"Classification unchanged for asset {asset_id}, skipping persistence")
                return
            
            # 创建新的分类结果记录
            result = DataClassificationResult(
                asset_id=asset_id,
                asset_name=asset_name,
                sensitivity=classification.get("sensitivity", "low"),
                business_value=classification.get("business_value", "low"),
                classification=classification.get("classification"),
                domain=classification.get("domain"),
                quality_score=classification.get("quality_score"),
                classification_details=classification,
                classified_at=datetime.now()
            )
            
            self.db.add(result)
            self.db.commit()
            logger.info(f"Persisted classification for asset {asset_id}: {classification.get('sensitivity')}/{classification.get('business_value')}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to persist classification: {e}", exc_info=True)
            raise
    
    def get_classification_history(self, asset_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取资产分类历史"""
        try:
            results = self.db.query(DataClassificationResult).filter(
                DataClassificationResult.asset_id == asset_id
            ).order_by(DataClassificationResult.classified_at.desc()).limit(limit).all()
            
            return [result.to_dict() for result in results]
        except Exception as e:
            logger.error(f"Failed to get classification history: {e}", exc_info=True)
            return []
    
    def get_latest_classifications(
        self,
        sensitivity: Optional[str] = None,
        business_value: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取最新分类结果"""
        try:
            query = self.db.query(DataClassificationResult)
            
            # 构建子查询：获取每个资产的最新分类
            from sqlalchemy import func
            subquery = self.db.query(
                DataClassificationResult.asset_id,
                func.max(DataClassificationResult.classified_at).label('max_date')
            ).group_by(DataClassificationResult.asset_id).subquery()
            
            query = query.join(
                subquery,
                (DataClassificationResult.asset_id == subquery.c.asset_id) &
                (DataClassificationResult.classified_at == subquery.c.max_date)
            )
            
            if sensitivity:
                query = query.filter(DataClassificationResult.sensitivity == sensitivity)
            if business_value:
                query = query.filter(DataClassificationResult.business_value == business_value)
            
            results = query.order_by(DataClassificationResult.classified_at.desc()).limit(limit).all()
            return [result.to_dict() for result in results]
        except Exception as e:
            logger.error(f"Failed to get latest classifications: {e}", exc_info=True)
            return []
    
    def _classify_asset(self, asset: Dict) -> Dict[str, Any]:
        """分类单个资产"""
        # 基于classification、quality_score、domain分类
        classification = asset.get("classification", "public")
        quality_metrics = asset.get("data_quality_metrics", {})
        quality_score = quality_metrics.get("quality_score", 0.5) if isinstance(quality_metrics, dict) else 0.5
        metadata = asset.get("metadata", {}) or asset.get("extra_metadata", {})
        domain = metadata.get("domain", "unknown") if isinstance(metadata, dict) else "unknown"
        
        # 计算敏感度
        sensitivity = self._calculate_sensitivity(classification, quality_score)
        
        # 计算业务价值
        business_value = self._calculate_business_value(quality_score, domain)
        
        return {
            "sensitivity": sensitivity,  # "low", "medium", "high", "critical"
            "business_value": business_value,  # "low", "medium", "high"
            "classification": classification,
            "domain": domain,
            "quality_score": quality_score
        }
    
    def _calculate_sensitivity(self, classification: str, quality_score: float) -> str:
        """计算敏感度"""
        classification_lower = classification.lower() if classification else "public"
        
        if classification_lower in ["confidential", "restricted", "secret"]:
            return "high"
        elif classification_lower in ["internal", "private"]:
            return "medium"
        elif classification_lower in ["public", "open"]:
            return "low"
        else:
            # 基于质量分数推断（高质量数据可能更敏感）
            if quality_score >= 0.8:
                return "medium"
            else:
                return "low"
    
    def _calculate_business_value(self, quality_score: float, domain: str) -> str:
        """计算业务价值"""
        # 基于质量分数和业务域
        if quality_score >= 0.8:
            return "high"
        elif quality_score >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _build_classification_graph(self, classifications: Dict) -> Dict[str, Any]:
        """构建数据分类图谱"""
        # 统计各分类的数量
        sensitivity_stats = {}
        business_value_stats = {}
        domain_stats = {}
        
        for asset_id, classification in classifications.items():
            sensitivity = classification.get("sensitivity", "low")
            business_value = classification.get("business_value", "low")
            domain = classification.get("domain", "unknown")
            
            sensitivity_stats[sensitivity] = sensitivity_stats.get(sensitivity, 0) + 1
            business_value_stats[business_value] = business_value_stats.get(business_value, 0) + 1
            domain_stats[domain] = domain_stats.get(domain, 0) + 1
        
        return {
            "sensitivity_distribution": sensitivity_stats,
            "business_value_distribution": business_value_stats,
            "domain_distribution": domain_stats,
            "total_assets": len(classifications)
        }
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()

