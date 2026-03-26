"""
工作流相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from .base_models import BaseEntity, Metadata, Status


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class NodeType(str, Enum):
    """节点类型枚举"""
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    MERGE = "merge"
    AGENT = "agent"  # 智能体节点
    # AI相关节点
    LLM = "llm"  # LLM节点
    # 工具节点
    TOOL = "tool"  # 工具调用节点
    # 数据处理节点
    TRANSFORM = "transform"  # 数据转换节点
    # 集成节点
    HTTP = "http"  # HTTP请求节点
    # 控制节点
    DELAY = "delay"  # 延迟节点
    # 调试节点
    LOG = "log"  # 日志节点
    # 知识库相关节点
    KNOWLEDGE_SEARCH = "knowledge_search"  # 知识搜索节点
    DOCUMENT_PROCESSING = "document_processing"  # 文档处理节点
    KNOWLEDGE_ENHANCEMENT = "knowledge_enhancement"  # 知识增强节点


class WorkflowNode(BaseModel):
    """工作流节点模型"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    node_type: NodeType = Field(..., description="节点类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")
    inputs: List[str] = Field(default_factory=list, description="输入参数")
    outputs: List[str] = Field(default_factory=list, description="输出参数")
    next_nodes: List[str] = Field(default_factory=list, description="下一个节点ID列表")
    condition: Optional[str] = Field(None, description="条件表达式（用于条件节点）")


class WorkflowDefinition(BaseModel):
    """工作流定义模型"""
    name: str = Field(..., description="工作流名称", min_length=1, max_length=100)
    description: str = Field(default="", description="工作流描述", max_length=1000)
    version: str = Field(default="1.0.0", description="工作流版本")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT, description="工作流状态")
    nodes: List[WorkflowNode] = Field(..., description="工作流节点列表")
    start_node_id: str = Field(..., description="起始节点ID")
    end_node_ids: List[str] = Field(default_factory=list, description="结束节点ID列表")
    variables: Dict[str, Any] = Field(default_factory=dict, description="工作流变量定义")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="工作流元数据")


class WorkflowInfo(WorkflowDefinition, BaseEntity):
    """工作流信息模型（包含实体信息）"""
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    execution_count: int = Field(default=0, ge=0, description="执行次数")
    success_count: int = Field(default=0, ge=0, description="成功次数")
    failure_count: int = Field(default=0, ge=0, description="失败次数")
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100


class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求模型"""
    workflow_name: str = Field(..., description="工作流名称")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    timeout: Optional[int] = Field(default=300, ge=1, le=3600, description="超时时间（秒）")
    async_execution: bool = Field(default=False, description="是否异步执行")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    execution_id: str = Field(..., description="执行ID")
    workflow_name: str = Field(..., description="工作流名称")
    status: ExecutionStatus = Field(..., description="执行状态")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    executed_at: datetime = Field(default_factory=datetime.now, description="执行时间")
    node_results: Dict[str, Any] = Field(default_factory=dict, description="节点执行结果")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="响应元数据")


class NodeExecutionResult(BaseModel):
    """节点执行结果模型"""
    node_id: str = Field(..., description="节点ID")
    node_name: str = Field(..., description="节点名称")
    status: ExecutionStatus = Field(..., description="执行状态")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(..., ge=0, description="执行时间（秒）")
    executed_at: datetime = Field(default_factory=datetime.now, description="执行时间")


class WorkflowRegisterRequest(BaseModel):
    """工作流注册请求模型"""
    workflow: WorkflowDefinition = Field(..., description="工作流定义")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的工作流")


class WorkflowRegisterResponse(BaseModel):
    """工作流注册响应模型"""
    success: bool = Field(..., description="注册是否成功")
    workflow_name: str = Field(..., description="工作流名称")
    message: str = Field(..., description="响应消息")
    registered_at: datetime = Field(default_factory=datetime.now, description="注册时间")


class WorkflowListResponse(BaseModel):
    """工作流列表响应模型"""
    workflows: List[WorkflowInfo] = Field(..., description="工作流列表")
    total: int = Field(..., ge=0, description="工作流总数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=100, ge=1, description="每页大小")


# 向后兼容别名
WorkflowCreate = WorkflowDefinition  # 为了向后兼容，WorkflowCreate指向WorkflowDefinition
WorkflowUpdate = WorkflowDefinition  # 为了向后兼容


