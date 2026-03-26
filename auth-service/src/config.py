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

    # IDaaS JWT / id_token 回调（GET 携带 token 或 id_token，RS256 验签）
    # 公钥：二选一。开发期可先配本机文件路径；容器部署时建议挂载项目内固定路径。
    SSO_ID_TOKEN_PUBLIC_KEY_PATH: Optional[str] = None
    SSO_ID_TOKEN_PUBLIC_KEY: Optional[str] = None
    # 与 IDP 约定一致时再开启校验（为空则跳过对应校验项）
    SSO_ID_TOKEN_ISSUER: str = ""
    SSO_ID_TOKEN_AUDIENCE: str = ""
    # 是否对 IDP 登录统一映射 admin 权限（当前按你的要求默认开启）
    SSO_ID_TOKEN_GRANT_ADMIN_PERMISSIONS: bool = True
    SSO_ID_TOKEN_ADMIN_USERNAME: str = "admin"
    # 浏览器重定向：成功/失败回到 Web UI（走 8080 时填对外网关或 Web 域名）
    SSO_POST_LOGIN_REDIRECT_BASE: str = "http://localhost:3000"
    SSO_TOKEN_LOGIN_DEFAULT_PATH: str = "/portal"
    
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









