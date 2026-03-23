"""
Registry Service配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """服务配置"""

    # 服务基本配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Redis配置
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 服务注册配置
    SERVICE_TTL: int = 60  # 服务TTL（秒）
    HEALTH_CHECK_INTERVAL: int = 10  # 健康检查间隔（秒）

    # 日志配置
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
