"""
健康检查路由
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get("/health", summary="健康检查", response_model=Dict[str, Any])
async def health_check():
    """
    健康检查端点
    返回服务状态和基本信息
    """
    return {
        "status": "healthy",
        "service": "workflow-engine",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/ready", summary="就绪检查")
async def readiness_check():
    """
    就绪检查端点
    用于Kubernetes等容器编排平台的就绪探针
    """
    # TODO: 添加LangGraph运行时检查等
    return {"status": "ready"}


@router.get("/health/live", summary="存活检查")
async def liveness_check():
    """
    存活检查端点
    用于Kubernetes等容器编排平台的存活探针
    """
    return {"status": "alive"}









