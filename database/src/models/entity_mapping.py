"""
实体映射模型
用于映射knowledge-base和metadata-service的实体
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from database.src.models.base import Base, TimestampMixin


class EntityMapping(Base, TimestampMixin):
    """实体映射表"""
    __tablename__ = "entity_mappings"
    __table_args__ = (
        Index('idx_source_uri', 'source_uri'),
        Index('idx_target_uri', 'target_uri'),
        Index('idx_source_target', 'source_uri', 'target_uri'),
        Index('idx_status', 'status'),
        {'extend_existing': True},
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 源实体（knowledge-base）
    source_uri = Column(String(500), nullable=False, index=True, comment="源实体URI")
    source_type = Column(String(50), nullable=False, comment="源实体类型")
    source_id = Column(String(255), nullable=False, comment="源实体ID")
    
    # 目标实体（metadata-service）
    target_uri = Column(String(500), nullable=False, index=True, comment="目标实体URI")
    target_type = Column(String(50), nullable=False, comment="目标实体类型")
    target_id = Column(String(255), nullable=False, comment="目标实体ID")
    
    # 映射信息
    mapping_type = Column(String(50), nullable=False, default="auto", comment="映射类型：auto, manual, similarity")
    confidence = Column(Float, nullable=False, default=0.0, comment="映射置信度（0-1）")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending, confirmed, rejected")
    
    # 映射时间
    mapped_at = Column(DateTime, default=func.now(), nullable=False, comment="映射时间")
    
    def to_dict(self):
        return {
            "id": self.id,
            "source_uri": self.source_uri,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_uri": self.target_uri,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "mapping_type": self.mapping_type,
            "confidence": self.confidence,
            "status": self.status,
            "mapped_at": self.mapped_at.isoformat() if self.mapped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EntityMappingBase(BaseModel):
    """实体映射基础模型"""
    source_uri: str = Field(..., description="源实体URI")
    target_uri: str = Field(..., description="目标实体URI")
    mapping_type: str = Field("auto", description="映射类型")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="映射置信度")
    status: str = Field("pending", description="状态")


class EntityMappingCreate(EntityMappingBase):
    """创建实体映射请求"""
    source_type: str = Field(..., description="源实体类型")
    source_id: str = Field(..., description="源实体ID")
    target_type: str = Field(..., description="目标实体类型")
    target_id: str = Field(..., description="目标实体ID")


class EntityMappingSchema(EntityMappingBase):
    """实体映射Schema"""
    id: int
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    mapped_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True




