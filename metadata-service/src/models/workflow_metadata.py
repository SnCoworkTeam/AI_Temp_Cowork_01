"""
工作流元数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from database.src.models.base import Base, TimestampMixin


class WorkflowStatus(str, enum.Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class WorkflowMetadata(Base, TimestampMixin):
    """工作流元数据表"""
    __tablename__ = "workflow_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(100), nullable=False, unique=True, index=True)  # 工作流引擎中的ID
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    status = Column(
        SQLEnum(WorkflowStatus, values_callable=lambda x: [e.value for e in x], name="workflowstatus"),
        default=WorkflowStatus.ACTIVE,
        index=True
    )
    
    # 工作流信息
    version = Column(String(50))
    category = Column(String(100))  # 工作流分类
    workflow_type = Column(String(50))  # 工作流类型
    
    # 定义信息
    definition = Column(JSON)  # 工作流定义（节点、连接等）
    input_schema = Column(JSON)  # 输入schema
    output_schema = Column(JSON)  # 输出schema
    
    # 执行信息
    execution_count = Column(Integer, default=0)
    last_execution_time = Column(DateTime)
    average_execution_time = Column(Integer)  # 平均执行时间（秒）
    success_rate = Column(String(10))  # 成功率
    
    # 依赖信息
    dependencies = Column(JSON)  # 依赖的数据资产、模型等
    data_sources = Column(JSON)  # 数据源列表
    data_sinks = Column(JSON)  # 数据输出列表
    
    # 业务信息
    business_owner = Column(String(100))
    technical_owner = Column(String(100))
    tags = Column(JSON)  # 标签列表（旧字段，保留向后兼容）
    use_cases = Column(JSON)  # 使用场景
    
    # 分类维度（新字段，支持三层分类体系）
    classification_dimensions = Column(JSON, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    standardized_tags = Column(JSON, nullable=True, comment='标准化标签列表')
    
    # 兼容属性：从新字段或旧字段获取主分类
    @property
    def primary_classification(self) -> Optional[str]:
        """从新字段或旧字段获取主分类"""
        if self.classification_dimensions and isinstance(self.classification_dimensions, dict):
            return self.classification_dimensions.get('primary')
        # 如果没有新字段，使用workflow_type或category作为主分类
        return self.workflow_type or self.category
    
    # 元数据
    extra_metadata = Column("metadata", JSON)  # 使用 metadata 作为数据库列名
    
    # 关系
    versions = relationship(
        "WorkflowVersion",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowVersion.version_number.desc()"
    )


class WorkflowMetadataSchema(BaseModel):
    """工作流元数据Schema（API响应）"""
    id: int
    workflow_id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: WorkflowStatus
    version: Optional[str] = None
    category: Optional[str] = None
    workflow_type: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    execution_count: int
    last_execution_time: Optional[datetime] = None
    average_execution_time: Optional[int] = None
    success_rate: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    data_sinks: Optional[List[str]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    use_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowMetadataCreate(BaseModel):
    """创建工作流元数据请求"""
    workflow_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    version: Optional[str] = None
    category: Optional[str] = None
    workflow_type: Optional[str] = None
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    definition: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    execution_count: int = 0
    last_execution_time: Optional[datetime] = None
    average_execution_time: Optional[int] = None
    success_rate: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    data_sinks: Optional[List[str]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class WorkflowMetadataUpdate(BaseModel):
    """更新工作流元数据请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    version: Optional[str] = None
    category: Optional[str] = None
    workflow_type: Optional[str] = None
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    definition: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    execution_count: Optional[int] = None
    last_execution_time: Optional[datetime] = None
    average_execution_time: Optional[int] = None
    success_rate: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    data_sinks: Optional[List[str]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
