"""
健康检查路由
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get(
    "/health",
    summary="健康检查",
    description="返回服务健康状态",
    tags=["Health"]
)
async def health_check() -> Dict[str, Any]:
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "knowledge-base",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get(
    "/health/ready",
    summary="就绪检查",
    description="就绪检查端点",
    tags=["Health"]
)
async def readiness_check() -> Dict[str, Any]:
    """就绪检查"""
    # 检查向量存储是否可用
    try:
        from ..core.vector_store import get_vector_store
        vector_store = get_vector_store()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@router.get(
    "/health/live",
    summary="存活检查",
    description="存活检查端点",
    tags=["Health"]
)
async def liveness_check() -> Dict[str, Any]:
    """存活检查"""
    return {"status": "alive"}









