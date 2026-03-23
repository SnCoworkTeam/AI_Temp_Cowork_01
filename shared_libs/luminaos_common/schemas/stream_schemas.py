"""
流式协议标准定义
统一所有服务的流式数据格式
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict
from enum import Enum
import time


class StreamMessageType(str, Enum):
    """流式消息类型"""
    START = "start"  # 开始执行
    CHUNK = "chunk"  # 数据块
    STEP = "step"  # 步骤结果
    PROGRESS = "progress"  # 进度更新
    COMPLETE = "complete"  # 执行完成
    ERROR = "error"  # 错误信息
    CANCEL = "cancel"  # 取消执行


class StreamMessage(BaseModel):
    """标准流式消息格式"""
    type: StreamMessageType = Field(..., description="消息类型")
    data: Optional[Any] = Field(None, description="消息数据")
    progress: Optional[float] = Field(None, ge=0, le=100, description="进度百分比 (0-100)")
    step: Optional[str] = Field(None, description="当前步骤名称")
    step_id: Optional[str] = Field(None, description="步骤ID")
    timestamp: float = Field(default_factory=time.time, description="时间戳")
    execution_id: Optional[str] = Field(None, description="执行ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        use_enum_values = True


class AgentStreamResponse(BaseModel):
    """智能体流式响应"""
    execution_id: str = Field(..., description="执行ID")
    agent_id: str = Field(..., description="智能体ID")
    agent_name: Optional[str] = Field(None, description="智能体名称")
    messages: List[StreamMessage] = Field(default_factory=list, description="流式消息列表")
    final_result: Optional[Any] = Field(None, description="最终结果")


class WorkflowStreamResponse(BaseModel):
    """工作流流式响应"""
    execution_id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: Optional[str] = Field(None, description="工作流名称")
    messages: List[StreamMessage] = Field(default_factory=list, description="流式消息列表")
    final_result: Optional[Any] = Field(None, description="最终结果")


class DAGStreamResponse(BaseModel):
    """DAG流式响应"""
    execution_id: str = Field(..., description="执行ID")
    dag_id: Optional[str] = Field(None, description="DAG ID")
    messages: List[StreamMessage] = Field(default_factory=list, description="流式消息列表")
    final_result: Optional[Any] = Field(None, description="最终结果")




