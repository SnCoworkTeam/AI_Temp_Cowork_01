"""
业务实体元数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from database.src.models.base import Base, TimestampMixin


class EntityType(str, enum.Enum):
    """实体类型"""
    DOMAIN = "domain"
    CONCEPT = "concept"
    TERM = "term"
    GLOSSARY = "glossary"
    POLICY = "policy"
    RULE = "rule"


class BusinessEntity(Base, TimestampMixin):
    """业务实体元数据表"""
    __tablename__ = "business_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    # 使用native_enum=False和values_callable确保使用枚举值而不是名称
    entity_type = Column(SQLEnum(EntityType, native_enum=False, values_callable=lambda x: [e.value for e in EntityType]), nullable=False, index=True)
    
    # 层次结构
    parent_id = Column(Integer, ForeignKey("business_entities.id"), nullable=True)
    parent = relationship("BusinessEntity", remote_side=[id], backref="children")
    
    # 业务信息
    business_definition = Column(Text)  # 业务定义
    business_rules = Column(JSON)  # 业务规则
    data_dictionary = Column(JSON)  # 数据字典
    
    # 关联信息
    related_entities = Column(JSON)  # 关联实体ID列表
    related_data_assets = Column(JSON)  # 关联数据资产ID列表
    related_models = Column(JSON)  # 关联AI模型ID列表
    
    # 治理信息
    data_steward = Column(String(100))  # 数据管家
    business_owner = Column(String(100))
    classification = Column(String(50))  # 分类（主分类，保留向后兼容）
    tags = Column(JSON)  # 标签列表（旧字段，保留向后兼容）
    
    # 分类维度（新字段，支持三层分类体系）
    classification_dimensions = Column(JSON, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    standardized_tags = Column(JSON, nullable=True, comment='标准化标签列表')
    
    # 兼容属性：从新字段或旧字段获取主分类
    @property
    def primary_classification(self) -> Optional[str]:
        """从新字段或旧字段获取主分类"""
        if self.classification_dimensions and isinstance(self.classification_dimensions, dict):
            return self.classification_dimensions.get('primary')
        # 如果没有新字段，使用classification或entity_type作为主分类
        return self.classification or (self.entity_type.value if self.entity_type else None)
    
    # 元数据
    extra_metadata = Column("metadata", JSON)  # 使用 metadata 作为数据库列名


class BusinessEntitySchema(BaseModel):
    """业务实体Schema（API响应）"""
    id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    entity_type: EntityType
    parent_id: Optional[int] = None
    business_definition: Optional[str] = None
    business_rules: Optional[Dict[str, Any]] = None
    data_dictionary: Optional[Dict[str, Any]] = None
    related_entities: Optional[List[int]] = None
    related_data_assets: Optional[List[int]] = None
    related_models: Optional[List[int]] = None
    data_steward: Optional[str] = None
    business_owner: Optional[str] = None
    classification: Optional[str] = None  # 主分类，保留向后兼容
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BusinessEntityCreate(BaseModel):
    """创建业务实体请求"""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    entity_type: EntityType
    parent_id: Optional[int] = None
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    business_definition: Optional[str] = None
    business_rules: Optional[Dict[str, Any]] = None
    data_dictionary: Optional[Dict[str, Any]] = None
    related_entities: Optional[List[int]] = None
    related_data_assets: Optional[List[int]] = None
    related_models: Optional[List[int]] = None
    data_steward: Optional[str] = None
    business_owner: Optional[str] = None
    classification: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class BusinessEntityUpdate(BaseModel):
    """更新业务实体请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    business_definition: Optional[str] = None
    business_rules: Optional[Dict[str, Any]] = None
    data_dictionary: Optional[Dict[str, Any]] = None
    related_entities: Optional[List[int]] = None
    related_data_assets: Optional[List[int]] = None
    related_models: Optional[List[int]] = None
    data_steward: Optional[str] = None
    business_owner: Optional[str] = None
    classification: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")

