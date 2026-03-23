"""
执行相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionRequest(BaseModel):
    """执行请求模型"""
    agent_id: str = Field(..., description="智能体ID")
    task: str = Field(..., description="任务描述", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    timeout: Optional[int] = Field(300, description="超时时间（秒）", ge=1, le=3600)
    stream: bool = Field(False, description="是否流式返回")


class ExecutionResponse(BaseModel):
    """执行响应模型"""
    execution_id: str = Field(..., description="执行ID")
    agent_id: str = Field(..., description="智能体ID")
    status: ExecutionStatus = Field(..., description="执行状态")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        use_enum_values = True


class ExecutionResult(BaseModel):
    """执行结果模型"""
    success: bool = Field(..., description="是否成功")
    output: Any = Field(..., description="输出结果")
    logs: List[str] = Field(default_factory=list, description="执行日志")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")

