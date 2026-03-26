"""
业务活动相关数据模型
用于企业语义能力图谱
"""
from sqlalchemy import (
    Column, String, Text, DateTime, Index, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from .base import Base, TimestampMixin


class BusinessActivity(Base, TimestampMixin):
    """业务活动表（优化版 - 向量管理增强）"""
    __tablename__ = "business_activities"
    
    # 主键
    id = Column(String(255), primary_key=True, comment="活动ID，格式：activity:domain:name")
    
    # 基本信息
    name = Column(String(200), nullable=False, index=True, comment="活动名称")
    description = Column(Text, nullable=True, comment="活动描述")
    activity_type = Column(String(50), nullable=False, index=True, comment="活动类型：action, query, approval, notification")
    business_domain = Column(String(50), nullable=False, index=True, comment="业务领域：procurement, finance, warehouse等")
    
    # 业务属性
    success_criteria = Column(Text, nullable=True, comment="成功标准")
    prerequisites = Column(JSONB, nullable=True, default=list, comment="前置条件列表")
    estimated_time = Column(String(50), nullable=True, comment="预计时间")
    risk_level = Column(String(20), nullable=True, comment="风险等级：low, medium, high")
    owner_dept = Column(String(100), nullable=True, comment="责任部门")
    
    # 来源信息
    source_type = Column(String(50), nullable=True, comment="来源类型：document, log, conversation, code")
    source_id = Column(String(255), nullable=True, comment="来源ID")
    
    # ⚠️ 向量管理优化（解决向量更新不一致风险）
    vector_entity_uri = Column(String(500), nullable=False, index=True, comment="指向vector_coordinator的URI")
    embedding_snapshot = Column(JSONB, nullable=True, comment="快照向量（用于快速检索，可选）")
    embedding_version = Column(String(20), default="1.0", nullable=False, comment="向量版本")
    last_vectorized_at = Column(DateTime, nullable=True, comment="最后向量化时间")
    description_updated_at = Column(DateTime, nullable=True, comment="描述更新时间（用于触发向量更新）")
    
    # 多模态向量支持（预留）
    multi_modal_vectors = Column(JSONB, nullable=True, comment="多模态向量URI列表")
    
    # 元数据
    extra_metadata = Column(JSONB, nullable=True, default=dict, comment="额外元数据")
    
    # 索引
    __table_args__ = (
        Index('idx_activity_domain_type', 'business_domain', 'activity_type'),
        Index('idx_activity_vector_uri', 'vector_entity_uri'),
        Index('idx_activity_name', 'name'),
    )
    
    def needs_vector_update(self) -> bool:
        """检查是否需要更新向量"""
        if not self.last_vectorized_at:
            return True
        if self.description_updated_at and self.description_updated_at > self.last_vectorized_at:
            return True
        return False
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "activity_type": self.activity_type,
            "business_domain": self.business_domain,
            "success_criteria": self.success_criteria,
            "prerequisites": self.prerequisites,
            "estimated_time": self.estimated_time,
            "risk_level": self.risk_level,
            "owner_dept": self.owner_dept,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "vector_entity_uri": self.vector_entity_uri,
            "embedding_version": self.embedding_version,
            "last_vectorized_at": self.last_vectorized_at.isoformat() if self.last_vectorized_at else None,
            "description_updated_at": self.description_updated_at.isoformat() if self.description_updated_at else None,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<BusinessActivity(id={self.id}, name={self.name}, domain={self.business_domain})>"





