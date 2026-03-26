"""
统一错误处理
提供标准化的错误响应格式和异常处理
"""
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


def create_error_response(
    status_code: int,
    message: str,
    details: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = None,
    error_code: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> JSONResponse:
    """
    创建统一的错误响应
    
    Args:
        status_code: HTTP状态码
        message: 错误消息
        details: 错误详情（可以是字符串、字典或列表）
        error_code: 错误代码
        timestamp: 时间戳（默认当前时间）
    
    Returns:
        JSON响应对象
    """
    error_data = {
        "success": False,
        "error": {
            "message": message,
            "status_code": status_code,
        },
        "timestamp": (timestamp or datetime.now()).isoformat()
    }
    
    if details:
        error_data["error"]["details"] = details
    
    if error_code:
        error_data["error"]["code"] = error_code
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


def handle_exception(exc: Exception) -> JSONResponse:
    """
    处理异常并返回错误响应
    
    Args:
        exc: 异常对象
    
    Returns:
        JSON响应对象
    """
    if isinstance(exc, AppError):
        return create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            details=str(exc.details) if exc.details else None
        )
    
    # 处理未知异常
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal server error",
        details=str(exc)
    )

