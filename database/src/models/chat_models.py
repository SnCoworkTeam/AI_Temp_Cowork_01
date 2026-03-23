"""
对话和消息相关数据模型
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from .base import Base, TimestampMixin


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """消息状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Conversation(Base, TimestampMixin):
    """对话模型"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="新对话")
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False, index=True)
    meta_data = Column(JSON, default=dict, nullable=True)

    # 关系
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"


class Message(Base, TimestampMixin):
    """消息模型"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), nullable=False, index=True)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.COMPLETED, nullable=False, index=True)

    # AI相关字段
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0, nullable=True)
    execution_time = Column(Integer, default=0, nullable=True, comment="执行时间（毫秒）")

    # 工具调用和上下文
    tool_calls = Column(JSON, default=list, nullable=True)
    sources = Column(JSON, default=list, nullable=True, comment="引用的知识库来源")
    meta_data = Column(JSON, default=dict, nullable=True)

    # 关系
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"
