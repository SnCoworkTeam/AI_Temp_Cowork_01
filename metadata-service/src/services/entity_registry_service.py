"""
实体注册服务
管理统一实体标识的注册、查询和生命周期
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database.src.models.entity_registry import (
    EntityRegistry,
    EntityRegistryCreate,
    EntityRegistrySchema
)
from ..utils.entity_uri import EntityURI, create_entity_uri

logger = logging.getLogger(__name__)


class EntityRegistryService:
    """实体注册服务"""
    
    def __init__(self, db: Session):
        """
        初始化实体注册服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def register_entity(
        self,
        domain: str,
        entity_type: str,
        internal_id: str,
        service_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EntityRegistrySchema:
        """
        注册实体
        
        Args:
            domain: 实体域
            entity_type: 实体类型
            internal_id: 服务内部ID
            service_name: 服务名称
            metadata: 额外元数据
        
        Returns:
            注册的实体信息
        """
        # 生成统一实体URI
        entity_uri = create_entity_uri(
            domain=domain,
            entity_type=entity_type,
            entity_id=internal_id
        )
        uri_string = entity_uri.to_string()
        
        # 检查是否已存在
        existing = self.db.query(EntityRegistry).filter(
            EntityRegistry.entity_uri == uri_string,
            EntityRegistry.status == "active"
        ).first()
        
        if existing:
            logger.info(f"Entity already registered: {uri_string}")
            return EntityRegistrySchema.model_validate(existing)
        
        # 创建新注册
        registry = EntityRegistry(
            entity_uri=uri_string,
            domain=domain,
            entity_type=entity_type,
            internal_id=str(internal_id),
            service_name=service_name,
            status="active",
            extra_metadata=metadata or {}
        )
        
        self.db.add(registry)
        self.db.commit()
        self.db.refresh(registry)
        
        logger.info(f"Registered entity: {uri_string}")
        return EntityRegistrySchema.model_validate(registry)
    
    def get_entity_by_uri(
        self,
        entity_uri: str
    ) -> Optional[EntityRegistrySchema]:
        """
        根据统一实体URI获取实体信息
        
        Args:
            entity_uri: 统一实体URI
        
        Returns:
            实体信息，如果不存在返回None
        """
        registry = self.db.query(EntityRegistry).filter(
            EntityRegistry.entity_uri == entity_uri,
            EntityRegistry.status == "active"
        ).first()
        
        if not registry:
            return None
        
        return EntityRegistrySchema.model_validate(registry)
    
    def get_entity_by_internal_id(
        self,
        service_name: str,
        internal_id: str
    ) -> Optional[EntityRegistrySchema]:
        """
        根据服务内部ID获取实体信息
        
        Args:
            service_name: 服务名称
            internal_id: 内部ID
        
        Returns:
            实体信息，如果不存在返回None
        """
        registry = self.db.query(EntityRegistry).filter(
            EntityRegistry.service_name == service_name,
            EntityRegistry.internal_id == str(internal_id),
            EntityRegistry.status == "active"
        ).first()
        
        if not registry:
            return None
        
        return EntityRegistrySchema.model_validate(registry)
    
    def list_entities(
        self,
        domain: Optional[str] = None,
        entity_type: Optional[str] = None,
        service_name: Optional[str] = None,
        status: str = "active",
        skip: int = 0,
        limit: int = 100
    ) -> List[EntityRegistrySchema]:
        """
        列出实体
        
        Args:
            domain: 实体域过滤
            entity_type: 实体类型过滤
            service_name: 服务名称过滤
            status: 状态过滤
            skip: 跳过数量
            limit: 返回数量限制
        
        Returns:
            实体列表
        """
        query = self.db.query(EntityRegistry).filter(
            EntityRegistry.status == status
        )
        
        if domain:
            query = query.filter(EntityRegistry.domain == domain)
        if entity_type:
            query = query.filter(EntityRegistry.entity_type == entity_type)
        if service_name:
            query = query.filter(EntityRegistry.service_name == service_name)
        
        registries = query.offset(skip).limit(limit).all()
        return [EntityRegistrySchema.model_validate(r) for r in registries]
    
    def update_entity_status(
        self,
        entity_uri: str,
        status: str
    ) -> Optional[EntityRegistrySchema]:
        """
        更新实体状态
        
        Args:
            entity_uri: 统一实体URI
            status: 新状态（active, deleted, merged）
        
        Returns:
            更新后的实体信息，如果不存在返回None
        """
        registry = self.db.query(EntityRegistry).filter(
            EntityRegistry.entity_uri == entity_uri
        ).first()
        
        if not registry:
            return None
        
        registry.status = status
        self.db.commit()
        self.db.refresh(registry)
        
        logger.info(f"Updated entity status: {entity_uri} -> {status}")
        return EntityRegistrySchema.model_validate(registry)
    
    def merge_entities(
        self,
        source_uri: str,
        target_uri: str
    ) -> Optional[EntityRegistrySchema]:
        """
        合并实体（将源实体合并到目标实体）
        
        Args:
            source_uri: 源实体URI
            target_uri: 目标实体URI
        
        Returns:
            目标实体信息，如果合并失败返回None
        """
        source_registry = self.db.query(EntityRegistry).filter(
            EntityRegistry.entity_uri == source_uri,
            EntityRegistry.status == "active"
        ).first()
        
        target_registry = self.db.query(EntityRegistry).filter(
            EntityRegistry.entity_uri == target_uri,
            EntityRegistry.status == "active"
        ).first()
        
        if not source_registry or not target_registry:
            logger.warning(f"Cannot merge: source or target not found")
            return None
        
        # 更新源实体状态为merged，并记录合并信息
        source_registry.status = "merged"
        source_registry.extra_metadata = source_registry.extra_metadata or {}
        source_registry.extra_metadata["merged_to"] = target_uri
        source_registry.extra_metadata["merged_at"] = datetime.now().isoformat()
        
        # 更新目标实体元数据，记录合并来源
        target_registry.extra_metadata = target_registry.extra_metadata or {}
        if "merged_from" not in target_registry.extra_metadata:
            target_registry.extra_metadata["merged_from"] = []
        target_registry.extra_metadata["merged_from"].append(source_uri)
        
        self.db.commit()
        self.db.refresh(target_registry)
        
        logger.info(f"Merged entity: {source_uri} -> {target_uri}")
        return EntityRegistrySchema.model_validate(target_registry)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取实体注册统计信息
        
        Returns:
            统计信息
        """
        total = self.db.query(EntityRegistry).filter(
            EntityRegistry.status == "active"
        ).count()
        
        by_domain = {}
        by_type = {}
        by_service = {}
        
        registries = self.db.query(EntityRegistry).filter(
            EntityRegistry.status == "active"
        ).all()
        
        for registry in registries:
            # 按域统计
            by_domain[registry.domain] = by_domain.get(registry.domain, 0) + 1
            
            # 按类型统计
            by_type[registry.entity_type] = by_type.get(registry.entity_type, 0) + 1
            
            # 按服务统计
            by_service[registry.service_name] = by_service.get(registry.service_name, 0) + 1
        
        return {
            "total": total,
            "by_domain": by_domain,
            "by_type": by_type,
            "by_service": by_service
        }

