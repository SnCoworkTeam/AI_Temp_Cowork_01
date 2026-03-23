"""
配置管理
提供环境变量验证和默认值
"""
try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback for environments without pydantic-settings
    from pydantic import BaseModel  # type: ignore
    import os

    class BaseSettings(BaseModel):  # type: ignore
        """简化版 BaseSettings：从环境变量注入同名字段值"""

        def __init__(self, **values):
            env_values = {}
            fields = getattr(self.__class__, "model_fields", None) or getattr(self.__class__, "__fields__", {})
            for name in fields.keys():
                if name in os.environ and name not in values:
                    env_values[name] = os.environ[name]
            super().__init__(**{**env_values, **values})

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = True
            extra = "ignore"

from pydantic import Field, validator, field_validator
from typing import List, Optional, Dict, Any, Union
from functools import lru_cache
import os


class BaseConfig(BaseSettings):
    """基础配置类"""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略未定义的字段


class ServiceConfig(BaseConfig):
    """服务基础配置"""
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8000, ge=1, le=65535, description="服务端口")
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(default="standard", description="日志格式")
    LOG_FILE: Optional[str] = Field(default=None, description="日志文件路径")
    LOG_JSON: bool = Field(default=False, description="是否使用JSON格式")
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """验证日志格式"""
        valid_formats = ["standard", "json", "detailed"]
        if v.lower() not in valid_formats:
            raise ValueError(f"LOG_FORMAT must be one of {valid_formats}")
        return v.lower()


class DatabaseConfig(BaseConfig):
    """数据库配置"""
    
    # PostgreSQL配置
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL主机")
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL端口")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL用户名")
    POSTGRES_PASSWORD: str = Field(default="", description="PostgreSQL密码")
    POSTGRES_DB: str = Field(default="enterprise_ai", description="PostgreSQL数据库名")
    POSTGRES_POOL_SIZE: int = Field(default=10, ge=1, description="连接池大小")
    POSTGRES_MAX_OVERFLOW: int = Field(default=20, ge=0, description="连接池最大溢出")
    
    @property
    def postgres_url(self) -> str:
        """获取PostgreSQL连接URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def postgres_url_async(self) -> str:
        """获取PostgreSQL异步连接URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


class RedisConfig(BaseConfig):
    """Redis配置"""
    
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535, description="Redis端口")
    REDIS_DB: int = Field(default=0, ge=0, le=15, description="Redis数据库索引")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_SOCKET_TIMEOUT: float = Field(default=5.0, ge=0, description="Redis Socket超时")
    REDIS_POOL_SIZE: int = Field(default=10, ge=1, description="Redis连接池大小")
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class CORSConfig(BaseConfig):
    """CORS配置"""
    
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="允许的CORS源"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="允许凭证")
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="允许的HTTP方法"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="允许的请求头"
    )


class AIConfig(BaseConfig):
    """AI服务配置（支持OpenAI和DeepSeek等兼容OpenAI API的服务）"""
    
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="LLM API密钥（OpenAI或DeepSeek）")
    # LLM服务基础URL（可选，默认使用OpenAI官方API）
    # 使用DeepSeek时设置为: https://api.deepseek.com
    LLM_BASE_URL: Optional[str] = Field(default=None, description="LLM服务基础URL")
    # LLM模型名称（默认: gpt-4，使用DeepSeek时建议: deepseek-chat）
    LLM_MODEL: str = Field(default="gpt-4", description="LLM模型名称")
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    OPENAI_MAX_TOKENS: int = Field(default=2000, ge=1, description="最大token数")
    
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None, description="LangChain API密钥")
    LANGCHAIN_TRACING_V2: bool = Field(default=False, description="启用LangChain追踪")
    LANGCHAIN_PROJECT: Optional[str] = Field(default=None, description="LangChain项目名称")


class AppConfig(ServiceConfig, DatabaseConfig, RedisConfig, CORSConfig, AIConfig):
    """应用完整配置"""
    
    # 应用信息
    APP_NAME: str = Field(default="Enterprise AI Platform", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    ENVIRONMENT: str = Field(default="development", description="环境名称")
    
    # API配置
    API_V1_PREFIX: str = Field(default="/api", description="API v1前缀")
    API_TITLE: str = Field(default="Enterprise AI Platform API", description="API标题")
    
    # 安全配置
    SECRET_KEY: str = Field(default="change-me-in-production", description="密钥")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, description="访问令牌过期时间（分钟）")
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证环境名称"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v.lower()
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_config() -> AppConfig:
    """
    获取应用配置（单例模式）
    
    Returns:
        应用配置实例
    """
    return AppConfig()


def get_service_config() -> ServiceConfig:
    """获取服务配置"""
    return ServiceConfig()


def get_redis_config() -> RedisConfig:
    """获取Redis配置"""
    return RedisConfig()


def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return DatabaseConfig()
