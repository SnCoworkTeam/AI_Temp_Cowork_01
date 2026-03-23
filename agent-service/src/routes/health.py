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
        "service": "agent-service",
        "version": "1.0.0",
        "deepseek": {
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
            "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
            "model": os.getenv("LLM_MODEL", "deepseek-chat"),
            "status": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
        }
    }

