"""
工作流版本管理模型
存储工作流的不同版本信息和版本标签
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.src.models.base import Base, TimestampMixin


class WorkflowVersion(Base, TimestampMixin):
    """
    工作流版本历史模型
    存储工作流的不同版本信息
    """
    __tablename__ = "workflow_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), ForeignKey('workflow_metadata.workflow_id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)  # 版本号，如 "v1.0", "v2.1"
    version_number = Column(Integer, nullable=False)  # 数字版本号，用于排序
    description = Column(Text, nullable=True)  # 版本描述
    change_summary = Column(Text, nullable=True)  # 变更摘要
    definition = Column(JSON, nullable=False)  # 工作流定义（完整定义）
    changes = Column(JSON, nullable=True)  # 变更详情
    created_by = Column(String(255), nullable=True)  # 创建者
    is_current = Column(Boolean, default=False, index=True)  # 是否为当前版本
    deployed_at = Column(DateTime(timezone=True), nullable=True)  # 部署时间
    
    # 关系
    workflow = relationship("WorkflowMetadata", back_populates="versions")
    tags = relationship("WorkflowVersionTag", back_populates="version", cascade="all, delete-orphan")
    
    # 唯一约束：同一工作流的版本号必须唯一
    __table_args__ = (
        UniqueConstraint('workflow_id', 'version', name='uq_workflow_version'),
    )
    
    def __repr__(self):
        return f"<WorkflowVersion {self.workflow_id}@{self.version}>"


class WorkflowVersionTag(Base, TimestampMixin):
    """
    工作流版本标签
    """
    __tablename__ = "workflow_version_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey('workflow_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)  # 标签名，如 "stable", "beta", "deprecated"
    
    # 关系
    version = relationship("WorkflowVersion", back_populates="tags")
    
    # 唯一约束：同一版本的标签名必须唯一
    __table_args__ = (
        UniqueConstraint('version_id', 'tag', name='uq_version_tag'),
    )
    
    def __repr__(self):
        return f"<WorkflowVersionTag {self.version_id}:{self.tag}>"


# Pydantic Schema 模型
class WorkflowVersionBase(BaseModel):
    """版本基础模型"""
    version: str = Field(..., description="版本号", min_length=1, max_length=50)
    version_number: int = Field(..., description="数字版本号", ge=1)
    description: Optional[str] = Field(None, description="版本描述")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    definition: Dict[str, Any] = Field(..., description="工作流定义")
    changes: Optional[Dict[str, Any]] = Field(None, description="变更详情")
    created_by: Optional[str] = Field(None, description="创建者", max_length=255)


class WorkflowVersionCreate(WorkflowVersionBase):
    """创建版本请求"""
    workflow_id: str = Field(..., description="工作流ID", min_length=1, max_length=100)


class WorkflowVersionUpdate(BaseModel):
    """更新版本请求"""
    description: Optional[str] = None
    change_summary: Optional[str] = None
    is_current: Optional[bool] = None


class WorkflowVersionSchema(WorkflowVersionBase):
    """版本响应模型"""
    id: int
    workflow_id: str
    is_current: bool
    deployed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: List[str] = Field(default_factory=list, description="版本标签列表")
    
    class Config:
        from_attributes = True


class WorkflowVersionListResponse(BaseModel):
    """版本列表响应"""
    items: List[WorkflowVersionSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class VersionRestoreRequest(BaseModel):
    """恢复版本请求"""
    version: str = Field(..., description="要恢复的版本号")
    description: Optional[str] = Field(None, description="恢复操作的描述")

