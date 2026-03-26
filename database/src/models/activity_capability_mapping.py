"""
活动-能力映射相关数据模型
用于企业语义能力图谱
"""
from sqlalchemy import (
    Column, String, DateTime, Index, Integer, Float, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, TimestampMixin


class ActivityCapabilityMapping(Base, TimestampMixin):
    """活动-能力映射表"""
    __tablename__ = "activity_capability_mappings"
    
    # 主键
    id = Column(String(255), primary_key=True, comment="映射ID，格式：mapping:activity_id:capability_id")
    
    # 外键（引用业务活动和能力单元）
    activity_id = Column(String(255), nullable=False, index=True, comment="业务活动ID")
    capability_id = Column(String(255), nullable=False, index=True, comment="能力单元ID")
    
    # 映射属性
    mapping_type = Column(String(50), nullable=False, default="primary", comment="映射类型：primary, alternative, fallback")
    priority = Column(Integer, default=0, nullable=False, comment="优先级（数字越大优先级越高）")
    conditions = Column(JSONB, nullable=True, default=dict, comment="使用条件")
    
    # 性能指标
    success_rate = Column(Float, default=0.0, nullable=False, comment="使用该能力执行活动的成功率（0.0-1.0）")
    avg_execution_time = Column(Float, nullable=True, comment="平均执行时间（秒）")
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    
    # 置信度
    confidence = Column(Float, default=0.0, nullable=False, comment="映射置信度（0.0-1.0）")
    
    # 元数据
    extra_metadata = Column(JSONB, nullable=True, default=dict, comment="额外元数据")
    
    # 索引
    __table_args__ = (
        Index('idx_mapping_activity', 'activity_id'),
        Index('idx_mapping_capability', 'capability_id'),
        Index('idx_mapping_type', 'mapping_type'),
        Index('idx_mapping_activity_capability', 'activity_id', 'capability_id', unique=True),
        Index('idx_mapping_success_rate', 'success_rate'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "capability_id": self.capability_id,
            "mapping_type": self.mapping_type,
            "priority": self.priority,
            "conditions": self.conditions,
            "success_rate": self.success_rate,
            "avg_execution_time": self.avg_execution_time,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "confidence": self.confidence,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<ActivityCapabilityMapping(id={self.id}, activity={self.activity_id}, capability={self.capability_id}, type={self.mapping_type})>"




