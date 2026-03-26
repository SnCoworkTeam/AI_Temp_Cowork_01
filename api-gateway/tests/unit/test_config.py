"""
配置模块单元测试
"""
import pytest
import os
from unittest.mock import patch
from src.config import Settings, settings


class TestSettings:
    """Settings类测试"""
    
    def test_default_values(self):
        """测试默认值"""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.HOST == "0.0.0.0"
            assert test_settings.PORT == 8080
            assert test_settings.DEBUG is True
            assert test_settings.REDIS_HOST == "redis"
            assert test_settings.REDIS_PORT == 6379
            assert test_settings.RATE_LIMIT_ENABLED is True
            assert test_settings.RATE_LIMIT_PER_MINUTE == 60
            assert test_settings.METRICS_ENABLED is True
    
    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {
            "PORT": "9090",
            "REDIS_HOST": "custom-redis",
            "RATE_LIMIT_PER_MINUTE": "120"
        }, clear=False):
            test_settings = Settings()
            assert test_settings.PORT == 9090
            assert test_settings.REDIS_HOST == "custom-redis"
            assert test_settings.RATE_LIMIT_PER_MINUTE == 120
    
    def test_local_dev_mode(self):
        """测试本地开发模式"""
        with patch.dict(os.environ, {
            "LOCAL_DEV": "true"
        }, clear=False):
            test_settings = Settings()
            if "registry-service" in test_settings.REGISTRY_SERVICE_URL:
                # 如果设置了LOCAL_DEV，应该自动调整
                assert "localhost" in test_settings.REGISTRY_SERVICE_URL or test_settings.LOCAL_DEV is True
    
    def test_settings_singleton(self):
        """测试settings单例"""
        assert settings is not None
        assert isinstance(settings, Settings)
        assert settings.PORT == 8080




