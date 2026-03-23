"""
统一实体标识符（EntityURI）
格式: entity://{domain}/{type}/{id}
"""
from typing import Optional
import re


class EntityURI:
    """统一实体标识符"""
    
    URI_PATTERN = re.compile(r'^entity://([^/]+)/([^/]+)/(.+)$')
    
    def __init__(self, domain: str, entity_type: str, entity_id: str):
        """
        初始化EntityURI
        
        Args:
            domain: 实体域（metadata, knowledge, sap, workflow等）
            entity_type: 实体类型（data_asset, node, business_entity等）
            entity_id: 实体ID（可以是Integer或UUID字符串）
        """
        if not domain or not entity_type or not entity_id:
            raise ValueError("domain, entity_type, and entity_id cannot be empty")
        
        self.domain = domain
        self.entity_type = entity_type
        self.entity_id = str(entity_id)  # 确保是字符串
    
    def to_string(self) -> str:
        """转换为字符串格式"""
        return f"entity://{self.domain}/{self.entity_type}/{self.entity_id}"
    
    @classmethod
    def from_string(cls, uri: str) -> 'EntityURI':
        """
        从字符串解析EntityURI
        
        Args:
            uri: 实体URI字符串，格式: entity://domain/type/id
        
        Returns:
            EntityURI对象
        
        Raises:
            ValueError: 如果URI格式无效
        """
        match = cls.URI_PATTERN.match(uri)
        if not match:
            raise ValueError(f"Invalid EntityURI format: {uri}. Expected format: entity://domain/type/id")
        
        domain, entity_type, entity_id = match.groups()
        return cls(domain=domain, entity_type=entity_type, entity_id=entity_id)
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __repr__(self) -> str:
        return f"EntityURI(domain='{self.domain}', type='{self.entity_type}', id='{self.entity_id}')"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, EntityURI):
            return False
        return (self.domain == other.domain and 
                self.entity_type == other.entity_type and 
                self.entity_id == other.entity_id)
    
    def __hash__(self) -> int:
        return hash((self.domain, self.entity_type, self.entity_id))
    
    @property
    def is_metadata(self) -> bool:
        """是否为元数据服务实体"""
        return self.domain == "metadata"
    
    @property
    def is_knowledge(self) -> bool:
        """是否为知识库服务实体"""
        return self.domain == "knowledge"
    
    @property
    def is_sap(self) -> bool:
        """是否为SAP实体"""
        return self.domain == "sap"
    
    @property
    def is_workflow(self) -> bool:
        """是否为工作流实体"""
        return self.domain == "workflow"


def create_entity_uri(domain: str, entity_type: str, entity_id: str) -> EntityURI:
    """
    创建EntityURI的便捷函数
    
    Args:
        domain: 实体域
        entity_type: 实体类型
        entity_id: 实体ID
    
    Returns:
        EntityURI对象
    """
    return EntityURI(domain=domain, entity_type=entity_type, entity_id=entity_id)


def parse_entity_uri(uri: str) -> EntityURI:
    """
    解析EntityURI字符串的便捷函数
    
    Args:
        uri: 实体URI字符串
    
    Returns:
        EntityURI对象
    """
    return EntityURI.from_string(uri)






