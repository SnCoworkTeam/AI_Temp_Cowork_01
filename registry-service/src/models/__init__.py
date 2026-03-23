"""
模型模块初始化
"""
from .service_models import (
    ServiceStatus,
    ServiceType,
    ServiceRegistration,
    ServiceInfo,
    HealthCheckResult
)

__all__ = [
    "ServiceStatus",
    "ServiceType",
    "ServiceRegistration",
    "ServiceInfo",
    "HealthCheckResult"
]
