"""
分类体系迁移工具
将现有分类数据迁移到新的三层分类体系
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.data_asset import DataAsset
from ..models.ai_model import AIModel
from ..models.workflow_metadata import WorkflowMetadata
from ..models.business_entity import BusinessEntity

logger = logging.getLogger(__name__)


class ClassificationMigrationTool:
    """分类体系迁移工具"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def migrate_data_asset(self, asset: DataAsset) -> Dict[str, Any]:
        """
        迁移数据资产的分类信息
        
        迁移规则：
        1. 主分类：从classification字段获取，如果没有则从asset_type推断
        2. 业务维度：从metadata中的domain提取，或从source_system推断
        3. 技术维度：从source_system提取
        4. 生命周期：从status推断
        5. 治理维度：从classification字段推断（如果是pii, confidential等）
        6. 标准化标签：从tags字段提取并标准化
        """
        dimensions: Dict[str, Any] = {}
        
        # 1. 主分类
        primary = asset.classification
        if not primary:
            # 从asset_type推断
            type_map = {
                'dataset': 'analytical_data',
                'table': 'transaction_data',
                'view': 'analytical_data',
                'file': 'operational_data',
                'stream': 'operational_data',
                'api': 'operational_data'
            }
            primary = type_map.get(asset.asset_type.value, 'operational_data')
        
        if primary:
            dimensions['primary'] = primary
        
        # 2. 业务维度
        business_dim: Dict[str, Any] = {}
        if asset.extra_metadata and isinstance(asset.extra_metadata, dict):
            if 'domain' in asset.extra_metadata:
                business_dim['domain'] = asset.extra_metadata['domain']
        
        # 从source_system推断业务领域（简单映射）
        if asset.source_system:
            source_to_domain = {
                'SAP': 'finance',
                'Oracle': 'finance',
                'Salesforce': 'sales',
                'Workday': 'hr'
            }
            for source, domain in source_to_domain.items():
                if source in asset.source_system.upper():
                    business_dim['domain'] = domain
                    break
        
        if business_dim:
            dimensions['business'] = business_dim
        
        # 3. 技术维度
        technical_dim: Dict[str, Any] = {}
        if asset.source_system:
            # 标准化source_system值
            source_lower = asset.source_system.lower()
            if 'sap' in source_lower:
                technical_dim['source'] = 'sap'
            elif 'oracle' in source_lower:
                technical_dim['source'] = 'oracle_erp'
            elif 'salesforce' in source_lower:
                technical_dim['source'] = 'salesforce'
            elif 'database' in source_lower or 'db' in source_lower:
                technical_dim['source'] = 'database'
            elif 'api' in source_lower:
                technical_dim['source'] = 'api'
            else:
                technical_dim['source'] = 'custom'
        
        # 从asset_type推断数据格式
        if asset.asset_type:
            if asset.asset_type.value in ['table', 'view', 'dataset']:
                technical_dim['format'] = 'structured'
            elif asset.asset_type.value in ['file']:
                technical_dim['format'] = 'unstructured'
            elif asset.asset_type.value in ['stream']:
                technical_dim['format'] = 'semi_structured'
        
        if technical_dim:
            dimensions['technical'] = technical_dim
        
        # 4. 生命周期维度
        lifecycle_dim: Dict[str, Any] = {}
        if asset.status:
            status_map = {
                'active': 'production',
                'deprecated': 'archive',
                'archived': 'archive'
            }
            lifecycle_dim['stage'] = status_map.get(asset.status.value, 'production')
        
        if asset.update_frequency:
            lifecycle_dim['freshness'] = asset.update_frequency.lower()
        
        if lifecycle_dim:
            dimensions['lifecycle'] = lifecycle_dim
        
        # 5. 治理维度
        governance_dim: Dict[str, Any] = {}
        if asset.classification:
            classification_lower = asset.classification.lower()
            if 'pii' in classification_lower or 'confidential' in classification_lower:
                governance_dim['security'] = 'confidential'
            elif 'public' in classification_lower:
                governance_dim['security'] = 'public'
            else:
                governance_dim['security'] = 'internal'
        
        if asset.data_quality_metrics and isinstance(asset.data_quality_metrics, dict):
            quality_score = asset.data_quality_metrics.get('quality_score', 0)
            if quality_score >= 0.9:
                governance_dim['quality'] = 'certified'
            elif quality_score >= 0.7:
                governance_dim['quality'] = 'validated'
            else:
                governance_dim['quality'] = 'unverified'
        
        if governance_dim:
            dimensions['governance'] = governance_dim
        
        # 6. 标准化标签
        standardized_tags: List[str] = []
        if asset.tags and isinstance(asset.tags, list):
            for tag in asset.tags:
                if isinstance(tag, str):
                    # 标准化标签（添加前缀或直接使用）
                    standardized_tag = self._standardize_tag(tag)
                    if standardized_tag and standardized_tag not in standardized_tags:
                        standardized_tags.append(standardized_tag)
        
        return {
            'classification_dimensions': dimensions if dimensions else None,
            'standardized_tags': standardized_tags if standardized_tags else None
        }
    
    def migrate_ai_model(self, model: AIModel) -> Dict[str, Any]:
        """迁移AI模型的分类信息"""
        dimensions: Dict[str, Any] = {}
        
        # 1. 主分类：使用model_type
        dimensions['primary'] = model.model_type.value
        
        # 2. 技术维度
        technical_dim: Dict[str, Any] = {}
        if model.framework:
            framework_lower = model.framework.lower()
            if 'pytorch' in framework_lower:
                technical_dim['framework'] = 'pytorch'
            elif 'tensorflow' in framework_lower:
                technical_dim['framework'] = 'tensorflow'
            elif 'huggingface' in framework_lower:
                technical_dim['framework'] = 'huggingface'
            elif 'sklearn' in framework_lower or 'scikit' in framework_lower:
                technical_dim['framework'] = 'scikit_learn'
            else:
                technical_dim['framework'] = 'custom'
        
        if technical_dim:
            dimensions['technical'] = technical_dim
        
        # 3. 生命周期维度
        lifecycle_dim: Dict[str, Any] = {}
        if model.status:
            lifecycle_dim['status'] = model.status.value
        
        if lifecycle_dim:
            dimensions['lifecycle'] = lifecycle_dim
        
        # 4. 标准化标签
        standardized_tags: List[str] = []
        if model.tags and isinstance(model.tags, list):
            for tag in model.tags:
                if isinstance(tag, str):
                    standardized_tag = self._standardize_tag(tag)
                    if standardized_tag and standardized_tag not in standardized_tags:
                        standardized_tags.append(standardized_tag)
        
        return {
            'classification_dimensions': dimensions if dimensions else None,
            'standardized_tags': standardized_tags if standardized_tags else None
        }
    
    def migrate_workflow(self, workflow: WorkflowMetadata) -> Dict[str, Any]:
        """迁移工作流的分类信息"""
        dimensions: Dict[str, Any] = {}
        
        # 1. 主分类：使用workflow_type或category
        primary = workflow.workflow_type or workflow.category
        if primary:
            dimensions['primary'] = primary
        
        # 2. 业务维度：从category推断
        if workflow.category:
            category_lower = workflow.category.lower()
            business_dim: Dict[str, Any] = {}
            
            if 'data' in category_lower and 'quality' in category_lower:
                business_dim['domain'] = 'data_quality'
            elif 'ml' in category_lower or 'model' in category_lower:
                business_dim['domain'] = 'ml_training'
            elif 'integration' in category_lower:
                business_dim['domain'] = 'data_integration'
            
            if business_dim:
                dimensions['business'] = business_dim
        
        # 3. 标准化标签
        standardized_tags: List[str] = []
        if workflow.tags and isinstance(workflow.tags, list):
            for tag in workflow.tags:
                if isinstance(tag, str):
                    standardized_tag = self._standardize_tag(tag)
                    if standardized_tag and standardized_tag not in standardized_tags:
                        standardized_tags.append(standardized_tag)
        
        return {
            'classification_dimensions': dimensions if dimensions else None,
            'standardized_tags': standardized_tags if standardized_tags else None
        }
    
    def migrate_business_entity(self, entity: BusinessEntity) -> Dict[str, Any]:
        """迁移业务实体的分类信息"""
        dimensions: Dict[str, Any] = {}
        
        # 1. 主分类：使用entity_type
        dimensions['primary'] = entity.entity_type.value
        
        # 2. 业务维度：从classification或metadata提取
        if entity.classification:
            # 尝试从classification推断业务领域
            classification_lower = entity.classification.lower()
            business_dim: Dict[str, Any] = {}
            
            domain_keywords = {
                'finance': ['finance', 'financial', '财务'],
                'sales': ['sales', '销售'],
                'hr': ['hr', 'human', 'resource', '人力资源'],
                'operations': ['operation', '运营']
            }
            
            for domain, keywords in domain_keywords.items():
                if any(keyword in classification_lower for keyword in keywords):
                    business_dim['domain'] = domain
                    break
            
            if business_dim:
                dimensions['business'] = business_dim
        
        # 3. 标准化标签
        standardized_tags: List[str] = []
        if entity.tags and isinstance(entity.tags, list):
            for tag in entity.tags:
                if isinstance(tag, str):
                    standardized_tag = self._standardize_tag(tag)
                    if standardized_tag and standardized_tag not in standardized_tags:
                        standardized_tags.append(standardized_tag)
        
        return {
            'classification_dimensions': dimensions if dimensions else None,
            'standardized_tags': standardized_tags if standardized_tags else None
        }
    
    def _standardize_tag(self, tag: str) -> Optional[str]:
        """标准化标签"""
        if not tag:
            return None
        
        tag_lower = tag.lower().strip()
        
        # 标签映射规则
        tag_mapping = {
            'critical': 'biz:critical',
            'high_volume': 'biz:high_volume',
            'real_time': 'biz:real_time',
            'financial': 'biz:financial_reporting',
            'regulatory': 'biz:regulatory_required',
            'customer': 'biz:customer_facing',
            'gdpr': 'gov:gdpr',
            'pii': 'gov:pii',
            'high_performance': 'tech:high_performance',
            'scalable': 'tech:scalable',
            'cloud': 'tech:cloud_native'
        }
        
        # 检查是否匹配映射
        for key, value in tag_mapping.items():
            if key in tag_lower:
                return value
        
        # 如果没有匹配，返回原标签（小写）
        return tag_lower
    
    def migrate_all(self, batch_size: int = 100, dry_run: bool = True) -> Dict[str, Any]:
        """
        迁移所有元数据的分类信息
        
        Args:
            batch_size: 每批处理的记录数
            dry_run: 是否为试运行（不实际更新数据库）
        
        Returns:
            迁移统计信息
        """
        stats = {
            'data_assets': {'total': 0, 'migrated': 0, 'errors': 0},
            'ai_models': {'total': 0, 'migrated': 0, 'errors': 0},
            'workflows': {'total': 0, 'migrated': 0, 'errors': 0},
            'business_entities': {'total': 0, 'migrated': 0, 'errors': 0}
        }
        
        try:
            # 迁移数据资产
            logger.info("开始迁移数据资产...")
            data_assets = self.db.query(DataAsset).all()
            stats['data_assets']['total'] = len(data_assets)
            
            for asset in data_assets:
                try:
                    migration_data = self.migrate_data_asset(asset)
                    if not dry_run:
                        asset.classification_dimensions = migration_data['classification_dimensions']
                        asset.standardized_tags = migration_data['standardized_tags']
                        self.db.add(asset)
                    stats['data_assets']['migrated'] += 1
                except Exception as e:
                    logger.error(f"迁移数据资产 {asset.id} 失败: {e}")
                    stats['data_assets']['errors'] += 1
            
            # 迁移AI模型
            logger.info("开始迁移AI模型...")
            ai_models = self.db.query(AIModel).all()
            stats['ai_models']['total'] = len(ai_models)
            
            for model in ai_models:
                try:
                    migration_data = self.migrate_ai_model(model)
                    if not dry_run:
                        model.classification_dimensions = migration_data['classification_dimensions']
                        model.standardized_tags = migration_data['standardized_tags']
                        self.db.add(model)
                    stats['ai_models']['migrated'] += 1
                except Exception as e:
                    logger.error(f"迁移AI模型 {model.id} 失败: {e}")
                    stats['ai_models']['errors'] += 1
            
            # 迁移工作流
            logger.info("开始迁移工作流...")
            workflows = self.db.query(WorkflowMetadata).all()
            stats['workflows']['total'] = len(workflows)
            
            for workflow in workflows:
                try:
                    migration_data = self.migrate_workflow(workflow)
                    if not dry_run:
                        workflow.classification_dimensions = migration_data['classification_dimensions']
                        workflow.standardized_tags = migration_data['standardized_tags']
                        self.db.add(workflow)
                    stats['workflows']['migrated'] += 1
                except Exception as e:
                    logger.error(f"迁移工作流 {workflow.id} 失败: {e}")
                    stats['workflows']['errors'] += 1
            
            # 迁移业务实体
            logger.info("开始迁移业务实体...")
            business_entities = self.db.query(BusinessEntity).all()
            stats['business_entities']['total'] = len(business_entities)
            
            for entity in business_entities:
                try:
                    migration_data = self.migrate_business_entity(entity)
                    if not dry_run:
                        entity.classification_dimensions = migration_data['classification_dimensions']
                        entity.standardized_tags = migration_data['standardized_tags']
                        self.db.add(entity)
                    stats['business_entities']['migrated'] += 1
                except Exception as e:
                    logger.error(f"迁移业务实体 {entity.id} 失败: {e}")
                    stats['business_entities']['errors'] += 1
            
            if not dry_run:
                self.db.commit()
                logger.info("迁移完成并已提交到数据库")
            else:
                logger.info("试运行完成，未实际更新数据库")
            
        except Exception as e:
            logger.error(f"迁移过程出错: {e}", exc_info=True)
            if not dry_run:
                self.db.rollback()
            raise
        
        return stats








