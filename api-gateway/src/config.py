"""
API Gateway配置
"""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any


class Settings(BaseSettings):
    """API Gateway配置"""

    # 服务基本配置
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True

    # Redis配置
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 服务注册中心配置
    REGISTRY_SERVICE_URL: str = "http://registry-service:8000"

    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # 熔断配置
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60

    # 负载均衡策略
    LOAD_BALANCE_STRATEGY: str = "round_robin"  # round_robin, random, least_connections

    # 超时配置
    REQUEST_TIMEOUT: int = 30

    # 重试配置
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 认证配置
    AUTH_ENABLED: bool = True
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"

    # 监控配置
    METRICS_ENABLED: bool = True
    TRACING_ENABLED: bool = True

    # 智能路由配置
    INTELLIGENT_ROUTING_ENABLED: bool = True
    INTELLIGENT_ROUTER_USE_LLM: bool = False  # 是否使用LLM进行意图识别（默认使用规则匹配）

    # 本地开发模式配置
    LOCAL_DEV: bool = False  # 本地开发模式：使用 localhost 而非 Docker 服务名
    USE_LOCALHOST: bool = False  # 别名，与 LOCAL_DEV 功能相同

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 如果设置了 LOCAL_DEV 或 USE_LOCALHOST，自动调整 REGISTRY_SERVICE_URL
if settings.LOCAL_DEV or settings.USE_LOCALHOST:
    if "registry-service" in settings.REGISTRY_SERVICE_URL:
        settings.REGISTRY_SERVICE_URL = "http://localhost:8000"
