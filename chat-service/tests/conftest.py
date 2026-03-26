"""
Chat Service 测试配置
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 添加shared_libs和database到路径
shared_libs = project_root.parent / "shared_libs"
database_root = project_root.parent / "database"
database_src = database_root / "src"

if str(shared_libs) not in sys.path:
    sys.path.insert(0, str(shared_libs))
if str(database_root) not in sys.path:
    sys.path.insert(0, str(database_root))
if str(database_src) not in sys.path:
    sys.path.insert(0, str(database_src))


@pytest.fixture
def client():
    """创建测试客户端"""
    from src.main import app
    return TestClient(app)


@pytest.fixture
def mock_conversation_data():
    """模拟对话数据"""
    return {
        "conversation_id": "conv-123",
        "user_id": "user-456",
        "title": "Test Conversation",
        "created_at": "2026-02-05T09:00:00",
        "updated_at": "2026-02-05T09:00:00",
        "messages": []
    }


@pytest.fixture
def mock_message_data():
    """模拟消息数据"""
    return {
        "message_id": "msg-789",
        "conversation_id": "conv-123",
        "role": "user",
        "content": "Hello, AI!",
        "created_at": "2026-02-05T09:00:00"
    }
