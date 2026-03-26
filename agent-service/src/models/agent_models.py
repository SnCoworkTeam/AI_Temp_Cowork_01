"""
智能体数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class AgentStatus(str, Enum):
    """智能体状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"


class AgentCapability(str, Enum):
    """智能体能力类型"""
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    CODE_GENERATION = "code_generation"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    CONVERSATION = "conversation"
    TASK_PLANNING = "task_planning"
    MULTI_AGENT_COORDINATION = "multi_agent_coordination"
    SERVER_OPERATION = "server_operation"


class AgentBase(BaseModel):
    """智能体基础模型"""
    name: str = Field(..., description="智能体名称", min_length=1, max_length=100)
    description: str = Field(..., description="智能体描述", max_length=1000)
    capabilities: List[AgentCapability] = Field(default_factory=list, description="能力列表")
    system_prompt: Optional[str] = Field(None, description="系统提示词", max_length=5000)
    config: Dict[str, Any] = Field(default_factory=dict, description="配置参数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class AgentCreate(AgentBase):
    """创建智能体请求模型"""
    pass


class AgentUpdate(BaseModel):
    """更新智能体请求模型"""
    name: Optional[str] = Field(None, description="智能体名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="智能体描述", max_length=1000)
    capabilities: Optional[List[AgentCapability]] = Field(None, description="能力列表")
    system_prompt: Optional[str] = Field(None, description="系统提示词", max_length=5000)
    config: Optional[Dict[str, Any]] = Field(None, description="配置参数")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    status: Optional[AgentStatus] = Field(None, description="状态")


class Agent(AgentBase):
    """智能体完整模型"""
    id: str = Field(..., description="智能体ID")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")

    class Config:
        use_enum_values = True


class AgentResponse(Agent):
    """智能体响应模型"""
    execution_count: int = Field(default=0, description="执行次数")
    success_rate: float = Field(default=0.0, description="成功率")
    last_execution_at: Optional[datetime] = Field(None, description="最后执行时间")

