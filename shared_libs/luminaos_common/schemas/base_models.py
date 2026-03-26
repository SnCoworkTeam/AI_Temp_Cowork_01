"""
基础数据模型
提供跨服务使用的基础Pydantic模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum


class Status(str, Enum):
    """通用状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="响应时间戳"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ApiResponse(BaseResponse):
    """标准API响应模型"""
    data: Optional[Any] = Field(None, description="响应数据")
    code: Optional[str] = Field(None, description="响应代码")


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    data: List[Any] = Field(default_factory=list, description="数据列表")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页大小")
    total: int = Field(..., ge=0, description="总记录数")
    total_pages: int = Field(..., ge=0, description="总页数")
    
    @classmethod
    def create(
        cls,
        data: List[Any],
        page: int,
        page_size: int,
        total: int,
        message: Optional[str] = None
    ) -> "PaginatedResponse":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            success=True,
            data=data,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            message=message or f"Retrieved {len(data)} items"
        )


class ErrorDetail(BaseModel):
    """错误详情模型"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[List[ErrorDetail]] = Field(None, description="错误详情列表")
    traceback: Optional[str] = Field(None, description="错误堆栈（仅开发环境）")
    
    @classmethod
    def create(
        cls,
        error: str,
        error_code: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None,
        traceback: Optional[str] = None
    ) -> "ErrorResponse":
        """创建错误响应"""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            details=details,
            traceback=traceback
        )


class HealthCheckResponse(BaseResponse):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="服务版本")
    checks: Dict[str, Any] = Field(default_factory=dict, description="健康检查详情")


class Metadata(BaseModel):
    """元数据模型"""
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")
    tags: List[str] = Field(default_factory=list, description="标签")
    extra: Dict[str, Any] = Field(default_factory=dict, description="额外信息")


class BaseEntity(BaseModel):
    """基础实体模型"""
    id: Optional[str] = Field(None, description="实体ID")
    metadata: Optional[Metadata] = Field(None, description="元数据")


class FilterParams(BaseModel):
    """过滤参数模型"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=1000, description="每页大小")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field(default="asc", description="排序方向")
    search: Optional[str] = Field(None, description="搜索关键词")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    
    @classmethod
    def validate_sort_order(cls, v: Optional[str]) -> str:
        """验证排序方向"""
        if v and v.lower() not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower() if v else "asc"


