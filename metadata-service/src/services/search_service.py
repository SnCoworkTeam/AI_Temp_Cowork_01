"""
元数据搜索服务
提供元数据的全文搜索和高级查询
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from ..models.data_asset import DataAsset, DataAssetSchema
from ..models.ai_model import AIModel, AIModelSchema
from ..models.business_entity import BusinessEntity, BusinessEntitySchema
from ..models.workflow_metadata import WorkflowMetadata, WorkflowMetadataSchema

logger = logging.getLogger(__name__)


class SearchService:
    """元数据搜索服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_all(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        全局搜索所有类型的元数据
        
        Args:
            query: 搜索关键词
            entity_types: 限制搜索的实体类型列表（data_asset, ai_model, business_entity, workflow）
            tags: 标签过滤
            skip: 跳过数量
            limit: 返回数量限制
            
        Returns:
            搜索结果字典
        """
        results = {
            "data_assets": [],
            "ai_models": [],
            "business_entities": [],
            "workflows": [],
            "total": 0
        }
        
        search_pattern = f"%{query}%"
        
        # 搜索数据资产
        if not entity_types or "data_asset" in entity_types:
            asset_query = self.db.query(DataAsset).filter(
                or_(
                    DataAsset.name.ilike(search_pattern),
                    DataAsset.display_name.ilike(search_pattern),
                    DataAsset.description.ilike(search_pattern),
                    DataAsset.source_system.ilike(search_pattern)
                )
            )
            
            if tags:
                asset_query = asset_query.filter(
                    func.jsonb_array_to_text(DataAsset.tags).ilike(search_pattern)
                )
            
            assets = asset_query.offset(skip).limit(limit).all()
            results["data_assets"] = [DataAssetSchema.model_validate(asset) for asset in assets]
        
        # 搜索AI模型
        if not entity_types or "ai_model" in entity_types:
            model_query = self.db.query(AIModel).filter(
                or_(
                    AIModel.name.ilike(search_pattern),
                    AIModel.display_name.ilike(search_pattern),
                    AIModel.description.ilike(search_pattern),
                    AIModel.framework.ilike(search_pattern)
                )
            )
            
            if tags:
                model_query = model_query.filter(
                    func.jsonb_array_to_text(AIModel.tags).ilike(search_pattern)
                )
            
            models = model_query.offset(skip).limit(limit).all()
            results["ai_models"] = [AIModelSchema.model_validate(model) for model in models]
        
        # 搜索业务实体
        if not entity_types or "business_entity" in entity_types:
            entity_query = self.db.query(BusinessEntity).filter(
                or_(
                    BusinessEntity.name.ilike(search_pattern),
                    BusinessEntity.display_name.ilike(search_pattern),
                    BusinessEntity.description.ilike(search_pattern),
                    BusinessEntity.business_definition.ilike(search_pattern)
                )
            )
            
            if tags:
                entity_query = entity_query.filter(
                    func.jsonb_array_to_text(BusinessEntity.tags).ilike(search_pattern)
                )
            
            entities = entity_query.offset(skip).limit(limit).all()
            results["business_entities"] = [BusinessEntitySchema.model_validate(entity) for entity in entities]
        
        # 搜索工作流
        if not entity_types or "workflow" in entity_types:
            workflow_query = self.db.query(WorkflowMetadata).filter(
                or_(
                    WorkflowMetadata.name.ilike(search_pattern),
                    WorkflowMetadata.display_name.ilike(search_pattern),
                    WorkflowMetadata.description.ilike(search_pattern),
                    WorkflowMetadata.category.ilike(search_pattern)
                )
            )
            
            if tags:
                workflow_query = workflow_query.filter(
                    func.jsonb_array_to_text(WorkflowMetadata.tags).ilike(search_pattern)
                )
            
            workflows = workflow_query.offset(skip).limit(limit).all()
            results["workflows"] = [WorkflowMetadataSchema.model_validate(workflow) for workflow in workflows]
        
        results["total"] = (
            len(results["data_assets"]) +
            len(results["ai_models"]) +
            len(results["business_entities"]) +
            len(results["workflows"])
        )
        
        return results
    
    def search_by_tags(
        self,
        tags: List[str],
        entity_types: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """按标签搜索"""
        results = {
            "data_assets": [],
            "ai_models": [],
            "business_entities": [],
            "workflows": [],
            "total": 0
        }
        
        # 这里简化处理，实际应该使用PostgreSQL的JSONB查询
        # 搜索数据资产
        if not entity_types or "data_asset" in entity_types:
            assets = self.db.query(DataAsset).offset(skip).limit(limit).all()
            for asset in assets:
                if asset.tags and any(tag in asset.tags for tag in tags):
                    results["data_assets"].append(DataAssetSchema.model_validate(asset))
        
        # 搜索AI模型
        if not entity_types or "ai_model" in entity_types:
            models = self.db.query(AIModel).offset(skip).limit(limit).all()
            for model in models:
                if model.tags and any(tag in model.tags for tag in tags):
                    results["ai_models"].append(AIModelSchema.model_validate(model))
        
        # 搜索业务实体
        if not entity_types or "business_entity" in entity_types:
            entities = self.db.query(BusinessEntity).offset(skip).limit(limit).all()
            for entity in entities:
                if entity.tags and any(tag in entity.tags for tag in tags):
                    results["business_entities"].append(BusinessEntitySchema.model_validate(entity))
        
        # 搜索工作流
        if not entity_types or "workflow" in entity_types:
            workflows = self.db.query(WorkflowMetadata).offset(skip).limit(limit).all()
            for workflow in workflows:
                if workflow.tags and any(tag in workflow.tags for tag in tags):
                    results["workflows"].append(WorkflowMetadataSchema.model_validate(workflow))
        
        results["total"] = (
            len(results["data_assets"]) +
            len(results["ai_models"]) +
            len(results["business_entities"]) +
            len(results["workflows"])
        )
        
        return results
    
    def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门标签"""
        # 这里简化实现，实际应该聚合所有实体的标签
        tags_count = {}
        
        # 从数据资产收集标签
        assets = self.db.query(DataAsset).all()
        for asset in assets:
            if asset.tags:
                for tag in asset.tags:
                    tags_count[tag] = tags_count.get(tag, 0) + 1
        
        # 从AI模型收集标签
        models = self.db.query(AIModel).all()
        for model in models:
            if model.tags:
                for tag in model.tags:
                    tags_count[tag] = tags_count.get(tag, 0) + 1
        
        # 排序并返回
        sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)
        return [{"tag": tag, "count": count} for tag, count in sorted_tags[:limit]]

