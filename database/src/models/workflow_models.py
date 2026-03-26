"""
工作流相关数据模型
工作流定义、执行历史、节点配置
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Float, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum
from datetime import datetime

from .base import BaseModel, TimestampMixin


class WorkflowStatus(str, Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeType(str, Enum):
    """节点类型"""
    START = "start"
    END = "end"
    LLM = "llm"
    TOOL = "tool"
    CONDITION = "condition"
    TRANSFORM = "transform"
    HTTP = "http"
    DELAY = "delay"
    LOG = "log"
    KNOWLEDGE_SEARCH = "knowledge_search"
    DOCUMENT_PROCESSING = "document_processing"
    KNOWLEDGE_ENHANCEMENT = "knowledge_enhancement"


class WorkflowDefinition(BaseModel):
    """工作流定义模型"""
    __tablename__ = "workflow_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="工作流ID")
    name = Column(String(200), nullable=False, index=True, comment="工作流名称")
    description = Column(Text, nullable=True, comment="工作流描述")
    version = Column(String(50), nullable=False, default="1.0.0", comment="版本号")
    status = Column(
        SQLEnum(WorkflowStatus, values_callable=lambda x: [e.value for e in x]),
        default="draft",  # 使用字符串值而不是枚举对象
        nullable=False,
        comment="状态"
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="创建者ID")
    config = Column(JSONB, nullable=True, default=dict, comment="工作流配置")
    workflow_metadata = Column(JSONB, nullable=True, default=dict, comment="元数据")
    
    # 关系
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    connections = relationship("WorkflowConnection", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkflowDefinition(id={self.id}, name={self.name})>"


class WorkflowNode(BaseModel):
    """工作流节点模型"""
    __tablename__ = "workflow_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="节点ID")
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False, index=True, comment="工作流ID")
    node_id = Column(String(100), nullable=False, comment="节点标识符")
    name = Column(String(200), nullable=False, comment="节点名称")
    node_type = Column(
        SQLEnum(NodeType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="节点类型"
    )
    description = Column(Text, nullable=True, comment="节点描述")
    config = Column(JSONB, nullable=True, default=dict, comment="节点配置")
    position = Column(JSONB, nullable=True, comment="节点位置（x, y）")
    style = Column(JSONB, nullable=True, comment="节点样式")
    
    # 关系
    workflow = relationship("WorkflowDefinition", back_populates="nodes")
    source_connections = relationship("WorkflowConnection", foreign_keys="WorkflowConnection.source_node_id", back_populates="source_node")
    target_connections = relationship("WorkflowConnection", foreign_keys="WorkflowConnection.target_node_id", back_populates="target_node")
    
    def __repr__(self):
        return f"<WorkflowNode(id={self.id}, node_id={self.node_id}, type={self.node_type})>"


class WorkflowConnection(BaseModel):
    """工作流连接模型"""
    __tablename__ = "workflow_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="连接ID")
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False, index=True, comment="工作流ID")
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False, comment="源节点ID")
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False, comment="目标节点ID")
    condition = Column(String(500), nullable=True, comment="连接条件")
    label = Column(String(200), nullable=True, comment="连接标签")
    style = Column(JSONB, nullable=True, comment="连接样式")
    
    # 关系
    workflow = relationship("WorkflowDefinition", back_populates="connections")
    source_node = relationship("WorkflowNode", foreign_keys=[source_node_id], back_populates="source_connections")
    target_node = relationship("WorkflowNode", foreign_keys=[target_node_id], back_populates="target_connections")
    
    def __repr__(self):
        return f"<WorkflowConnection(id={self.id}, source={self.source_node_id}, target={self.target_node_id})>"


class WorkflowExecution(BaseModel):
    """工作流执行历史模型"""
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="执行ID")
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False, index=True, comment="工作流ID")
    executed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="执行者ID")
    status = Column(
        SQLEnum(ExecutionStatus, values_callable=lambda x: [e.value for e in x]),
        default="pending",  # 使用字符串值
        nullable=False,
        comment="执行状态"
    )
    input_data = Column(JSONB, nullable=True, comment="输入数据")
    output_data = Column(JSONB, nullable=True, comment="输出数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    progress = Column(Float, default=0.0, nullable=False, comment="执行进度（0-1）")
    current_node_id = Column(String(100), nullable=True, comment="当前节点ID")
    node_results = Column(JSONB, nullable=True, comment="节点执行结果")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    execution_time = Column(Float, nullable=True, comment="执行耗时（秒）")
    execution_metadata = Column(JSONB, nullable=True, default=dict, comment="执行元数据")
    
    # 关系
    workflow = relationship("WorkflowDefinition", back_populates="executions")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"

