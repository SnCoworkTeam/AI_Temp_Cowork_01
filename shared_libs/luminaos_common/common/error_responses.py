"""
统一错误响应格式

为所有服务提供标准化的错误响应
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

from .error_codes import ErrorCode, get_http_status, get_error_message


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: Optional[str] = Field(None, description="相关字段（验证错误时）")
    details: Optional[Dict[str, Any]] = Field(None, description="额外的错误详情")


class ErrorResponse(BaseModel):
    """标准错误响应格式"""
    success: bool = Field(False, description="请求是否成功")
    error: ErrorDetail = Field(..., description="错误详情")
    request_id: Optional[str] = Field(None, description="请求追踪ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="错误发生时间(UTC)"
    )
    path: Optional[str] = Field(None, description="请求路径")


def create_error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None
) -> JSONResponse:
    """
    创建标准错误响应

    Args:
        error_code: 错误代码
        message: 自定义错误消息（可选）
        request_id: 请求ID（可选）
        path: 请求路径（可选）
        field: 相关字段（可选，用于验证错误）
        details: 额外详情（可选）
        status_code: HTTP状态码（可选，默认从error_code推导）

    Returns:
        JSONResponse: FastAPI JSONResponse对象
    """
    # 获取HTTP状态码
    http_status = status_code or get_http_status(error_code)

    # 获取错误消息
    error_message = message or get_error_message(error_code)

    # 构建错误响应
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=error_code.value,
            message=error_message,
            field=field,
            details=details
        ),
        request_id=request_id,
        path=path
    )

    return JSONResponse(
        status_code=http_status,
        content=error_response.model_dump(exclude_none=True)
    )


class APIException(Exception):
    """
    自定义API异常基类

    所有业务逻辑异常都应该继承此类
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        self.error_code = error_code
        self.message = message or get_error_message(error_code)
        self.field = field
        self.details = details
        self.status_code = status_code or get_http_status(error_code)
        super().__init__(self.message)

    def to_response(
        self,
        request_id: Optional[str] = None,
        path: Optional[str] = None
    ) -> JSONResponse:
        """转换为JSONResponse"""
        return create_error_response(
            error_code=self.error_code,
            message=self.message,
            request_id=request_id,
            path=path,
            field=self.field,
            details=self.details,
            status_code=self.status_code
        )


# 常用异常类
class ValidationException(APIException):
    """验证异常"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, field, details)


class NotFoundException(APIException):
    """资源不存在异常"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(ErrorCode.RESOURCE_NOT_FOUND, message, details=details)


class AuthenticationException(APIException):
    """认证失败异常"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(ErrorCode.AUTHENTICATION_FAILED, message, details=details)


class AuthorizationException(APIException):
    """授权失败异常"""
    def __init__(self, message: str = "Access denied", details: Optional[Dict] = None):
        super().__init__(ErrorCode.AUTHORIZATION_ERROR, message, details=details)


class ConflictException(APIException):
    """资源冲突异常"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(ErrorCode.CONFLICT_ERROR, message, details=details)


class DatabaseException(APIException):
    """数据库异常"""
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATABASE_ERROR, details: Optional[Dict] = None):
        super().__init__(error_code, message, details=details)
