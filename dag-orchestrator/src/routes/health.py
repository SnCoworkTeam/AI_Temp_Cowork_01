"""
健康检查路由
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["健康检查"])


@router.get("/health", summary="健康检查")
async def health_check() -> Dict[str, Any]:
    """
    服务健康检查
    """
    return {
        "status": "healthy",
        "service": "dag-orchestrator",
        "version": "1.0.0"
    }











































