"""
数据分类结果模型
"""
from sqlalchemy import Column, Integer, String, JSON, Float, DateTime, Index
from sqlalchemy.sql import func
from database.src.models.base import Base, TimestampMixin


class DataClassificationResult(Base, TimestampMixin):
    """数据分类结果表"""
    __tablename__ = "data_classification_results"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, nullable=False, index=True, comment="数据资产ID")
    asset_name = Column(String(255), nullable=False, comment="数据资产名称")
    
    # 分类结果
    sensitivity = Column(String(50), nullable=False, index=True, comment="敏感度: low/medium/high/critical")
    business_value = Column(String(50), nullable=False, index=True, comment="业务价值: low/medium/high")
    classification = Column(String(100), comment="原始分类")
    domain = Column(String(100), comment="业务域")
    quality_score = Column(Float, comment="质量分数")
    
    # 分类详情
    classification_details = Column(JSON, comment="分类详情JSON")
    
    # 分类时间
    classified_at = Column(DateTime, default=func.now(), nullable=False, comment="分类时间")
    
    # 索引
    __table_args__ = (
        Index('idx_asset_id_classified_at', 'asset_id', 'classified_at'),
        Index('idx_sensitivity_business_value', 'sensitivity', 'business_value'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "sensitivity": self.sensitivity,
            "business_value": self.business_value,
            "classification": self.classification,
            "domain": self.domain,
            "quality_score": self.quality_score,
            "classification_details": self.classification_details,
            "classified_at": self.classified_at.isoformat() if self.classified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

