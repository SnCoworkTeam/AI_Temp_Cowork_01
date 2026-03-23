"""
元数据服务配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3000",
    ]
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "enterprise_ai_platform"
    DB_ECHO: bool = False
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 元数据搜索配置
    SEARCH_INDEX_NAME: str = "metadata_index"
    SEARCH_MAX_RESULTS: int = 100
    SEARCH_DEFAULT_LIMIT: int = 20
    
    # 数据血缘配置
    LINEAGE_MAX_DEPTH: int = 10
    LINEAGE_CACHE_TTL: int = 3600  # 1小时
    
    # 数据质量配置
    QUALITY_CHECK_INTERVAL: int = 3600  # 1小时
    QUALITY_CACHE_TTL: int = 1800  # 30分钟
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略未定义的环境变量


settings = Settings()

