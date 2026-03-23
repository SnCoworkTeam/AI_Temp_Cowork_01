"""
MCP工具相关数据模型
工具定义、执行历史、调用记录
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Float, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum

from .base import BaseModel, TimestampMixin


class ToolType(str, Enum):
    """工具类型"""
    SAP = "sap"
    KNOWLEDGE = "knowledge"
    HTTP = "http"
    CUSTOM = "custom"


class ToolStatus(str, Enum):
    """工具状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class MCPTool(BaseModel):
    """MCP工具定义模型"""
    __tablename__ = "mcp_tools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="工具ID")
    name = Column(String(200), unique=True, nullable=False, index=True, comment="工具名称")
    description = Column(Text, nullable=True, comment="工具描述")
    version = Column(String(50), nullable=False, default="1.0.0", comment="版本号")
    tool_type = Column(SQLEnum(ToolType), nullable=False, comment="工具类型")
    status = Column(SQLEnum(ToolStatus), default=ToolStatus.ACTIVE, nullable=False, comment="工具状态")
    
    # 工具定义
    parameters = Column(JSONB, nullable=True, comment="参数定义（JSON Schema）")
    required_parameters = Column(JSONB, nullable=True, default=list, comment="必需参数列表")
    return_type = Column(String(100), nullable=True, comment="返回类型")
    
    # 配置
    config = Column(JSONB, nullable=True, default=dict, comment="工具配置")
    tool_metadata = Column(JSONB, nullable=True, default=dict, comment="元数据")
    
    # 统计
    call_count = Column(Integer, default=0, nullable=False, comment="调用次数")
    success_count = Column(Integer, default=0, nullable=False, comment="成功次数")
    failure_count = Column(Integer, default=0, nullable=False, comment="失败次数")
    avg_execution_time = Column(Float, nullable=True, comment="平均执行时间（秒）")
    
    # 关系
    executions = relationship("MCPToolExecution", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MCPTool(id={self.id}, name={self.name})>"


class MCPToolExecution(BaseModel):
    """MCP工具执行历史模型"""
    __tablename__ = "mcp_tool_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="执行ID")
    tool_id = Column(UUID(as_uuid=True), ForeignKey("mcp_tools.id"), nullable=False, index=True, comment="工具ID")
    executed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="执行者ID")
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=True, comment="关联工作流执行ID")
    
    # 执行信息
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, comment="执行状态")
    parameters = Column(JSONB, nullable=True, comment="执行参数")
    result = Column(JSONB, nullable=True, comment="执行结果")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 性能指标
    execution_time = Column(Float, nullable=True, comment="执行耗时（秒）")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    
    # 元数据
    execution_metadata = Column(JSONB, nullable=True, default=dict, comment="执行元数据")
    
    # 关系
    tool = relationship("MCPTool", back_populates="executions")
    
    def __repr__(self):
        return f"<MCPToolExecution(id={self.id}, tool_id={self.tool_id}, status={self.status})>"

