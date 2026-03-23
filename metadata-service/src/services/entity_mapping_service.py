"""
实体映射服务
用于映射knowledge-base和metadata-service的实体
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database.src.models.entity_mapping import (
    EntityMapping,
    EntityMappingCreate,
    EntityMappingSchema
)
from ..services.metadata_catalog import MetadataCatalogService

logger = logging.getLogger(__name__)


class EntityMappingService:
    """实体映射服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.catalog = MetadataCatalogService(db)
    
    async def auto_map_entities(
        self,
        similarity_threshold: float = 0.8
    ) -> List[EntityMappingSchema]:
        """
        自动映射实体
        
        基于名称相似度自动映射knowledge-base和metadata-service的实体
        
        Args:
            similarity_threshold: 相似度阈值（0-1），默认0.8
        
        Returns:
            创建的映射列表
        """
        try:
            # 1. 获取knowledge-base的实体
            kg_entities = await self._get_knowledge_base_entities()
            logger.info(f"Retrieved {len(kg_entities)} entities from knowledge-base")
            
            # 2. 获取metadata-service的业务实体
            be_entities = self._get_business_entities()
            logger.info(f"Retrieved {len(be_entities)} entities from metadata-service")
            
            # 3. 基于名称相似度自动映射
            mappings = []
            for kg_entity in kg_entities:
                kg_name = kg_entity.get("name", "").lower()
                kg_id = kg_entity.get("id")
                if not kg_id:
                    continue
                kg_uri = f"entity://knowledge/node/{kg_id}"
                
                for be_entity in be_entities:
                    be_name = be_entity.name.lower() if hasattr(be_entity, 'name') else ""
                    be_id = be_entity.id if hasattr(be_entity, 'id') else None
                    if not be_id:
                        continue
                    be_uri = f"entity://metadata/business_entity/{be_id}"
                    
                    # 计算名称相似度
                    similarity = self._calculate_name_similarity(kg_name, be_name)
                    
                    if similarity >= similarity_threshold:
                        # 检查是否已存在映射
                        existing = self.db.query(EntityMapping).filter(
                            or_(
                                and_(
                                    EntityMapping.source_uri == kg_uri,
                                    EntityMapping.target_uri == be_uri
                                ),
                                and_(
                                    EntityMapping.source_uri == be_uri,
                                    EntityMapping.target_uri == kg_uri
                                )
                            )
                        ).first()
                        
                        if not existing:
                            mapping = EntityMapping(
                                source_uri=kg_uri,
                                source_type="knowledge_graph_node",
                                source_id=str(kg_id),
                                target_uri=be_uri,
                                target_type="business_entity",
                                target_id=str(be_id),
                                mapping_type="auto",
                                confidence=similarity,
                                status="pending"
                            )
                            self.db.add(mapping)
                            mappings.append(mapping)
            
            self.db.commit()
            
            # 刷新并返回
            for mapping in mappings:
                self.db.refresh(mapping)
            
            logger.info(f"Created {len(mappings)} entity mappings")
            return [EntityMappingSchema.model_validate(m) for m in mappings]
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to auto map entities: {e}", exc_info=True)
            raise
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度（简单实现）"""
        if not name1 or not name2:
            return 0.0
        
        if name1 == name2:
            return 1.0
        
        # 包含关系
        if name1 in name2 or name2 in name1:
            return 0.8
        
        # 字符重叠度（Jaccard相似度）
        set1 = set(name1)
        set2 = set(name2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    async def _get_knowledge_base_entities(self) -> List[Dict[str, Any]]:
        """获取knowledge-base的实体"""
        try:
            # 尝试获取知识图谱节点
            response = await self.http_client.get(
                f"{self.knowledge_base_url}/api/ontology/concepts",
                params={"limit": 1000}
            )
            response.raise_for_status()
            data = response.json()
            
            # 处理不同的响应格式
            if isinstance(data, dict):
                return data.get("concepts", []) or data.get("results", []) or []
            elif isinstance(data, list):
                return data
            else:
                return []
        except httpx.HTTPStatusError as e:
            logger.warning(f"Failed to get knowledge-base entities: HTTP {e.response.status_code}")
            return []
        except Exception as e:
            logger.warning(f"Failed to get knowledge-base entities: {e}")
            return []
    
    def _get_business_entities(self) -> List:
        """获取metadata-service的业务实体"""
        try:
            entities = self.catalog.list_business_entities(limit=1000)
            return entities
        except Exception as e:
            logger.error(f"Failed to get business entities: {e}", exc_info=True)
            return []
    
    def get_mappings(
        self,
        source_uri: Optional[str] = None,
        target_uri: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[EntityMappingSchema]:
        """获取实体映射列表"""
        query = self.db.query(EntityMapping)
        
        if source_uri:
            query = query.filter(EntityMapping.source_uri == source_uri)
        if target_uri:
            query = query.filter(EntityMapping.target_uri == target_uri)
        if status:
            query = query.filter(EntityMapping.status == status)
        
        mappings = query.offset(skip).limit(limit).all()
        return [EntityMappingSchema.model_validate(m) for m in mappings]
    
    def create_mapping(self, mapping_data: EntityMappingCreate) -> EntityMappingSchema:
        """创建实体映射"""
        mapping = EntityMapping(**mapping_data.model_dump())
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return EntityMappingSchema.model_validate(mapping)
    
    def update_mapping_status(
        self,
        mapping_id: int,
        status: str
    ) -> Optional[EntityMappingSchema]:
        """更新映射状态"""
        mapping = self.db.query(EntityMapping).filter(
            EntityMapping.id == mapping_id
        ).first()
        
        if not mapping:
            return None
        
        mapping.status = status
        self.db.commit()
        self.db.refresh(mapping)
        return EntityMappingSchema.model_validate(mapping)
    
    async def trigger_immediate_mapping(
        self,
        entity_uri: str,
        entity_type: str
    ) -> List[EntityMappingSchema]:
        """
        为新创建的实体触发立即映射
        
        Args:
            entity_uri: 实体URI
            entity_type: 实体类型
        
        Returns:
            创建的映射列表
        """
        # 这是一个简化实现，实际应该根据实体类型和URI获取实体信息
        # 然后查找可能的映射目标
        logger.info(f"Triggering immediate mapping for {entity_uri} ({entity_type})")
        
        # TODO: 实现具体的映射逻辑
        # 1. 获取新实体信息
        # 2. 查找可能的映射目标
        # 3. 计算相似度并创建映射
        # 4. 刷新搜索缓存
        
        return []
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()








