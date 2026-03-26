"""
对话管理API测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_conversation_service():
    """模拟对话服务"""
    with patch('src.routes.conversations.ConversationService') as mock:
        yield mock


class TestConversationsAPI:
    """对话管理API测试类"""

    def test_create_conversation_success(self, client, mock_conversation_service):
        """测试成功创建对话"""
        # 准备mock数据 - 符合Conversation schema
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.create_conversation.return_value = {
            "id": "conv-123",  # 使用id而不是conversation_id
            "user_id": "test-user-id",
            "title": "New Conversation",
            "description": None,
            "is_archived": False,
            "metadata": None,
            "created_at": "2026-02-05T09:00:00",
            "updated_at": "2026-02-05T09:00:00",
            "message_count": 0
        }

        # 发送请求
        response = client.post(
            "/api/v1/conversations",
            json={"title": "New Conversation"}
        )

        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "conv-123"  # 使用id
        assert data["title"] == "New Conversation"
        assert mock_service_instance.create_conversation.called

    def test_create_conversation_invalid_data(self, client):
        """测试使用无效数据创建对话"""
        response = client.post(
            "/api/v1/conversations",
            json={}  # 缺少required字段
        )

        # 应该返回422验证错误
        assert response.status_code == 422

    def test_list_conversations_success(self, client, mock_conversation_service):
        """测试成功获取对话列表"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_user_conversations.return_value = (
            [
                {
                    "id": "conv-1",
                    "user_id": "test-user-id",
                    "title": "Conversation 1",
                    "description": None,
                    "is_archived": False,
                    "metadata": None,
                    "created_at": "2026-02-05T09:00:00",
                    "updated_at": "2026-02-05T09:00:00",
                    "message_count": 0
                },
                {
                    "id": "conv-2",
                    "user_id": "test-user-id",
                    "title": "Conversation 2",
                    "description": None,
                    "is_archived": False,
                    "metadata": None,
                    "created_at": "2026-02-05T10:00:00",
                    "updated_at": "2026-02-05T10:00:00",
                    "message_count": 0
                }
            ],
            2  # total count
        )

        response = client.get("/api/v1/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["conversations"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_conversations_with_pagination(self, client, mock_conversation_service):
        """测试带分页的对话列表"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_user_conversations.return_value = ([], 0)

        response = client.get(
            "/api/v1/conversations",
            params={"page": 2, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    def test_get_conversation_success(self, client, mock_conversation_service):
        """测试成功获取对话详情"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_conversation.return_value = {
            "id": "conv-123",
            "user_id": "test-user-id",
            "title": "Test Conversation",
            "description": None,
            "is_archived": False,
            "metadata": None,
            "created_at": "2026-02-05T09:00:00",
            "updated_at": "2026-02-05T09:00:00",
            "message_count": 1,
            "messages": [
                {
                    "id": "msg-1",
                    "conversation_id": "conv-123",
                    "role": "user",
                    "content": "Hello",
                    "status": "completed",
                    "model": None,
                    "tokens_used": None,
                    "execution_time": None,
                    "tool_calls": None,
                    "sources": None,
                    "metadata": None,
                    "created_at": "2026-02-05T09:01:00",
                    "updated_at": "2026-02-05T09:01:00"
                }
            ]
        }

        response = client.get("/api/v1/conversations/conv-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "conv-123"
        assert len(data["messages"]) == 1

    def test_update_conversation_success(self, client, mock_conversation_service):
        """测试成功更新对话"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.update_conversation.return_value = {
            "id": "conv-123",
            "user_id": "test-user-id",
            "title": "Updated Title",
            "description": None,
            "is_archived": False,
            "metadata": None,
            "created_at": "2026-02-05T09:00:00",
            "updated_at": "2026-02-05T09:30:00",
            "message_count": 0
        }

        response = client.patch(
            "/api/v1/conversations/conv-123",
            json={"title": "Updated Title"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_delete_conversation_success(self, client, mock_conversation_service):
        """测试成功删除对话"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.delete_conversation.return_value = None

        response = client.delete("/api/v1/conversations/conv-123")

        assert response.status_code == 204
        assert mock_service_instance.delete_conversation.called

    def test_add_message_success(self, client, mock_conversation_service):
        """测试成功添加消息"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.add_message.return_value = {
            "id": "msg-123",
            "conversation_id": "conv-123",
            "role": "user",
            "content": "Hello, AI!",
            "status": "completed",
            "model": None,
            "tokens_used": None,
            "execution_time": None,
            "tool_calls": None,
            "sources": None,
            "metadata": {},
            "created_at": "2026-02-05T09:00:00",
            "updated_at": "2026-02-05T09:00:00"
        }

        response = client.post(
            "/api/v1/conversations/conv-123/messages",
            json={
                "role": "user",
                "content": "Hello, AI!"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "msg-123"
        assert data["content"] == "Hello, AI!"

    def test_add_message_invalid_role(self, client):
        """测试使用无效角色添加消息"""
        response = client.post(
            "/api/v1/conversations/conv-123/messages",
            json={
                "role": "invalid_role",
                "content": "Test"
            }
        )

        # 应该返回422验证错误
        assert response.status_code == 422

    def test_get_messages_success(self, client, mock_conversation_service):
        """测试成功获取消息列表"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_messages.return_value = [
            {
                "id": "msg-1",
                "conversation_id": "conv-123",
                "role": "user",
                "content": "Hello",
                "status": "completed",
                "model": None,
                "tokens_used": None,
                "execution_time": None,
                "tool_calls": None,
                "sources": None,
                "metadata": {},
                "created_at": "2026-02-05T09:00:00",
                "updated_at": "2026-02-05T09:00:00"
            },
            {
                "id": "msg-2",
                "conversation_id": "conv-123",
                "role": "assistant",
                "content": "Hi there!",
                "status": "completed",
                "model": None,
                "tokens_used": None,
                "execution_time": None,
                "tool_calls": None,
                "sources": None,
                "metadata": {},
                "created_at": "2026-02-05T09:00:01",
                "updated_at": "2026-02-05T09:00:01"
            }
        ]

        response = client.get("/api/v1/conversations/conv-123/messages")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"

    def test_get_messages_with_limit(self, client, mock_conversation_service):
        """测试带限制的消息列表"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_messages.return_value = []

        response = client.get(
            "/api/v1/conversations/conv-123/messages",
            params={"limit": 10}
        )

        assert response.status_code == 200
        # 验证limit参数被传递
        args, kwargs = mock_service_instance.get_messages.call_args
        assert args[2] == 10  # limit参数

    def test_list_conversations_include_archived(self, client, mock_conversation_service):
        """测试列出包含已归档的对话"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_user_conversations.return_value = ([], 0)

        response = client.get(
            "/api/v1/conversations?include_archived=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data

    def test_create_conversation_with_all_fields(self, client, mock_conversation_service):
        """测试创建包含所有字段的对话"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.create_conversation.return_value = {
            "id": "conv-full",
            "user_id": "test-user-id",
            "title": "Full Conversation",
            "description": "Full description",
            "is_archived": False,
            "metadata": {"key1": "value1", "key2": "value2"},
            "created_at": "2026-02-05T09:00:00",
            "updated_at": "2026-02-05T09:00:00",
            "message_count": 0
        }

        response = client.post(
            "/api/v1/conversations",
            json={
                "title": "Full Conversation",
                "description": "Full description",
                "metadata": {"key1": "value1", "key2": "value2"}
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Full description"
        assert data["metadata"] == {"key1": "value1", "key2": "value2"}

    def test_update_conversation_partial(self, client, mock_conversation_service):
        """测试部分更新对话（只更新title）"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.update_conversation.return_value = {
            "id": "conv-123",
            "user_id": "test-user-id",
            "title": "Partially Updated",
            "description": "Original description",
            "is_archived": False,
            "metadata": None,
            "created_at": "2026-02-05T09:00:00",
            "updated_at": "2026-02-05T09:10:00",
            "message_count": 0,
            "status": "active"
        }

        response = client.patch(
            "/api/v1/conversations/conv-123",
            json={"title": "Partially Updated"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Partially Updated"

    def test_get_messages_empty_conversation(self, client, mock_conversation_service):
        """测试获取空对话的消息列表"""
        mock_service_instance = mock_conversation_service.return_value
        mock_service_instance.get_messages.return_value = []

        response = client.get("/api/v1/conversations/conv-empty/messages")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
        assert isinstance(data, list)
