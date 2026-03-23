"""
操作元数据模型
包含使用统计、变更历史等操作元数据
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from database.src.models.base import Base, TimestampMixin


class UsageStats(BaseModel):
    """使用统计"""
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    access_frequency: str = "unknown"  # daily, weekly, monthly, rarely
    access_users: List[str] = Field(default_factory=list)
    access_services: List[str] = Field(default_factory=list)
    query_patterns: List[Dict[str, Any]] = Field(default_factory=list)


class ChangeRecord(BaseModel):
    """变更记录"""
    change_type: str  # created, updated, deleted, schema_changed
    changed_by: Optional[str] = None
    changed_at: datetime
    change_description: Optional[str] = None
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None


class OperationalMetadata(Base):
    """操作元数据表"""
    __tablename__ = "operational_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(50), nullable=False, index=True)  # data_asset, ai_model, workflow等
    asset_id = Column(Integer, nullable=False, index=True)
    
    # 使用统计
    usage_stats = Column(JSON)  # UsageStats的JSON表示
    
    # 变更历史
    change_history = Column(JSON)  # List[ChangeRecord]的JSON表示
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, server_default='now()')
    updated_at = Column(DateTime, nullable=False, server_default='now()', onupdate='now()')


class OperationalMetadataSchema(BaseModel):
    """操作元数据Schema"""
    id: int
    asset_type: str
    asset_id: int
    usage_stats: Optional[UsageStats] = None
    change_history: List[ChangeRecord] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


