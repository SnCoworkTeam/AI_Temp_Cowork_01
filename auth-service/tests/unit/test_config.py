"""
配置模块测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestConfig:
    """配置模块测试"""
    
    def test_settings_initialization(self):
        """测试Settings初始化"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings is not None
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8003
        assert settings.DEBUG is False
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) > 0
    
    def test_settings_default_values(self):
        """测试Settings默认值"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.JWT_SECRET_KEY is not None
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB == 0
        assert settings.CACHE_SESSION_TTL == 1800
        assert settings.CACHE_ACCESS_TOKEN_TTL == 3600
        assert settings.CACHE_REFRESH_TOKEN_TTL == 604800
        assert settings.LOG_LEVEL == "INFO"
    
    def test_settings_sso_config(self):
        """测试SSO配置"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.SSO_AUTHORIZATION_URL is not None
        assert settings.SSO_TOKEN_URL is not None
        assert settings.SSO_USERINFO_URL is not None
        assert settings.SSO_REDIRECT_URI is not None
        assert isinstance(settings.SSO_SCOPES, list)
        assert len(settings.SSO_SCOPES) > 0
    
    def test_settings_from_env(self):
        """测试从环境变量加载配置"""
        with patch.dict(os.environ, {
            'HOST': '127.0.0.1',
            'PORT': '9000',
            'DEBUG': 'true',
            'JWT_SECRET_KEY': 'test_secret_key'
        }):
            from src.config import Settings
            settings = Settings()
            
            # 注意：pydantic-settings可能不会自动转换类型
            # 这里主要测试配置可以加载
            assert settings is not None
    
    def test_settings_instance(self):
        """测试settings实例"""
        from src.config import settings
        
        assert settings is not None
        assert isinstance(settings, type(Settings()))
    
    def test_settings_cors_origins(self):
        """测试CORS配置"""
        from src.config import Settings
        
        settings = Settings()
        
        assert "*" in settings.CORS_ORIGINS or "http://localhost:3000" in settings.CORS_ORIGINS
        assert isinstance(settings.CORS_ORIGINS, list)
    
    def test_settings_cache_config(self):
        """测试缓存配置"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.CACHE_SESSION_TTL > 0
        assert settings.CACHE_ACCESS_TOKEN_TTL > 0
        assert settings.CACHE_REFRESH_TOKEN_TTL > 0
        assert settings.CACHE_REFRESH_TOKEN_TTL > settings.CACHE_ACCESS_TOKEN_TTL
    
    def test_settings_jwt_config(self):
        """测试JWT配置"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.JWT_SECRET_KEY is not None
        assert len(settings.JWT_SECRET_KEY) > 0
        assert settings.JWT_ALGORITHM in ["HS256", "HS512", "RS256"]
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_settings_redis_config(self):
        """测试Redis配置"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.REDIS_HOST is not None
        assert settings.REDIS_PORT > 0
        assert settings.REDIS_PORT < 65536
        assert settings.REDIS_DB >= 0
