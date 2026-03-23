"""
对话数据访问层
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
import uuid
from datetime import datetime

# 导入database模块（通过sys.path设置）
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
_database_src = str(project_root / "database" / "src")
if _database_src not in sys.path:
    sys.path.insert(0, _database_src)

from database.src.models.chat_models import Conversation, Message, MessageRole, MessageStatus


class ConversationRepository:
    """对话仓库"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, title: str, description: Optional[str] = None,
               metadata: Optional[dict] = None) -> Conversation:
        """创建对话"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: str, user_id: Optional[str] = None) -> Optional[Conversation]:
        """根据ID获取对话"""
        query = self.db.query(Conversation).filter(Conversation.id == conversation_id)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        return query.first()

    def get_user_conversations(self, user_id: str, include_archived: bool = False,
                                 page: int = 1, page_size: int = 20) -> tuple[List[Conversation], int]:
        """获取用户的对话列表"""
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)

        if not include_archived:
            query = query.filter(Conversation.is_archived == False)

        # 获取总数
        total = query.count()

        # 分页
        conversations = (
            query
            .order_by(Conversation.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return conversations, total

    def update(self, conversation_id: str, user_id: str, **kwargs) -> Optional[Conversation]:
        """更新对话"""
        conversation = self.get_by_id(conversation_id, user_id)
        if not conversation:
            return None

        for key, value in kwargs.items():
            if hasattr(conversation, key) and value is not None:
                setattr(conversation, key, value)

        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete(self, conversation_id: str, user_id: str) -> bool:
        """删除对话"""
        conversation = self.get_by_id(conversation_id, user_id)
        if not conversation:
            return False

        self.db.delete(conversation)
        self.db.commit()
        return True

    def get_message_count(self, conversation_id: str) -> int:
        """获取对话的消息数量"""
        return self.db.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id
        ).scalar() or 0


class MessageRepository:
    """消息仓库"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, conversation_id: str, role: MessageRole, content: str,
               status: MessageStatus = MessageStatus.COMPLETED,
               model: Optional[str] = None, tokens_used: Optional[int] = None,
               execution_time: Optional[int] = None, tool_calls: Optional[list] = None,
               sources: Optional[list] = None, metadata: Optional[dict] = None) -> Message:
        """创建消息"""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            status=status,
            model=model,
            tokens_used=tokens_used,
            execution_time=execution_time,
            tool_calls=tool_calls or [],
            sources=sources or [],
            metadata=metadata or {}
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # 更新对话的updated_at
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            self.db.commit()

        return message

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """根据ID获取消息"""
        return self.db.query(Message).filter(Message.id == message_id).first()

    def get_conversation_messages(self, conversation_id: str,
                                   limit: Optional[int] = None) -> List[Message]:
        """获取对话的消息列表"""
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def update_status(self, message_id: str, status: MessageStatus) -> Optional[Message]:
        """更新消息状态"""
        message = self.get_by_id(message_id)
        if not message:
            return None

        message.status = status
        message.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete(self, message_id: str) -> bool:
        """删除消息"""
        message = self.get_by_id(message_id)
        if not message:
            return False

        self.db.delete(message)
        self.db.commit()
        return True
