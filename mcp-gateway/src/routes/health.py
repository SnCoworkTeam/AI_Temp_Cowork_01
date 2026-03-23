"""
健康检查路由
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field

from ..tools import tool_registry

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态", example="healthy")
    service: str = Field(..., description="服务名称", example="mcp-gateway")
    timestamp: str = Field(..., description="检查时间", example="2024-01-01T00:00:00")
    version: str = Field(..., description="服务版本", example="1.0.0")
    tools_count: int = Field(..., description="已注册工具数量", example=5)
    active_tools_count: int = Field(..., description="活跃工具数量", example=5)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="返回服务健康状态和基本信息",
    tags=["Health"]
)
async def health_check() -> HealthResponse:
    """
    健康检查端点
    
    返回服务状态、版本信息和工具统计
    """
    return HealthResponse(
        status="healthy",
        service="mcp-gateway",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        tools_count=tool_registry.get_tool_count(),
        active_tools_count=tool_registry.get_active_tool_count()
    )


@router.get(
    "/health/ready",
    response_model=Dict[str, Any],
    summary="就绪检查",
    description="就绪检查端点，用于Kubernetes等容器编排平台的就绪探针",
    tags=["Health"]
)
async def readiness_check() -> Dict[str, Any]:
    """
    就绪检查端点
    
    检查服务是否准备好接收请求
    - 检查工具注册表是否可用
    """
    # 检查工具注册表
    try:
        tool_registry.get_tool_count()
        return {
            "status": "ready",
            "checks": {
                "tool_registry": "ok"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        }


@router.get(
    "/health/live",
    response_model=Dict[str, Any],
    summary="存活检查",
    description="存活检查端点，用于Kubernetes等容器编排平台的存活探针",
    tags=["Health"]
)
async def liveness_check() -> Dict[str, Any]:
    """
    存活检查端点
    
    检查服务是否还在运行
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }

