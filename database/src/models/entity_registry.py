"""
实体注册表模型
用于统一实体标识管理
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Index, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, Field

from database.src.models.base import Base, TimestampMixin


class EntityRegistry(Base, TimestampMixin):
    """实体注册表"""
    __tablename__ = "entity_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 统一实体标识
    entity_uri = Column(String(500), unique=True, nullable=False, index=True, comment="统一实体URI")
    domain = Column(String(50), nullable=False, index=True, comment="实体域（metadata, knowledge, sap, workflow）")
    entity_type = Column(String(50), nullable=False, index=True, comment="实体类型（data_asset, node, business_entity等）")
    
    # 服务内部标识
    internal_id = Column(String(255), nullable=False, comment="服务内部ID")
    service_name = Column(String(50), nullable=False, index=True, comment="所属服务名称")
    
    # 状态和元数据
    status = Column(String(20), nullable=False, default="active", index=True, comment="状态：active, deleted, merged")
    extra_metadata = Column(JSONB, comment="额外元数据")
    
    # 索引
    __table_args__ = (
        Index('idx_entity_uri', 'entity_uri'),
        Index('idx_domain_type', 'domain', 'entity_type'),
        Index('idx_service_internal', 'service_name', 'internal_id'),
        Index('idx_status', 'status'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "entity_uri": self.entity_uri,
            "domain": self.domain,
            "entity_type": self.entity_type,
            "internal_id": self.internal_id,
            "service_name": self.service_name,
            "status": self.status,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class EntityRegistryBase(BaseModel):
    """实体注册基础模型"""
    entity_uri: str = Field(..., description="统一实体URI")
    domain: str = Field(..., description="实体域")
    entity_type: str = Field(..., description="实体类型")
    internal_id: str = Field(..., description="服务内部ID")
    service_name: str = Field(..., description="所属服务名称")
    status: str = Field("active", description="状态")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class EntityRegistryCreate(EntityRegistryBase):
    """创建实体注册请求"""
    pass


class EntityRegistrySchema(EntityRegistryBase):
    """实体注册Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

