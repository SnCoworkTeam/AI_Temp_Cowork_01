"""
通用数据模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    timestamp: str = Field(..., description="时间戳")
    version: str = Field(..., description="版本号")


class ApiResponse(BaseModel):
    """标准API响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error: Dict[str, Any] = Field(..., description="错误信息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


