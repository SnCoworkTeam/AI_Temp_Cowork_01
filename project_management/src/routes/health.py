"""
健康检查路由
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(status="healthy", service="project-management")
