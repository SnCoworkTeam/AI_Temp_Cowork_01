"""
路由模块
"""
from .registry import router as registry_router
from .discovery import router as discovery_router
from .health import router as health_router

__all__ = ["registry_router", "discovery_router", "health_router"]

