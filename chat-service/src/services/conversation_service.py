"""
对话管理服务
"""
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy.orm import Session
# 导入database模块（通过sys.path设置）
import sys
from pathlib import Path
_database_src = str(Path(__file__).parent.parent.parent.parent / "database" / "src")
if _database_src not in sys.path:
    sys.path.insert(0, _database_src)

from models.chat_models import Conversation, Message, MessageRole, MessageStatus

from ..repositories.conversation_repository import ConversationRepository, MessageRepository
from luminaos_common.schemas.chat_schemas import (
    ConversationCreate, ConversationUpdate, Conversation as ConversationSchema,
    Message as MessageSchema, ConversationWithMessages
)
from luminaos_common.common.error_handler import AppError

logger = logging.getLogger("chat-service")


class ConversationService:
    """对话管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    def create_conversation(self, user_id: str, data: ConversationCreate) -> ConversationSchema:
        """创建新对话"""
        try:
            conversation = self.conversation_repo.create(
                user_id=user_id,
                title=data.title,
                description=data.description,
                metadata=data.metadata
            )

            return self._to_schema(conversation)
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}", exc_info=True)
            raise AppError(
                status_code=500,
                message="创建对话失败",
                details=str(e)
            )

    def get_conversation(self, conversation_id: str, user_id: str,
                          include_messages: bool = False) -> ConversationSchema:
        """获取对话详情"""
        conversation = self.conversation_repo.get_by_id(conversation_id, user_id)
        if not conversation:
            raise AppError(
                status_code=404,
                message="对话不存在",
                details=f"Conversation {conversation_id} not found"
            )

        if include_messages:
            messages = self.message_repo.get_conversation_messages(conversation_id)
            return ConversationWithMessages(
                **self._to_dict(conversation),
                messages=[self._message_to_dict(msg) for msg in messages]
            )

        return self._to_schema(conversation)

    def get_user_conversations(self, user_id: str, include_archived: bool = False,
                                page: int = 1, page_size: int = 20) -> tuple[List[ConversationSchema], int]:
        """获取用户的对话列表"""
        conversations, total = self.conversation_repo.get_user_conversations(
            user_id=user_id,
            include_archived=include_archived,
            page=page,
            page_size=page_size
        )

        conversation_schemas = []
        for conv in conversations:
            schema_dict = self._to_dict(conv)
            schema_dict['message_count'] = self.conversation_repo.get_message_count(conv.id)
            conversation_schemas.append(ConversationSchema(**schema_dict))

        return conversation_schemas, total

    def update_conversation(self, conversation_id: str, user_id: str,
                             data: ConversationUpdate) -> ConversationSchema:
        """更新对话"""
        update_data = data.model_dump(exclude_unset=True)
        conversation = self.conversation_repo.update(conversation_id, user_id, **update_data)

        if not conversation:
            raise AppError(
                status_code=404,
                message="对话不存在",
                details=f"Conversation {conversation_id} not found"
            )

        return self._to_schema(conversation)

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """删除对话"""
        success = self.conversation_repo.delete(conversation_id, user_id)
        if not success:
            raise AppError(
                status_code=404,
                message="对话不存在",
                details=f"Conversation {conversation_id} not found"
            )
        return True

    def add_message(self, conversation_id: str, user_id: str, role: MessageRole,
                     content: str, **kwargs) -> MessageSchema:
        """添加消息到对话"""
        # 验证对话存在且属于用户
        conversation = self.conversation_repo.get_by_id(conversation_id, user_id)
        if not conversation:
            raise AppError(
                status_code=404,
                message="对话不存在",
                details=f"Conversation {conversation_id} not found"
            )

        try:
            message = self.message_repo.create(
                conversation_id=conversation_id,
                role=role,
                content=content,
                **kwargs
            )
            return MessageSchema(**self._message_to_dict(message))
        except Exception as e:
            logger.error(f"Failed to add message: {str(e)}", exc_info=True)
            raise AppError(
                status_code=500,
                message="添加消息失败",
                details=str(e)
            )

    def get_messages(self, conversation_id: str, user_id: str,
                      limit: Optional[int] = None) -> List[MessageSchema]:
        """获取对话的消息列表"""
        # 验证对话存在且属于用户
        conversation = self.conversation_repo.get_by_id(conversation_id, user_id)
        if not conversation:
            raise AppError(
                status_code=404,
                message="对话不存在",
                details=f"Conversation {conversation_id} not found"
            )

        messages = self.message_repo.get_conversation_messages(conversation_id, limit)
        return [MessageSchema(**self._message_to_dict(msg)) for msg in messages]

    def _to_schema(self, conversation: Conversation) -> ConversationSchema:
        """转换为schema"""
        return ConversationSchema(**self._to_dict(conversation))

    def _to_dict(self, conversation: Conversation) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "description": conversation.description,
            "is_archived": conversation.is_archived,
            "metadata": conversation.metadata,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "message_count": 0
        }

    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """转换消息为字典"""
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "status": message.status,
            "model": message.model,
            "tokens_used": message.tokens_used,
            "execution_time": message.execution_time,
            "tool_calls": message.tool_calls,
            "sources": message.sources,
            "metadata": message.metadata,
            "created_at": message.created_at,
            "updated_at": message.updated_at
        }
