"""
数据质量规则引擎
定义和执行数据质量规则
支持指标向量化和规则执行
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.data_asset import DataAsset, DataAssetSchema
from ..models.quality_vector import QualityRuleVector

logger = logging.getLogger(__name__)


class QualityRule:
    """质量规则"""
    
    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        rule_type: str,  # completeness, uniqueness, consistency, accuracy
        description: str,
        validator_func
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.description = description
        self.validator_func = validator_func
    
    def validate(self, asset: DataAssetSchema) -> Dict[str, Any]:
        """
        验证规则
        
        Returns:
            验证结果字典，包含passed, message, details
        """
        try:
            result = self.validator_func(asset)
            return {
                "rule_id": self.rule_id,
                "rule_name": self.rule_name,
                "rule_type": self.rule_type,
                "passed": result.get("passed", False),
                "message": result.get("message", ""),
                "details": result.get("details", {}),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error validating rule {self.rule_id}: {e}", exc_info=True)
            return {
                "rule_id": self.rule_id,
                "rule_name": self.rule_name,
                "rule_type": self.rule_type,
                "passed": False,
                "message": f"Validation error: {str(e)}",
                "details": {},
                "timestamp": datetime.now().isoformat()
            }


class QualityRulesEngine:
    """质量规则引擎（增强版，支持向量化）"""
    
    def __init__(self, db: Optional[Session] = None):
        """初始化质量规则引擎"""
        self.db = db
        self.rules: List[QualityRule] = []
        self._embedding_model = None  # 懒加载embedding模型
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认质量规则"""
        
        # 完整性规则
        def completeness_validator(asset: DataAssetSchema) -> Dict[str, Any]:
            """验证完整性"""
            missing_fields = []
            
            if not asset.name:
                missing_fields.append("name")
            if not asset.asset_type:
                missing_fields.append("asset_type")
            if not asset.description:
                missing_fields.append("description")
            
            passed = len(missing_fields) == 0
            return {
                "passed": passed,
                "message": "完整性检查通过" if passed else f"缺少必需字段: {', '.join(missing_fields)}",
                "details": {"missing_fields": missing_fields}
            }
        
        self.add_rule(QualityRule(
            rule_id="completeness_001",
            rule_name="必需字段完整性",
            rule_type="completeness",
            description="必须包含技术名称、资产类型和描述",
            validator_func=completeness_validator
        ))
        
        # 一致性规则
        def consistency_validator(asset: DataAssetSchema) -> Dict[str, Any]:
            """验证一致性"""
            issues = []
            
            # 检查schema_info格式
            if asset.schema_info:
                if not isinstance(asset.schema_info, dict):
                    issues.append("schema_info必须是字典格式")
                elif asset.asset_type.value == "table" and "fields" not in asset.schema_info:
                    issues.append("表类型资产必须包含fields字段")
            
            # 检查分类一致性
            if asset.classification:
                valid_classifications = [
                    "sap_master_data_customer", "sap_master_data_vendor", "sap_master_data_material",
                    "sap_transaction_sales_order", "sap_transaction_purchase_order",
                    "sap_odata_entity", "sap_table"
                ]
                if asset.classification not in valid_classifications:
                    issues.append(f"分类 {asset.classification} 不在有效分类列表中")
            
            passed = len(issues) == 0
            return {
                "passed": passed,
                "message": "一致性检查通过" if passed else f"发现一致性问题: {', '.join(issues)}",
                "details": {"issues": issues}
            }
        
        self.add_rule(QualityRule(
            rule_id="consistency_001",
            rule_name="数据格式一致性",
            rule_type="consistency",
            description="数据类型和格式必须符合标准",
            validator_func=consistency_validator
        ))
        
        # 准确性规则
        def accuracy_validator(asset: DataAssetSchema) -> Dict[str, Any]:
            """验证准确性"""
            issues = []
            
            # 检查业务术语准确性
            if asset.source_system == "SAP":
                if asset.sap_table_name and not asset.sap_table_name.isupper():
                    issues.append("SAP表名应该为大写")
                
                # 检查ABAP字典信息
                if asset.schema_info and asset.schema_info.get("abap_dictionary"):
                    abap_dict = asset.schema_info["abap_dictionary"]
                    if not abap_dict.get("table_info"):
                        issues.append("ABAP字典信息不完整")
            
            passed = len(issues) == 0
            return {
                "passed": passed,
                "message": "准确性检查通过" if passed else f"发现准确性问题: {', '.join(issues)}",
                "details": {"issues": issues}
            }
        
        self.add_rule(QualityRule(
            rule_id="accuracy_001",
            rule_name="业务术语准确性",
            rule_type="accuracy",
            description="业务术语定义必须准确",
            validator_func=accuracy_validator
        ))
    
    def add_rule(self, rule: QualityRule):
        """添加质量规则"""
        self.rules.append(rule)
    
    def validate_asset(self, asset: DataAssetSchema) -> Dict[str, Any]:
        """
        验证数据资产
        
        Args:
            asset: 数据资产
            
        Returns:
            验证结果
        """
        results = []
        passed_count = 0
        failed_count = 0
        
        for rule in self.rules:
            result = rule.validate(asset)
            results.append(result)
            if result["passed"]:
                passed_count += 1
            else:
                failed_count += 1
        
        overall_passed = failed_count == 0
        
        return {
            "overall_passed": overall_passed,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "total_rules": len(self.rules),
            "results": results,
            "quality_score": passed_count / len(self.rules) if self.rules else 0.0
        }
    
    def get_quality_summary(self, assets: List[DataAssetSchema]) -> Dict[str, Any]:
        """
        获取质量摘要
        
        Args:
            assets: 数据资产列表
            
        Returns:
            质量摘要
        """
        total_assets = len(assets)
        passed_assets = 0
        failed_assets = 0
        total_quality_score = 0.0
        
        for asset in assets:
            result = self.validate_asset(asset)
            if result["overall_passed"]:
                passed_assets += 1
            else:
                failed_assets += 1
            total_quality_score += result["quality_score"]
        
        avg_quality_score = total_quality_score / total_assets if total_assets > 0 else 0.0
        
        return {
            "total_assets": total_assets,
            "passed_assets": passed_assets,
            "failed_assets": failed_assets,
            "pass_rate": passed_assets / total_assets if total_assets > 0 else 0.0,
            "average_quality_score": avg_quality_score
        }
    
    def _get_embedding_model(self):
        """懒加载embedding模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded embedding model for vectorization")
            except ImportError:
                logger.warning("sentence-transformers not installed, vectorization disabled")
                self._embedding_model = None
        return self._embedding_model
    
    async def vectorize_metrics(self, metrics: Dict[str, Any]) -> List[float]:
        """
        指标向量化存储
        
        Args:
            metrics: 质量指标字典
        
        Returns:
            向量表示
        """
        try:
            # 将指标转换为文本
            metrics_text = self._metrics_to_text(metrics)
            
            # 使用本地embedding模型，不依赖vector-coordinator
            model = self._get_embedding_model()
            if model:
                embedding = model.encode(metrics_text).tolist()
                return embedding
            else:
                logger.warning("Embedding model not available, returning empty vector")
                return []
            
        except Exception as e:
            logger.error(f"Failed to vectorize metrics: {e}", exc_info=True)
            return []
    
    def _metrics_to_text(self, metrics: Dict[str, Any]) -> str:
        """将指标转换为文本"""
        text_parts = []
        for key, value in metrics.items():
            text_parts.append(f"{key}: {value}")
        return " ".join(text_parts)
    
    async def execute_rules(self, asset_id: int, rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        规则执行和监控
        
        Args:
            asset_id: 资产ID
            rules: 规则列表（可选，不提供则执行所有规则）
        
        Returns:
            执行结果
        """
        try:
            if not self.db:
                raise ValueError("Database session required for execute_rules")
            
            # 获取资产质量指标
            from ..services.quality_service import QualityService
            quality_service = QualityService(self.db)
            metrics = quality_service.get_quality_metrics(asset_id)
            
            if not metrics:
                return {
                    "success": False,
                    "error": "No quality metrics found",
                    "asset_id": asset_id
                }
            
            # 获取资产信息
            from ..services.metadata_catalog import MetadataCatalogService
            catalog = MetadataCatalogService(self.db)
            asset = catalog.get_data_asset(asset_id)
            
            if not asset:
                return {
                    "success": False,
                    "error": "Asset not found",
                    "asset_id": asset_id
                }
            
            # 执行规则
            rule_list = rules or [rule.rule_id for rule in self.rules]
            results = []
            
            for rule_id in rule_list:
                rule = next((r for r in self.rules if r.rule_id == rule_id), None)
                if rule:
                    rule_result = rule.validate(asset)
                    results.append(rule_result)
                else:
                    results.append({
                        "rule_id": rule_id,
                        "passed": False,
                        "message": f"Rule {rule_id} not found",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 向量化指标（可选）
            vector = await self.vectorize_metrics(metrics)
            
            # 持久化向量（如果向量化成功）
            vector_id = None
            if vector and len(vector) > 0:
                try:
                    vector_id = await self._persist_vector(asset_id, metrics, vector, results)
                except Exception as e:
                    logger.warning(f"Failed to persist vector: {e}")
            
            return {
                "success": True,
                "asset_id": asset_id,
                "rules_executed": len(results),
                "results": results,
                "metrics_vector": vector if vector else None,
                "vector_id": vector_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute rules: {e}", exc_info=True)
            raise
    
    def _get_default_rules(self) -> List[str]:
        """获取默认规则列表"""
        return [rule.rule_id for rule in self.rules]
    
    async def _persist_vector(
        self,
        asset_id: int,
        metrics: Dict[str, Any],
        vector: List[float],
        rule_results: List[Dict[str, Any]]
    ) -> Optional[int]:
        """持久化质量规则向量"""
        try:
            if not self.db:
                return None
            
            # 将指标转换为文本
            metrics_text = self._metrics_to_text(metrics)
            
            # 创建向量记录
            vector_record = QualityRuleVector(
                asset_id=asset_id,
                rule_id="batch_execution",  # 批量执行时使用此ID
                vector=vector,
                vector_dimension=len(vector),
                metrics=metrics,
                metrics_text=metrics_text,
                rule_result={
                    "results": rule_results,
                    "total_rules": len(rule_results),
                    "passed_count": sum(1 for r in rule_results if r.get("passed", False)),
                    "failed_count": sum(1 for r in rule_results if not r.get("passed", False))
                },
                executed_at=datetime.now()
            )
            
            self.db.add(vector_record)
            self.db.commit()
            self.db.refresh(vector_record)
            
            logger.info(f"Persisted quality vector for asset {asset_id}, vector_id: {vector_record.id}")
            return vector_record.id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to persist vector: {e}", exc_info=True)
            return None
    
    def get_vector_history(self, asset_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取资产向量历史"""
        try:
            if not self.db:
                return []
            
            vectors = self.db.query(QualityRuleVector).filter(
                QualityRuleVector.asset_id == asset_id
            ).order_by(QualityRuleVector.executed_at.desc()).limit(limit).all()
            
            return [vec.to_dict() for vec in vectors]
        except Exception as e:
            logger.error(f"Failed to get vector history: {e}", exc_info=True)
            return []


