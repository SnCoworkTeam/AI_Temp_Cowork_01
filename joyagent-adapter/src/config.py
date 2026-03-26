"""
JoyAgent Adapter Service Configuration

This module handles configuration management for the JoyAgent adapter service,
integrating JoyAgent-JDGenie with our enterprise AI platform.
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Configuration settings for JoyAgent Adapter Service"""

    # Service Configuration
    service_name: str = "joyagent-adapter"
    service_port: int = 8007
    service_host: str = "0.0.0.0"
    debug: bool = False
    log_level: str = "info"

    # JoyAgent-JDGenie Configuration
    joyagent_host: str = "joyagent-jdgenie"
    joyagent_port: int = 8080
    joyagent_ui_port: int = 3000
    joyagent_client_port: int = 1601
    joyagent_api_timeout: int = 300

    # Database Configuration (PostgreSQL)
    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "enterprise_ai_platform"

    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Service Discovery (Consul)
    consul_host: str = "registry-service"
    consul_port: int = 8500
    consul_token: Optional[str] = None

    # Platform Integration URLs
    mcp_gateway_url: str = "http://mcp-gateway:8001"
    workflow_engine_url: str = "http://workflow-engine:8002"
    auth_service_url: str = "http://auth-service:8003"
    knowledge_base_url: str = "http://knowledge-base:8004"
    metadata_service_url: str = "http://metadata-service:8005"
    api_gateway_url: str = "http://api-gateway:8080"

    # AI Configuration
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    openai_api_key: Optional[str] = None

    # JoyAgent Task Configuration
    max_concurrent_tasks: int = 10
    task_timeout: int = 600  # 10 minutes
    task_retry_count: int = 3
    task_retry_delay: int = 5

    # Context Management
    context_max_size: int = 100
    context_ttl: int = 3600  # 1 hour

    # Security
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Performance
    worker_processes: int = 1
    max_request_size: int = 100 * 1024 * 1024  # 100MB

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "JOYAGENT_ADAPTER_"
        case_sensitive = False


# Create global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get PostgreSQL database URL"""
    return f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"


def get_redis_url() -> str:
    """Get Redis URL"""
    if settings.redis_password:
        return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def get_joyagent_base_url() -> str:
    """Get JoyAgent backend API base URL"""
    return f"http://{settings.joyagent_host}:{settings.joyagent_port}"


def get_joyagent_client_url() -> str:
    """Get JoyAgent Python client URL"""
    return f"http://{settings.joyagent_host}:{settings.joyagent_client_port}"


def get_joyagent_ui_url() -> str:
    """Get JoyAgent frontend UI URL"""
    return f"http://{settings.joyagent_host}:{settings.joyagent_ui_port}"