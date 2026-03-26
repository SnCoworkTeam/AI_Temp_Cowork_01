"""
工作流元数据模型
用于与元数据服务集成的工作流元数据定义
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class WorkflowMetadata(BaseModel):
    """工作流元数据模型"""
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., min_length=1, max_length=255, description="工作流名称")
    description: str = Field(..., description="工作流描述")
    version: str = Field(..., description="工作流版本")
    business_process: str = Field(..., description="业务过程")
    kpis: List[str] = Field(default_factory=list, description="KPI列表")
    sla_requirements: Dict[str, Any] = Field(default_factory=dict, description="SLA要求")
    data_sources: List[str] = Field(default_factory=list, description="数据源列表")
    ai_models_used: List[str] = Field(default_factory=list, description="使用的AI模型列表")
    execution_statistics: Dict[str, Any] = Field(default_factory=dict, description="执行统计")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="成功率")
    average_execution_time: float = Field(..., ge=0.0, description="平均执行时间（秒）")
    category: Optional[str] = Field(None, description="工作流分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WorkflowMetadataCreate(BaseModel):
    """创建工作流元数据请求"""
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., min_length=1, max_length=255, description="工作流名称")
    description: str = Field(..., description="工作流描述")
    version: str = Field(..., description="工作流版本")
    business_process: str = Field(..., description="业务过程")
    kpis: Optional[List[str]] = Field(None, description="KPI列表")
    sla_requirements: Optional[Dict[str, Any]] = Field(None, description="SLA要求")
    data_sources: Optional[List[str]] = Field(None, description="数据源列表")
    ai_models_used: Optional[List[str]] = Field(None, description="使用的AI模型列表")
    execution_statistics: Optional[Dict[str, Any]] = Field(None, description="执行统计")
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="成功率")
    average_execution_time: Optional[float] = Field(None, ge=0.0, description="平均执行时间（秒）")
    category: Optional[str] = Field(None, description="工作流分类")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


class WorkflowMetadataUpdate(BaseModel):
    """更新工作流元数据请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: Optional[str] = Field(None, description="工作流版本")
    business_process: Optional[str] = Field(None, description="业务过程")
    kpis: Optional[List[str]] = Field(None, description="KPI列表")
    sla_requirements: Optional[Dict[str, Any]] = Field(None, description="SLA要求")
    data_sources: Optional[List[str]] = Field(None, description="数据源列表")
    ai_models_used: Optional[List[str]] = Field(None, description="使用的AI模型列表")
    execution_statistics: Optional[Dict[str, Any]] = Field(None, description="执行统计")
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="成功率")
    average_execution_time: Optional[float] = Field(None, ge=0.0, description="平均执行时间（秒）")
    category: Optional[str] = Field(None, description="工作流分类")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")

