"""
配置管理
"""
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # 如果pydantic_settings不可用，使用简单的类
    import os
    class BaseSettings:
        def __init__(self):
            self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
            self.LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
            self.LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
            self.HOST = os.getenv("HOST", "0.0.0.0")
            self.PORT = int(os.getenv("PORT", "8002"))
            self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"

from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://43.143.139.197:3000",
        "http://43.143.139.197:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # LangChain配置
    OPENAI_API_KEY: str = ""
    # LLM服务基础URL（可选，默认使用OpenAI官方API）
    # 使用DeepSeek时设置为: https://api.deepseek.com
    LLM_BASE_URL: str = ""
    # LLM模型名称（默认: deepseek-chat，使用DeepSeek时建议: deepseek-chat）
    LLM_MODEL: str = "deepseek-chat"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = False
    
    # MCP Gateway配置
    MCP_GATEWAY_URL: str = "http://mcp-gateway:8001"
    
    # 知识库服务配置
    KNOWLEDGE_BASE_URL: str = "http://knowledge-base:8004"
    
    # 元数据服务配置
    METADATA_SERVICE_URL: str = "http://metadata-service:8005"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

