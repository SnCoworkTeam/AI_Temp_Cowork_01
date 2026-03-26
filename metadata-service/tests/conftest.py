"""
测试配置文件
提供测试用的fixtures和测试环境设置
"""
import pytest
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main import app
from src.core.database import get_db
from database.src.models.base import Base

# 测试数据库配置
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://test_user:test_pass@localhost:5432/test_metadata_db"
)

# 使用SQLite内存数据库进行快速测试（可选）
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"
if USE_SQLITE:
    TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """创建测试数据库引擎"""
    if USE_SQLITE:
        engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # 清理
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(test_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass  # 会话在test_session fixture中管理
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_test_data(test_session):
    """每个测试后清理数据"""
    yield
    
    # 清理测试数据
    try:
        from src.models.workflow_version import WorkflowVersionTag, WorkflowVersion
        from src.models.workflow_metadata import WorkflowMetadata
        from sqlalchemy import delete
        
        # 删除所有测试数据（按依赖顺序）
        test_session.execute(delete(WorkflowVersionTag))
        test_session.execute(delete(WorkflowVersion))
        test_session.execute(delete(WorkflowMetadata))
        test_session.commit()
    except Exception as e:
        test_session.rollback()
        # 如果表不存在，忽略错误
        pass
