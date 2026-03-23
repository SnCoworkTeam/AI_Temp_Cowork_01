"""
限流中间件
实现基于令牌桶的限流功能
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from ..config import settings


# 创建限流器
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"] if settings.RATE_LIMIT_ENABLED else []
)


def setup_rate_limiting(app: FastAPI):
    """
    配置限流中间件

    Args:
        app: FastAPI应用实例
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
