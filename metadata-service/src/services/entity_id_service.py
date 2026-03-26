"""
实体ID服务
提供统一实体ID的生成、验证和转换功能
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..utils.entity_uri import EntityURI, create_entity_uri, parse_entity_uri

logger = logging.getLogger(__name__)


class EntityIDService:
    """实体ID服务"""
    
    def __init__(self, db: Session):
        """
        初始化实体ID服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def generate_entity_uri(
        self,
        domain: str,
        entity_type: str,
        internal_id: str
    ) -> EntityURI:
        """
        生成统一实体URI
        
        Args:
            domain: 实体域（metadata, knowledge, sap, workflow）
            entity_type: 实体类型（data_asset, node, business_entity等）
            internal_id: 服务内部ID
        
        Returns:
            EntityURI对象
        """
        return create_entity_uri(
            domain=domain,
            entity_type=entity_type,
            entity_id=str(internal_id)
        )
    
    def validate_entity_uri(self, uri: str) -> bool:
        """
        验证实体URI格式
        
        Args:
            uri: 实体URI字符串
        
        Returns:
            是否有效
        """
        try:
            parse_entity_uri(uri)
            return True
        except ValueError:
            return False
    
    def parse_entity_uri(self, uri: str) -> Optional[EntityURI]:
        """
        解析实体URI
        
        Args:
            uri: 实体URI字符串
        
        Returns:
            EntityURI对象，如果无效返回None
        """
        try:
            return parse_entity_uri(uri)
        except ValueError as e:
            logger.warning(f"Invalid EntityURI: {uri}, error: {e}")
            return None
    
    def get_domain_from_uri(self, uri: str) -> Optional[str]:
        """从URI获取域"""
        entity_uri = self.parse_entity_uri(uri)
        return entity_uri.domain if entity_uri else None
    
    def get_entity_type_from_uri(self, uri: str) -> Optional[str]:
        """从URI获取实体类型"""
        entity_uri = self.parse_entity_uri(uri)
        return entity_uri.entity_type if entity_uri else None
    
    def get_internal_id_from_uri(self, uri: str) -> Optional[str]:
        """从URI获取内部ID"""
        entity_uri = self.parse_entity_uri(uri)
        return entity_uri.entity_id if entity_uri else None
    
    def convert_to_internal_id(
        self,
        uri: str,
        target_service: str
    ) -> Optional[Dict[str, Any]]:
        """
        将统一实体URI转换为目标服务的内部ID
        
        Args:
            uri: 统一实体URI
            target_service: 目标服务名称
        
        Returns:
            包含服务名称和内部ID的字典，如果无法转换返回None
        """
        entity_uri = self.parse_entity_uri(uri)
        if not entity_uri:
            return None
        
        # 如果URI已经是目标服务的，直接返回
        if entity_uri.domain == target_service:
            return {
                "service": target_service,
                "internal_id": entity_uri.entity_id,
                "entity_type": entity_uri.entity_type
            }
        
        # 否则需要查询实体注册表进行映射
        from database.src.models.entity_registry import EntityRegistry
        
        registry = self.db.query(EntityRegistry).filter(
            EntityRegistry.entity_uri == uri,
            EntityRegistry.service_name == target_service,
            EntityRegistry.status == "active"
        ).first()
        
        if registry:
            return {
                "service": target_service,
                "internal_id": registry.internal_id,
                "entity_type": registry.entity_type
            }
        
        return None

