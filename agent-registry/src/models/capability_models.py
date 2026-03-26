"""
能力数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class CapabilityType(str, Enum):
    """能力类型枚举"""
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    CODE_GENERATION = "code_generation"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    CONVERSATION = "conversation"
    TASK_PLANNING = "task_planning"
    MULTI_AGENT_COORDINATION = "multi_agent_coordination"


class Capability(BaseModel):
    """能力模型"""
    type: CapabilityType = Field(..., description="能力类型")
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="能力参数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        use_enum_values = True


class CapabilityRequirement(BaseModel):
    """能力需求模型"""
    capabilities: List[CapabilityType] = Field(..., description="需要的能力列表")
    min_match: Optional[int] = Field(None, description="最少匹配数量")
    priority: Optional[List[CapabilityType]] = Field(None, description="优先级列表")

