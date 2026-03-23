"""
配置管理
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Dict, Any, Union
import json
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    
    # CORS配置（使用字符串类型，通过属性解析）
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    def get_cors_origins(self) -> List[str]:
        """
        解析CORS_ORIGINS配置为列表
        支持逗号分隔的字符串格式
        """
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
        elif isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        else:
            return ["http://localhost:3000", "http://localhost:3001"]
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 工作流引擎配置
    WORKFLOW_ENGINE_URL: str = "http://workflow-engine:8002"
    
    # 知识库服务配置
    KNOWLEDGE_BASE_URL: str = "http://knowledge-base:8004"
    
    # 元数据服务配置
    METADATA_SERVICE_URL: str = "http://metadata-service:8005"
    
    # MCP服务器配置（JSON格式字符串）
    MCP_SERVERS: str = "[]"
    
    # 工具自动刷新配置
    AUTO_REFRESH_TOOLS: bool = True
    TOOL_REFRESH_INTERVAL: int = 300  # 5分钟
    
    # 连接池配置
    MCP_CONNECTION_POOL_SIZE: int = 5
    MCP_MAX_RETRIES: int = 3
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # SMTP邮件配置
    SMTP_SERVER: str = "smtp.163.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: str = "false"
    SMTP_USE_SSL: str = "true"

    # MinIO 对象存储
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = ""
    MINIO_SECURE: bool = True
    MINIO_REGION: str | None = None
    
    def get_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        解析MCP服务器配置
        
        Returns:
            MCP服务器配置列表
        """
        try:
            if not self.MCP_SERVERS or self.MCP_SERVERS == "[]":
                return []
            return json.loads(self.MCP_SERVERS)
        except json.JSONDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse MCP_SERVERS config: {e}")
            return []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

