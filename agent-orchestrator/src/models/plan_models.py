"""
执行计划数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class PlanStatus(str, Enum):
    """计划状态枚举"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanStep(BaseModel):
    """计划步骤模型"""
    step_id: str = Field(..., description="步骤ID")
    name: str = Field(..., description="步骤名称")
    description: str = Field(..., description="步骤描述")
    agent_id: Optional[str] = Field(None, description="分配的智能体ID")
    agent_capabilities: List[str] = Field(default_factory=list, description="需要的智能体能力")
    task: str = Field(..., description="任务描述")
    dependencies: List[str] = Field(default_factory=list, description="依赖的步骤ID列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    status: PlanStatus = Field(default=PlanStatus.DRAFT, description="步骤状态")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        use_enum_values = True


class ExecutionPlan(BaseModel):
    """执行计划模型"""
    plan_id: str = Field(..., description="计划ID")
    name: str = Field(..., description="计划名称")
    description: str = Field(..., description="计划描述")
    task: str = Field(..., description="原始任务")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    steps: List[PlanStep] = Field(default_factory=list, description="执行步骤列表")
    status: PlanStatus = Field(default=PlanStatus.DRAFT, description="计划状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        use_enum_values = True


class PlanCreate(BaseModel):
    """创建计划请求模型"""
    task: str = Field(..., description="任务描述", min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    name: Optional[str] = Field(None, description="计划名称")
    description: Optional[str] = Field(None, description="计划描述")


class TaskDecomposition(BaseModel):
    """任务分解结果模型"""
    task: str = Field(..., description="原始任务")
    subtasks: List[Dict[str, Any]] = Field(..., description="子任务列表")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="依赖关系")
    estimated_duration: Optional[int] = Field(None, description="预计执行时间（秒）")

