"""
聊天API测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session


@pytest.fixture
def mock_httpx_client():
    """模拟httpx异步客户端"""
    with patch('httpx.AsyncClient') as mock:
        yield mock


class TestChatAPI:
    """聊天API测试类"""

    def test_chat_create_new_conversation(self, client, mock_httpx_client):
        """测试创建新对话并发送消息"""
        # Mock agent-service响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": "这是AI的回复",
            "error": None
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        # 发送聊天请求（无conversation_id，将创建新对话）
        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            # Mock创建对话
            mock_conversation = MagicMock()
            mock_conversation.id = "new-conv-123"
            mock_service_instance.create_conversation.return_value = mock_conversation

            # Mock添加消息
            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-1"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-1"
            mock_service_instance.add_message.side_effect = [mock_user_msg, mock_ai_msg]

            # Mock MessageRepository.create for AI message
            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-final"
            mock_ai_msg_final.conversation_id = "new-conv-123"
            mock_ai_msg_final.role = "assistant"
            mock_ai_msg_final.content = "这是AI的回复"
            mock_ai_msg_final.created_at = "2026-02-05T10:00:00"
            mock_ai_msg_final.status = "completed"
            mock_ai_msg_final.model = "default"
            mock_ai_msg_final.tokens_used = 7
            mock_ai_msg_final.execution_time = 100
            mock_ai_msg_final.metadata = {"simulated": True}
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            # Mock获取消息历史
            mock_service_instance.get_messages.return_value = []

            # Mock _message_to_dict
            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-final",
                "conversation_id": "new-conv-123",
                "role": "assistant",
                "content": "这是AI的回复",
                "created_at": "2026-02-05T10:00:00",
                "status": "completed",
                "model": "default",
                "tokens_used": 7,
                "execution_time": 100,
                "metadata": {"simulated": True},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:00:00"
            }

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "你好，AI助手！",
                    "metadata": {}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "new-conv-123"
            assert "message" in data
            assert "suggestions" in data
            assert len(data["suggestions"]) > 0

    def test_chat_existing_conversation(self, client, mock_httpx_client):
        """测试在现有对话中发送消息"""
        # Mock agent-service响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": "继续对话的回复",
            "error": None
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            # Mock添加消息
            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-2"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-2"
            mock_service_instance.add_message.side_effect = [
                mock_user_msg, mock_ai_msg
            ]

            # Mock MessageRepository.create for AI message
            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-final-2"
            mock_ai_msg_final.conversation_id = "existing-conv-456"
            mock_ai_msg_final.role = "assistant"
            mock_ai_msg_final.content = "继续对话的回复"
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            # Mock获取消息历史
            mock_history_msg = MagicMock()
            mock_history_msg.role = "user"
            mock_history_msg.content = "之前的消息"
            mock_service_instance.get_messages.return_value = [
                mock_history_msg
            ]

            # Mock _message_to_dict
            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-final-2",
                "conversation_id": "existing-conv-456",
                "role": "assistant",
                "content": "继续对话的回复",
                "created_at": "2026-02-05T10:05:00",
                "status": "completed",
                "model": "default",
                "tokens_used": 7,
                "execution_time": 100,
                "metadata": {},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:05:00"
            }

            response = client.post(
                "/api/v1/chat",
                json={
                    "conversation_id": "existing-conv-456",
                    "message": "继续聊天",
                    "metadata": {}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "existing-conv-456"

    def test_chat_agent_service_error(self, client, mock_httpx_client):
        """测试agent-service错误处理"""
        # Mock agent-service返回错误
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            mock_conversation = MagicMock()
            mock_conversation.id = "conv-error-test"
            mock_service_instance.create_conversation.return_value = (
                mock_conversation
            )

            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-err"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-err"
            mock_service_instance.add_message.side_effect = [
                mock_user_msg, mock_ai_msg
            ]
            mock_service_instance.get_messages.return_value = []

            # Mock MessageRepository.create for AI message
            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-err-final"
            mock_ai_msg_final.content = "抱歉，AI服务暂时不可用。错误代码: 500"
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-err-final",
                "conversation_id": "conv-error-test",
                "role": "assistant",
                "content": "抱歉，AI服务暂时不可用。错误代码: 500",
                "created_at": "2026-02-05T10:10:00",
                "status": "completed",
                "model": "default",
                "tokens_used": 10,
                "execution_time": 100,
                "metadata": {},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:10:00"
            }

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "测试错误处理",
                    "metadata": {}
                }
            )

            # 应该返回降级响应
            assert response.status_code == 200
            data = response.json()
            assert "AI服务暂时不可用" in data["message"]["content"]

    def test_chat_agent_service_network_error(self, client, mock_httpx_client):
        """测试网络错误的降级处理"""
        # Mock网络异常
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = Exception("Connection timeout")
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            mock_conversation = MagicMock()
            mock_conversation.id = "conv-network-err"
            mock_service_instance.create_conversation.return_value = mock_conversation

            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-net-err"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-net-err"
            mock_service_instance.add_message.side_effect = [mock_user_msg, mock_ai_msg]
            mock_service_instance.get_messages.return_value = []

            # Mock MessageRepository.create for AI message
            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-net-err-final"
            fallback_content = "收到您的消息：测试网络错误\n\nAI助手功能正在处理中，请稍候..."
            mock_ai_msg_final.content = fallback_content
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-net-err-final",
                "conversation_id": "conv-network-err",
                "role": "assistant",
                "content": fallback_content,
                "created_at": "2026-02-05T10:15:00",
                "status": "completed",
                "model": "default",
                "tokens_used": 20,
                "execution_time": 100,
                "metadata": {},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:15:00"
            }

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "测试网络错误",
                    "metadata": {}
                }
            )

            # 应该返回降级响应
            assert response.status_code == 200
            data = response.json()
            assert "正在处理中" in data["message"]["content"]

    def test_chat_invalid_request(self, client):
        """测试无效请求"""
        response = client.post(
            "/api/v1/chat",
            json={}  # 缺少message字段
        )

        # 应该返回422验证错误
        assert response.status_code == 422

    def test_get_chat_history_success(self, client):
        """测试成功获取聊天历史"""
        with patch('src.routes.chat.ConversationService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_service_instance.get_conversation.return_value = {
                "conversation_id": "conv-history-123",
                "user_id": "test-user-id",
                "title": "Test Conversation",
                "messages": [
                    {
                        "message_id": "msg-1",
                        "role": "user",
                        "content": "Hello"
                    },
                    {
                        "message_id": "msg-2",
                        "role": "assistant",
                        "content": "Hi there!"
                    }
                ]
            }

            response = client.get("/api/v1/chat/history/conv-history-123")

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "conv-history-123"
            assert len(data["messages"]) == 2

    def test_get_chat_history_not_found(self, client):
        """测试获取不存在的对话历史"""
        from fastapi import HTTPException

        with patch('src.routes.chat.ConversationService') as mock_service:
            mock_service_instance = mock_service.return_value
            mock_service_instance.get_conversation.side_effect = HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

            # 期望返回404错误
            response = client.get("/api/v1/chat/history/non-existent-conv")

            # 应该返回404错误
            assert response.status_code == 404

    def test_chat_with_model_parameter(self, client, mock_httpx_client):
        """测试带模型参数的聊天"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": "使用特定模型的回复",
            "error": None
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            mock_conversation = MagicMock()
            mock_conversation.id = "conv-model-test"
            mock_service_instance.create_conversation.return_value = mock_conversation

            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-model"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-model"
            mock_service_instance.add_message.side_effect = [mock_user_msg, mock_ai_msg]
            mock_service_instance.get_messages.return_value = []

            # Mock MessageRepository.create for AI message
            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-model-final"
            mock_ai_msg_final.content = "使用特定模型的回复"
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-model-final",
                "conversation_id": "conv-model-test",
                "role": "assistant",
                "content": "使用特定模型的回复",
                "created_at": "2026-02-05T10:20:00",
                "status": "completed",
                "model": "gpt-4",
                "tokens_used": 12,
                "execution_time": 150,
                "metadata": {},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:20:00"
            }

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "使用GPT-4",
                    "model": "gpt-4",
                    "metadata": {}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "conv-model-test"

    def test_chat_with_empty_message(self, client):
        """测试发送空消息"""
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "",
                "metadata": {}
            }
        )

        # 应该返回422验证错误
        assert response.status_code == 422

    def test_chat_with_long_message(self, client, mock_httpx_client):
        """测试发送超长消息"""
        # Mock agent-service响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": "处理了长消息",
            "error": None
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = (
            mock_client_instance
        )

        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            mock_conversation = MagicMock()
            mock_conversation.id = "conv-long"
            mock_service_instance.create_conversation.return_value = (
                mock_conversation
            )

            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-long"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-long"
            mock_service_instance.add_message.side_effect = [
                mock_user_msg, mock_ai_msg
            ]
            mock_service_instance.get_messages.return_value = []

            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-long-final"
            mock_ai_msg_final.content = "处理了长消息"
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-long-final",
                "conversation_id": "conv-long",
                "role": "assistant",
                "content": "处理了长消息",
                "created_at": "2026-02-05T10:25:00",
                "status": "completed",
                "model": "default",
                "tokens_used": 50,
                "execution_time": 200,
                "metadata": {},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:25:00"
            }

            long_message = "这是一条很长的消息。" * 100

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": long_message,
                    "metadata": {}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_chat_with_custom_metadata(self, client, mock_httpx_client):
        """测试带自定义metadata的聊天"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": "处理了带元数据的消息",
            "error": None
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = (
            mock_client_instance
        )

        with patch('src.routes.chat.ConversationService') as mock_service, \
             patch('src.repositories.conversation_repository.MessageRepository') as mock_message_repo:

            mock_service_instance = mock_service.return_value
            mock_repo_instance = mock_message_repo.return_value

            mock_conversation = MagicMock()
            mock_conversation.id = "conv-meta"
            mock_service_instance.create_conversation.return_value = (
                mock_conversation
            )

            mock_user_msg = MagicMock()
            mock_user_msg.id = "msg-user-meta"
            mock_ai_msg = MagicMock()
            mock_ai_msg.id = "msg-ai-meta"
            mock_service_instance.add_message.side_effect = [
                mock_user_msg, mock_ai_msg
            ]
            mock_service_instance.get_messages.return_value = []

            mock_ai_msg_final = MagicMock()
            mock_ai_msg_final.id = "msg-ai-meta-final"
            mock_repo_instance.create.return_value = mock_ai_msg_final
            mock_repo_instance.delete.return_value = None

            mock_service_instance._message_to_dict.return_value = {
                "id": "msg-ai-meta-final",
                "conversation_id": "conv-meta",
                "role": "assistant",
                "content": "处理了带元数据的消息",
                "created_at": "2026-02-05T10:30:00",
                "status": "completed",
                "model": "default",
                "tokens_used": 15,
                "execution_time": 120,
                "metadata": {"source": "custom"},
                "tool_calls": None,
                "sources": None,
                "updated_at": "2026-02-05T10:30:00"
            }

            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "测试元数据",
                    "metadata": {"source": "custom", "priority": "high"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "conv-meta"
