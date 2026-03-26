"""
智能体规格数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .capability_models import CapabilityType, Capability


class AgentSpec(BaseModel):
    """智能体规格模型"""
    agent_id: str = Field(..., description="智能体ID")
    agent_name: str = Field(..., description="智能体名称")
    agent_url: str = Field(..., description="智能体服务URL")
    capabilities: List[CapabilityType] = Field(..., description="能力列表")
    description: Optional[str] = Field(None, description="描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    registered_at: datetime = Field(..., description="注册时间")
    last_heartbeat: Optional[datetime] = Field(None, description="最后心跳时间")
    status: str = Field(default="active", description="状态")
    
    class Config:
        use_enum_values = True


class AgentSpecCreate(BaseModel):
    """创建智能体规格请求模型"""
    agent_id: str = Field(..., description="智能体ID")
    agent_name: str = Field(..., description="智能体名称")
    agent_url: str = Field(..., description="智能体服务URL")
    capabilities: List[CapabilityType] = Field(..., description="能力列表")
    description: Optional[str] = Field(None, description="描述")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class AgentSpecResponse(AgentSpec):
    """智能体规格响应模型"""
    match_score: Optional[float] = Field(None, description="匹配分数", ge=0.0, le=1.0)
    match_reason: Optional[str] = Field(None, description="匹配原因")

