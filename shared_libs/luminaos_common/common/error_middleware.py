"""
统一错误处理中间件

为所有FastAPI服务提供全局异常处理
"""
import os
import uuid
import traceback
import logging
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, DatabaseError
from pydantic import ValidationError

from .error_codes import ErrorCode
from .error_responses import create_error_response, APIException

logger = logging.getLogger(__name__)

# 判断是否为生产环境
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"


def get_request_id(request: Request) -> str:
    """获取或生成请求ID"""
    # 尝试从请求头获取
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        # 生成新的请求ID
        request_id = str(uuid.uuid4())
    return request_id


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    处理自定义API异常
    """
    request_id = get_request_id(request)

    logger.warning(
        f"[{request_id}] API Exception: {exc.error_code.value} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_code": exc.error_code.value,
            "details": exc.details
        }
    )

    return exc.to_response(request_id=request_id, path=request.url.path)


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    处理Pydantic验证异常
    """
    request_id = get_request_id(request)

    # 提取验证错误详情
    errors = []
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
    else:
        errors = [{"message": str(exc)}]

    logger.warning(
        f"[{request_id}] Validation Error: {errors}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": errors
        }
    )

    return create_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        request_id=request_id,
        path=request.url.path,
        details={"errors": errors}
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    处理HTTP异常
    """
    request_id = get_request_id(request)

    # 映射HTTP状态码到错误代码
    status_to_code = {
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.AUTHORIZATION_ERROR,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        409: ErrorCode.CONFLICT_ERROR,
        422: ErrorCode.UNPROCESSABLE_ENTITY,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
    }

    error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    logger.warning(
        f"[{request_id}] HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": exc.status_code
        }
    )

    return create_error_response(
        error_code=error_code,
        message=str(exc.detail),
        request_id=request_id,
        path=request.url.path,
        status_code=exc.status_code
    )


async def database_exception_handler(
    request: Request,
    exc: Union[IntegrityError, OperationalError, DatabaseError]
) -> JSONResponse:
    """
    处理数据库异常
    """
    request_id = get_request_id(request)

    # 记录完整错误到日志
    logger.error(
        f"[{request_id}] Database Error: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__
        }
    )

    # 根据异常类型选择错误代码
    if isinstance(exc, IntegrityError):
        # 检查是否为唯一约束违反
        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            error_code = ErrorCode.DB_UNIQUE_VIOLATION
            message = "Duplicate entry"
        elif "foreign key" in error_msg.lower():
            error_code = ErrorCode.DB_FOREIGN_KEY_VIOLATION
            message = "Referenced resource does not exist"
        else:
            error_code = ErrorCode.DB_INTEGRITY_ERROR
            message = "Data integrity constraint violation"
    elif isinstance(exc, OperationalError):
        error_code = ErrorCode.DB_CONNECTION_FAILED
        message = "Database connection failed"
    else:
        error_code = ErrorCode.DATABASE_ERROR
        message = "Database error occurred"

    # 生产环境不返回详细信息
    details = None if IS_PRODUCTION else {"error": str(exc)}

    return create_error_response(
        error_code=error_code,
        message=message,
        request_id=request_id,
        path=request.url.path,
        details=details
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器 - 捕获所有未处理的异常
    """
    request_id = get_request_id(request)

    # 记录完整的错误栈到日志
    logger.error(
        f"[{request_id}] Unhandled Exception: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__
        }
    )

    # 生产环境不返回详细错误信息（安全考虑）
    if IS_PRODUCTION:
        message = "An internal server error occurred"
        details = None
    else:
        message = str(exc)
        details = {
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc().split('\n')
        }

    return create_error_response(
        error_code=ErrorCode.INTERNAL_ERROR,
        message=message,
        request_id=request_id,
        path=request.url.path,
        details=details
    )


def setup_exception_handlers(app):
    """
    为FastAPI应用设置所有异常处理器

    Usage:
        from shared_libs.common.error_middleware import setup_exception_handlers

        app = FastAPI()
        setup_exception_handlers(app)
    """
    # 自定义API异常
    app.add_exception_handler(APIException, api_exception_handler)

    # 验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # HTTP异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 数据库异常
    app.add_exception_handler(IntegrityError, database_exception_handler)
    app.add_exception_handler(OperationalError, database_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)

    # 全局异常（必须最后注册）
    app.add_exception_handler(Exception, global_exception_handler)

    logger.info("✅ 统一错误处理中间件已设置")
