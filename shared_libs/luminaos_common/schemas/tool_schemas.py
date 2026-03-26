"""
工具相关数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from .base_models import BaseEntity, Metadata


class ToolType(str, Enum):
    """工具类型枚举"""
    FUNCTION = "function"
    API = "api"
    SCRIPT = "script"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


class ToolStatus(str, Enum):
    """工具状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"


class ToolDefinition(BaseModel):
    """工具定义模型"""
    name: str = Field(..., description="工具名称", min_length=1, max_length=100)
    description: str = Field(..., description="工具描述", min_length=1, max_length=1000)
    version: str = Field(default="1.0.0", description="工具版本")
    tool_type: ToolType = Field(default=ToolType.FUNCTION, description="工具类型")
    status: ToolStatus = Field(default=ToolStatus.ACTIVE, description="工具状态")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数定义（JSON Schema）")
    required_parameters: List[str] = Field(default_factory=list, description="必需参数列表")
    returns: Optional[Dict[str, Any]] = Field(None, description="返回值定义")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="工具元数据")


class ToolInfo(ToolDefinition, BaseEntity):
    """工具信息模型（包含实体信息）"""
    registered_at: Optional[datetime] = Field(None, description="注册时间")
    last_executed_at: Optional[datetime] = Field(None, description="最后执行时间")
    execution_count: int = Field(default=0, ge=0, description="执行次数")
    success_count: int = Field(default=0, ge=0, description="成功次数")
    failure_count: int = Field(default=0, ge=0, description="失败次数")
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100


class ToolExecutionRequest(BaseModel):
    """工具执行请求模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(..., description="执行参数")
    timeout: Optional[int] = Field(default=30, ge=1, le=300, description="超时时间（秒）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="执行元数据")
    async_execution: bool = Field(default=False, description="是否异步执行")


class ToolExecutionResponse(BaseModel):
    """工具执行响应模型"""
    success: bool = Field(..., description="执行是否成功")
    tool_name: str = Field(..., description="工具名称")
    execution_id: Optional[str] = Field(None, description="执行ID")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    executed_at: datetime = Field(default_factory=datetime.now, description="执行时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="响应元数据")


class ToolRegisterRequest(BaseModel):
    """工具注册请求模型"""
    tool: ToolDefinition = Field(..., description="工具定义")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的工具")


class ToolRegisterResponse(BaseModel):
    """工具注册响应模型"""
    success: bool = Field(..., description="注册是否成功")
    tool_name: str = Field(..., description="工具名称")
    message: str = Field(..., description="响应消息")
    registered_at: datetime = Field(default_factory=datetime.now, description="注册时间")


class ToolListResponse(BaseModel):
    """工具列表响应模型"""
    tools: List[ToolInfo] = Field(..., description="工具列表")
    total: int = Field(..., ge=0, description="工具总数")
    page: int = Field(default=1, ge=1, description="当前页码")
    page_size: int = Field(default=100, ge=1, description="每页大小")


