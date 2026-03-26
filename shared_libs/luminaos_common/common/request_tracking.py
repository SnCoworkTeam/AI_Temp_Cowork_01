"""
请求ID追踪中间件

为每个请求生成或传递唯一的追踪ID
"""
import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求ID追踪中间件

    为每个请求添加唯一的追踪ID，用于日志关联和问题排查
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 尝试从请求头获取请求ID
        request_id = request.headers.get("X-Request-ID")

        # 如果没有，生成新的请求ID
        if not request_id:
            request_id = str(uuid.uuid4())

        # 将请求ID存储到request.state中，方便后续访问
        request.state.request_id = request_id

        # 记录请求开始
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 将请求ID添加到响应头
            response.headers["X-Request-ID"] = request_id

            # 记录请求完成
            logger.info(
                f"[{request_id}] Response: {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code
                }
            )

            return response

        except Exception as exc:
            # 记录异常
            logger.error(
                f"[{request_id}] Request failed: {str(exc)}",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise


def setup_request_tracking(app):
    """
    为FastAPI应用设置请求追踪中间件

    Usage:
        from shared_libs.common.request_tracking import setup_request_tracking

        app = FastAPI()
        setup_request_tracking(app)
    """
    app.add_middleware(RequestIDMiddleware)
    logger.info("✅ 请求ID追踪中间件已设置")
