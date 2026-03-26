"""
任务编排数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class CoordinationStrategy(str, Enum):
    """协调策略枚举"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    PIPELINE = "pipeline"  # 流水线执行
    ADAPTIVE = "adaptive"  # 自适应执行


class AgentSelection(BaseModel):
    """智能体选择模型"""
    agent_id: str = Field(..., description="智能体ID")
    agent_name: str = Field(..., description="智能体名称")
    capabilities: List[str] = Field(..., description="能力列表")
    confidence: float = Field(..., description="匹配置信度", ge=0.0, le=1.0)
    reason: str = Field(..., description="选择原因")


class OrchestrationRequest(BaseModel):
    """编排请求模型"""
    task: str = Field(..., description="任务描述", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    strategy: CoordinationStrategy = Field(default=CoordinationStrategy.ADAPTIVE, description="协调策略")
    max_agents: Optional[int] = Field(5, description="最大智能体数量", ge=1, le=20)
    timeout: Optional[int] = Field(600, description="超时时间（秒）", ge=1, le=3600)


class OrchestrationResponse(BaseModel):
    """编排响应模型"""
    execution_id: str = Field(..., description="执行ID")
    plan_id: str = Field(..., description="计划ID")
    status: str = Field(..., description="执行状态")
    results: Dict[str, Any] = Field(default_factory=dict, description="执行结果")
    agent_selections: List[AgentSelection] = Field(default_factory=list, description="智能体选择列表")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

