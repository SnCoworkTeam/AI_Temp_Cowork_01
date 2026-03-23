"""
交互协议数据模型
定义实时交互、执行控制、用户反馈等协议
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class InteractionType(str, Enum):
    """交互类型枚举"""
    EXECUTION_START = "execution_start"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_STEP = "execution_step"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_RESUMED = "execution_resumed"
    EXECUTION_CANCELLED = "execution_cancelled"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_ERROR = "execution_error"
    USER_INTERACTION_REQUIRED = "user_interaction_required"
    CONFIRMATION_REQUIRED = "confirmation_required"


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"
    WAITING_FOR_INPUT = "waiting_for_input"


class InteractiveMessage(BaseModel):
    """交互消息模型"""
    type: InteractionType
    execution_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)  # 可用的用户操作
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)  # 进度 0-1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserAction(BaseModel):
    """用户操作模型"""
    action: str
    execution_id: str
    session_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ExecutionState(BaseModel):
    """执行状态模型"""
    execution_id: str
    session_id: str
    status: ExecutionStatus
    current_step: int = 0
    total_steps: int = 0
    progress: float = Field(0.0, ge=0.0, le=1.0)
    user_input: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    paused: bool = False
    cancelled: bool = False
    waiting_for_input: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ConfirmationRequest(BaseModel):
    """确认请求模型"""
    execution_id: str
    session_id: str
    subtask_name: str
    description: str
    actions_required: List[str] = Field(default_factory=list)
    timeout: int = 30  # 超时时间（秒）


class UserInputRequest(BaseModel):
    """用户输入请求模型"""
    execution_id: str
    session_id: str
    subtask_name: str
    required_parameters: List[str] = Field(default_factory=list)
    input_description: str
    timeout: int = 60  # 超时时间（秒）





































