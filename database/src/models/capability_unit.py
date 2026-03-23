"""
能力单元相关数据模型
用于企业语义能力图谱
"""
from sqlalchemy import (
    Column, String, Text, DateTime, Index, Integer, Float
)
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, TimestampMixin


class CapabilityUnit(Base, TimestampMixin):
    """能力单元表"""
    __tablename__ = "capability_units"
    
    # 主键
    id = Column(String(255), primary_key=True, comment="能力单元ID，格式：component:system:name 或 agent:name")
    
    # 基本信息
    name = Column(String(200), nullable=False, index=True, comment="能力单元名称")
    description = Column(Text, nullable=True, comment="能力单元描述")
    capability_type = Column(String(50), nullable=False, index=True, comment="能力类型：Component, Agent, Tool, API")
    
    # 技术属性
    version = Column(String(50), nullable=True, comment="版本号")
    endpoint = Column(String(500), nullable=True, comment="端点URL")
    input_schema = Column(JSONB, nullable=True, default=dict, comment="输入参数Schema")
    output_schema = Column(JSONB, nullable=True, default=dict, comment="输出结果Schema")
    
    # 性能指标
    reliability_score = Column(Float, default=0.0, nullable=False, comment="历史成功率（0.0-1.0）")
    avg_response_time = Column(Float, nullable=True, comment="平均响应时间（秒）")
    max_concurrent = Column(Integer, default=1, nullable=False, comment="最大并发数")
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")
    
    # 分类和标签
    tags = Column(JSONB, nullable=True, default=list, comment="标签列表")
    category = Column(String(100), nullable=True, index=True, comment="分类")
    
    # 元数据
    extra_metadata = Column(JSONB, nullable=True, default=dict, comment="额外元数据")
    
    # 索引
    __table_args__ = (
        Index('idx_capability_type', 'capability_type'),
        Index('idx_capability_category', 'category'),
        Index('idx_capability_reliability', 'reliability_score'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capability_type": self.capability_type,
            "version": self.version,
            "endpoint": self.endpoint,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "reliability_score": self.reliability_score,
            "avg_response_time": self.avg_response_time,
            "max_concurrent": self.max_concurrent,
            "usage_count": self.usage_count,
            "tags": self.tags,
            "category": self.category,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<CapabilityUnit(id={self.id}, name={self.name}, type={self.capability_type})>"




