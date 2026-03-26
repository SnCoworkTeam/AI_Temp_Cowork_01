"""
元数据分类模型
用于管理企业架构分类
"""
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from database.src.models.base import BaseModel, TimestampMixin


class MetadataClassification(BaseModel, TimestampMixin):
    """元数据分类表"""
    __tablename__ = "metadata_classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="分类ID")
    name = Column(String(100), nullable=False, unique=True, index=True, comment="分类名称（英文）")
    display_name = Column(String(200), nullable=False, comment="显示名称（中文）")
    description = Column(Text, nullable=True, comment="分类描述")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("metadata_classifications.id", ondelete="SET NULL"), nullable=True, index=True, comment="父分类ID")
    level = Column(Integer, nullable=False, default=1, comment="层级")
    order_index = Column(Integer, nullable=True, default=0, comment="排序索引")
    
    # 关系
    parent = relationship("MetadataClassification", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<MetadataClassification(id={self.id}, name={self.name}, display_name={self.display_name})>"

