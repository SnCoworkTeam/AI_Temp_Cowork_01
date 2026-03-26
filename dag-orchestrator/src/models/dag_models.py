"""
DAG核心数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class TaskType(str, Enum):
    """任务类型枚举"""
    MCP_TOOL = "mcp_tool"
    WORKFLOW = "workflow"
    AGENT = "agent"
    KNOWLEDGE = "knowledge"
    CALCULATION = "calculation"
    CONDITION = "condition"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskNode(BaseModel):
    """任务节点模型"""
    node_id: str = Field(..., description="节点唯一标识")
    name: str = Field(..., description="任务名称")
    description: str = Field(..., description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    target_service: str = Field(..., description="目标服务名称")
    action: str = Field(..., description="具体操作")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    dependencies: List[str] = Field(default_factory=list, description="依赖的node_id列表")
    timeout: int = Field(default=300, description="超时时间（秒）")
    retry_count: int = Field(default=3, description="重试次数")
    
    class Config:
        use_enum_values = True


class DAGPlan(BaseModel):
    """DAG执行计划"""
    dag_id: str = Field(..., description="DAG唯一标识")
    task_nodes: Dict[str, TaskNode] = Field(..., description="节点ID到节点的映射")
    entry_nodes: List[str] = Field(default_factory=list, description="入口节点列表")
    exit_nodes: List[str] = Field(default_factory=list, description="出口节点列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class ExecutionRequest(BaseModel):
    """执行请求模型"""
    user_input: str = Field(..., description="用户输入")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    priority: str = Field(default="normal", description="优先级")
    callback_url: Optional[str] = Field(None, description="回调URL")
    user_id: Optional[str] = Field(None, description="用户ID")


class ExecutionResult(BaseModel):
    """执行结果模型"""
    execution_id: str = Field(..., description="执行ID")
    dag_id: Optional[str] = Field(None, description="DAG ID")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="执行状态")
    results: Dict[str, Any] = Field(default_factory=dict, description="节点执行结果")
    final_output: Optional[str] = Field(None, description="最终输出")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    
    class Config:
        use_enum_values = True











































