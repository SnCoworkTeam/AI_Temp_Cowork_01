"""
基础数据模型
用于存储项目分类、行业、领域等基础数据
"""
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class BasicDataCategory(BaseModel):
    """基础数据分类（如：项目类型、行业分类、领域分类等）"""
    __tablename__ = "pm_basic_data_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="分类ID")
    category_type = Column(String(50), nullable=False, index=True, comment="分类类型（如：project_type, industry, domain等）")
    code = Column(String(50), nullable=False, index=True, comment="分类编码")
    name = Column(String(200), nullable=False, comment="分类名称")
    description = Column(Text, nullable=True, comment="分类描述")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=True, index=True, comment="父分类ID（支持多级分类）")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="是否启用")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    parent = relationship("BasicDataCategory", remote_side=[id], backref="children")
    
    # 唯一约束：同一类型下编码唯一
    __table_args__ = (
        UniqueConstraint('category_type', 'code', name='uq_category_type_code'),
    )


class ProjectBasicDataMapping(BaseModel):
    """项目与基础数据的关联表"""
    __tablename__ = "pm_project_basic_data_mapping"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="关联ID")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id"), nullable=False, index=True, comment="项目ID")
    category_id = Column(UUID(as_uuid=True), ForeignKey("pm_basic_data_categories.id"), nullable=False, index=True, comment="分类ID")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    project = relationship("Project", back_populates="basic_data_mappings")
    category = relationship("BasicDataCategory")
    
    # 唯一约束：同一项目同一分类只能有一条记录
    __table_args__ = (
        UniqueConstraint('project_id', 'category_id', name='uq_project_category'),
    )

