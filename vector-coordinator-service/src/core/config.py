"""
向量协调服务配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8020
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3000",
    ]
    
    # 向量模型配置
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # cpu or cuda
    EMBEDDING_DIMENSION: int = 384
    
    # Qdrant配置
    QDRANT_HOST: str = "qdrant"  # Docker环境默认使用服务名，可通过环境变量覆盖
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "unified_vectors"
    USE_QDRANT: bool = True  # 是否使用Qdrant（如果不可用会自动降级到内存）
    QDRANT_INDEX_TYPE: str = "hnsw"  # 索引类型：hnsw, ivf, flat
    QDRANT_HNSW_M: int = 16  # HNSW参数M
    QDRANT_HNSW_EF_CONSTRUCT: int = 200  # HNSW参数ef_construct
    
    # Redis配置（用于L2缓存）
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 缓存配置
    CACHE_ENABLED: bool = True
    CACHE_L1_MAX_SIZE: int = 1000
    CACHE_L1_TTL: int = 300  # 5分钟
    CACHE_L2_TTL: int = 3600  # 1小时
    
    # 持久化策略配置
    PERSISTENCE_MODE: str = "hybrid"  # realtime, batch, hybrid
    BATCH_WRITE_INTERVAL: int = 120  # 批量写入间隔（秒）
    BATCH_WRITE_SIZE: int = 100  # 批量写入大小
    
    # 向量融合配置
    FUSION_STRATEGY: str = "weighted_average"  # weighted_average, attention, concatenate
    DEFAULT_WEIGHTS: dict = {
        "metadata": 0.4,
        "knowledge": 0.4,
        "permission": 0.2
    }
    
    # 向量相似度配置
    SIMILARITY_METRIC: str = "cosine"  # cosine, euclidean, dot
    SIMILARITY_THRESHOLD: float = 0.7
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()


