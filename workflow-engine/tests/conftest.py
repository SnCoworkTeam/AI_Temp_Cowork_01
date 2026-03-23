"""
Workflow Engine测试配置
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.fixture
def sample_workflow_data():
    """示例工作流数据"""
    return {
        "name": "test_workflow",
        "description": "Test workflow",
        "version": "1.0.0",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "name": "开始"
            },
            {
                "id": "end",
                "type": "end",
                "name": "结束"
            }
        ],
        "connections": [
            {
                "source": "start",
                "target": "end"
            }
        ],
        "start_node_id": "start",
        "end_node_ids": ["end"]
    }


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.add = Mock()
    session.commit = Mock()
    session.flush = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端"""
    client = AsyncMock()
    client.get.return_value = None
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.smembers.return_value = []
    client.sadd = AsyncMock()
    client.srem = AsyncMock()
    client.expire = AsyncMock()
    return client

