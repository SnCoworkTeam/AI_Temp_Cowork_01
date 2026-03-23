"""
API Gateway测试配置
"""
import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient

# 设置测试环境变量
os.environ.setdefault("REGISTRY_SERVICE_URL", "http://localhost:8000")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("METRICS_ENABLED", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")  # 测试时禁用限流
os.environ.setdefault("CIRCUIT_BREAKER_ENABLED", "false")  # 测试时禁用熔断
os.environ.setdefault("LOCAL_DEV", "true")

# 测试基础URL
BASE_URL = os.getenv("API_GATEWAY_BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """创建测试客户端（延迟导入以避免依赖问题）"""
    # 延迟导入以避免在导入时执行main.py的初始化
    try:
        from src.main import app
        with TestClient(app) as client:
            yield client
    except ImportError as e:
        pytest.skip(f"Failed to import app: {e}")


@pytest.fixture(scope="module")
def base_url() -> str:
    """返回基础URL"""
    return BASE_URL




