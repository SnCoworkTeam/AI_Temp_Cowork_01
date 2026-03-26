"""
智能路由中间件
在请求处理前进行智能路由决策
"""
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.intelligent_router import intelligent_router
from ..core.proxy import gateway_proxy

logger = logging.getLogger(__name__)


class IntelligentRoutingMiddleware(BaseHTTPMiddleware):
    """
    智能路由中间件
    
    注意：当前版本中，智能路由通过端点 `/api/chat/intelligent` 实现。
    中间件保留用于未来扩展，如全局智能路由、请求预处理等。
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            响应对象
        """
        # 当前版本：所有请求正常处理
        # 未来可以在这里添加全局智能路由逻辑
        return await call_next(request)

