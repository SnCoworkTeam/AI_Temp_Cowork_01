"""
知识库服务配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8004
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 向量存储配置
    VECTOR_STORE_TYPE: str = "chroma"  # chroma 或 weaviate
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None
    
    # 嵌入模型配置
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # cpu 或 cuda
    EMBEDDING_DIMENSION: int = 384
    
    # 文档处理配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    CHUNK_SIZE: int = 800  # 文档分块大小（字符数）- 减小以降低内存占用
    CHUNK_OVERLAP: int = 150  # 分块重叠大小 - 相应减小

    # 文档处理超时配置（秒）
    DOCUMENT_PROCESSING_TIMEOUT: int = 1800  # 30分钟
    DOCUMENT_PARSING_BASE_TIMEOUT: int = 300  # 5分钟基础超时
    DOCUMENT_PARSING_TIMEOUT_PER_MB: int = 10  # 每MB增加10秒
    
    # 支持的文档类型
    SUPPORTED_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".txt", ".md", ".markdown"
    ]
    
    # 文档存储配置
    DOCUMENT_STORAGE_DIR: str = "./documents"
    
    # 知识图谱配置
    KNOWLEDGE_GRAPH_ENABLED: bool = True
    
    # 元数据服务配置
    METADATA_SERVICE_URL: str = "http://metadata-service:8005"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

