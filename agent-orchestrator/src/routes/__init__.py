"""
路由模块
"""
from .orchestrate import router as orchestrate_router
from .plans import router as plans_router
from .health import router as health_router

__all__ = ["orchestrate_router", "plans_router", "health_router"]

