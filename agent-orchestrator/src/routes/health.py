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
        "service": "agent-orchestrator",
        "version": "1.0.0",
        "dependencies": {
            "agent_service": os.getenv("AGENT_SERVICE_URL", "http://agent-service:8010"),
            "registry_service": os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000"),
        }
    }

