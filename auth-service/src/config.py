"""
认证服务配置
"""
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8003  # 注意：8002已被workflow-engine使用，使用8003避免冲突
    DEBUG: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "http://43.143.139.197:3000",
        "http://43.143.139.197:8003",
        "*",  # 开发环境允许所有来源
    ]
    
    # SSO/OAuth配置
    SSO_CLIENT_ID: str = ""
    SSO_CLIENT_SECRET: str = ""
    SSO_AUTHORIZATION_URL: str = "https://sso.example.com/oauth2/authorize"
    SSO_TOKEN_URL: str = "https://sso.example.com/oauth2/token"
    SSO_USERINFO_URL: str = "https://sso.example.com/oauth2/userinfo"
    SSO_REDIRECT_URI: str = "http://localhost:8003/auth/sso/callback"
    SSO_SCOPES: List[str] = ["openid", "profile", "email"]
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7天
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 缓存配置（秒）
    CACHE_SESSION_TTL: int = 1800  # 30分钟
    CACHE_ACCESS_TOKEN_TTL: int = 3600  # 1小时
    CACHE_REFRESH_TOKEN_TTL: int = 604800  # 7天
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()









