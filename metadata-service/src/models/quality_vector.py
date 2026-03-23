"""
质量规则向量存储模型
"""
from sqlalchemy import Column, Integer, String, JSON, ARRAY, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.sql import func
from database.src.models.base import Base, TimestampMixin


class QualityRuleVector(Base, TimestampMixin):
    """质量规则向量表"""
    __tablename__ = "quality_rule_vectors"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, nullable=False, index=True, comment="数据资产ID")
    rule_id = Column(String(100), nullable=False, index=True, comment="规则ID")
    
    # 向量数据
    vector = Column(PG_ARRAY(Float), nullable=False, comment="质量指标向量（384维）")
    vector_dimension = Column(Integer, default=384, comment="向量维度")
    
    # 原始指标
    metrics = Column(JSON, comment="原始质量指标JSON")
    metrics_text = Column(String(1000), comment="指标文本表示")
    
    # 规则执行结果
    rule_result = Column(JSON, comment="规则执行结果JSON")
    
    # 执行时间
    executed_at = Column(DateTime, default=func.now(), nullable=False, comment="执行时间")
    
    # 索引
    __table_args__ = (
        Index('idx_asset_id_executed_at', 'asset_id', 'executed_at'),
        Index('idx_rule_id_executed_at', 'rule_id', 'executed_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "rule_id": self.rule_id,
            "vector": self.vector,
            "vector_dimension": self.vector_dimension,
            "metrics": self.metrics,
            "metrics_text": self.metrics_text,
            "rule_result": self.rule_result,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

