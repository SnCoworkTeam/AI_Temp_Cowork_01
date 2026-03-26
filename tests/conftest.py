"""
Pytest配置和共享fixtures
"""
import pytest
import asyncio
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Pytest配置
def pytest_configure(config):
    """Pytest配置钩子"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试标记"
    )
    config.addinivalue_line(
        "markers", "security: 安全测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )


# 事件循环fixture（用于异步测试）
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 数据库fixtures
@pytest.fixture(scope="function")
def db_session():
    """数据库会话fixture"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 使用内存数据库进行测试
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    
    # 创建表
    from database.src.models.base import Base
    Base.metadata.create_all(engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session():
    """异步数据库会话fixture"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # 使用异步SQLite（需要aiosqlite）
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # 创建表
    from database.src.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()


# Redis fixtures
@pytest.fixture(scope="function")
def redis_client():
    """Redis客户端fixture（使用fakeredis）"""
    try:
        import fakeredis
        client = fakeredis.FakeStrictRedis()
        yield client
        client.flushall()
    except ImportError:
        # 如果没有fakeredis，返回mock
        mock_redis = Mock()
        # 添加常用方法
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis.delete = Mock(return_value=0)
        yield mock_redis


@pytest.fixture(scope="function")
async def async_redis_client():
    """异步Redis客户端fixture"""
    try:
        import fakeredis.aioredis
        client = fakeredis.aioredis.FakeRedis()
        yield client
        await client.flushall()
        await client.close()
    except ImportError:
        # 如果没有fakeredis，返回mock
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=0)
        yield mock_redis


# HTTP客户端fixtures
@pytest.fixture
def http_client():
    """HTTP客户端fixture"""
    from shared_libs.common.http_client import HTTPClient
    
    client = HTTPClient(base_url="http://test-server")
    yield client


@pytest.fixture
async def async_http_client():
    """异步HTTP客户端fixture"""
    import httpx
    
    async with httpx.AsyncClient(base_url="http://test-server") as client:
        yield client


# FastAPI应用fixtures
@pytest.fixture
def test_app():
    """测试用FastAPI应用"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI(title="Test App")
    
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    client = TestClient(app)
    yield client


@pytest.fixture
async def async_test_app():
    """异步测试用FastAPI应用"""
    from fastapi import FastAPI
    from httpx import AsyncClient
    
    app = FastAPI(title="Test App")
    
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# 认证fixtures
@pytest.fixture
def mock_user():
    """模拟用户"""
    return {
        "id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read"]
    }


@pytest.fixture
def auth_token(mock_user):
    """认证token fixture"""
    from shared_libs.common.config import get_settings
    
    # 这里可以生成真实的JWT token或使用mock
    # 简化版本返回mock token
    return "mock-auth-token"


@pytest.fixture
def authenticated_client(test_app, auth_token):
    """已认证的客户端"""
    client = test_app
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


# 测试数据fixtures
@pytest.fixture
def sample_workflow_data():
    """示例工作流数据"""
    return {
        "name": "test_workflow",
        "description": "Test workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "node1",
                "type": "start",
                "position": {"x": 0, "y": 0}
            },
            {
                "id": "node2",
                "type": "llm",
                "position": {"x": 100, "y": 0},
                "config": {
                    "model": "gpt-3.5-turbo",
                    "prompt": "Hello, world!"
                }
            }
        ],
        "connections": [
            {
                "source": "node1",
                "target": "node2"
            }
        ],
        "config": {}
    }


@pytest.fixture
def sample_tool_data():
    """示例工具数据"""
    return {
        "name": "test_tool",
        "description": "Test tool",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter"
                }
            },
            "required": ["input"]
        }
    }


@pytest.fixture
def sample_document_data():
    """示例文档数据"""
    return {
        "title": "Test Document",
        "content": "This is a test document",
        "type": "text",
        "metadata": {
            "author": "Test Author",
            "tags": ["test", "example"]
        }
    }


# 环境变量fixtures
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """模拟环境变量"""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key-32-chars-min")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("DEBUG", "true")


# 清理fixtures
@pytest.fixture(autouse=True)
def cleanup():
    """测试后清理"""
    yield
    # 清理逻辑可以放在这里
    pass


# 性能测试fixtures
@pytest.fixture
def performance_thresholds():
    """性能阈值配置"""
    return {
        "api_response_time": 0.5,  # 秒
        "database_query_time": 0.1,  # 秒
        "memory_usage_mb": 500,  # MB
        "cpu_usage_percent": 80  # %
    }


# 安全测试fixtures
@pytest.fixture
def security_test_cases():
    """安全测试用例"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd"
        ]
    }

