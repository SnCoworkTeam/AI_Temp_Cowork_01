"""
健康检查API路由
"""
from fastapi import APIRouter
from ..core.embedding_manager import get_unified_embedding_manager

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """健康检查"""
    embedding_manager = get_unified_embedding_manager()
    return {
        "status": "healthy",
        "service": "vector-coordinator-service",
        "model_available": embedding_manager.is_available(),
        "model_dimension": embedding_manager.get_dimension()
    }


@router.get("/health/ready")
async def readiness_check():
    """就绪检查"""
    embedding_manager = get_unified_embedding_manager()
    if not embedding_manager.is_available():
        return {
            "status": "not_ready",
            "reason": "Embedding model not available"
        }, 503
    
    return {
        "status": "ready",
        "service": "vector-coordinator-service"
    }







