"""
健康检查路由
"""
from fastapi import APIRouter
from typing import Dict, Any
import os

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("", summary="健康检查")
@router.get("/", summary="健康检查")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点
    
    Returns:
        服务健康状态
    """
    return {
        "status": "healthy",
        "service": "agent-registry",
        "version": "1.0.0",
        "redis": {
            "host": os.getenv("REDIS_HOST", "redis"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
        }
    }

