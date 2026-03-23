"""
健康检查路由
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["健康检查"])


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        service="memory-service",
        version="1.0.0"
    )




