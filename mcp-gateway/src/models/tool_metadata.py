"""
工具元数据模型
用于与元数据服务集成的工具元数据定义
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class ToolMetadata(BaseModel):
    """工具元数据模型"""
    tool_name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    description: str = Field(..., min_length=1, description="工具描述")
    category: str = Field(..., description="工具分类")
    input_schema: Dict[str, Any] = Field(..., description="输入Schema定义")
    output_schema: Dict[str, Any] = Field(..., description="输出Schema定义")
    usage_statistics: Dict[str, Any] = Field(default_factory=dict, description="使用统计")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="质量指标")
    dependencies: List[str] = Field(default_factory=list, description="依赖的工具列表")
    version: Optional[str] = Field(None, description="工具版本")
    author: Optional[str] = Field(None, description="工具作者")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ToolMetadataCreate(BaseModel):
    """创建工具元数据请求"""
    tool_name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    description: str = Field(..., min_length=1, description="工具描述")
    category: str = Field(..., description="工具分类")
    input_schema: Dict[str, Any] = Field(..., description="输入Schema定义")
    output_schema: Dict[str, Any] = Field(..., description="输出Schema定义")
    usage_statistics: Optional[Dict[str, Any]] = Field(None, description="使用统计")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="质量指标")
    dependencies: Optional[List[str]] = Field(None, description="依赖的工具列表")
    version: Optional[str] = Field(None, description="工具版本")
    author: Optional[str] = Field(None, description="工具作者")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


class ToolMetadataUpdate(BaseModel):
    """更新工具元数据请求"""
    description: Optional[str] = Field(None, description="工具描述")
    category: Optional[str] = Field(None, description="工具分类")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="输入Schema定义")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="输出Schema定义")
    usage_statistics: Optional[Dict[str, Any]] = Field(None, description="使用统计")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标")
    quality_metrics: Optional[Dict[str, Any]] = Field(None, description="质量指标")
    dependencies: Optional[List[str]] = Field(None, description="依赖的工具列表")
    version: Optional[str] = Field(None, description="工具版本")
    author: Optional[str] = Field(None, description="工具作者")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")

