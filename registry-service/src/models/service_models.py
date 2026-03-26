"""
服务注册数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """服务状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """服务类型"""
    HTTP = "http"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


class ServiceRegistration(BaseModel):
    """服务注册请求"""
    name: str = Field(..., description="服务名称")
    host: str = Field(..., description="服务主机")
    port: int = Field(..., description="服务端口")
    service_type: ServiceType = Field(default=ServiceType.HTTP, description="服务类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="服务元数据")
    health_check_url: Optional[str] = Field(None, description="健康检查URL")
    tags: List[str] = Field(default_factory=list, description="服务标签")


class ServiceInfo(BaseModel):
    """服务信息"""
    service_id: str
    name: str
    host: str
    port: int
    service_type: ServiceType
    status: ServiceStatus
    metadata: Dict[str, Any]
    health_check_url: Optional[str]
    tags: List[str]
    registered_at: datetime
    last_heartbeat: datetime
    uptime_seconds: float


class HealthCheckResult(BaseModel):
    """健康检查结果"""
    service_id: str
    status: ServiceStatus
    response_time_ms: float
    checked_at: datetime
    error: Optional[str] = None
