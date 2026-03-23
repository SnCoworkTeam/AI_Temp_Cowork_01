"""
对话和消息相关的Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """消息状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageBase(BaseModel):
    """消息基础模型"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容", min_length=1)


class MessageCreate(MessageBase):
    """创建消息请求"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class Message(MessageBase):
    """消息响应模型"""
    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="对话ID")
    status: MessageStatus = Field(..., description="消息状态")
    model: Optional[str] = Field(None, description="使用的AI模型")
    tokens_used: Optional[int] = Field(None, description="使用的Token数量")
    execution_time: Optional[int] = Field(None, description="执行时间（毫秒）")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="知识库来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """对话基础模型"""
    title: str = Field(..., description="对话标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="对话描述")


class ConversationCreate(ConversationBase):
    """创建对话请求"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="对话元数据")


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = Field(None, description="对话标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="对话描述")
    is_archived: Optional[bool] = Field(None, description="是否归档")
    metadata: Optional[Dict[str, Any]] = Field(None, description="对话元数据")


class Conversation(ConversationBase):
    """对话响应模型"""
    id: str = Field(..., description="对话ID")
    user_id: str = Field(..., description="用户ID")
    is_archived: bool = Field(..., description="是否归档")
    metadata: Optional[Dict[str, Any]] = Field(None, description="对话元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    message_count: Optional[int] = Field(0, description="消息数量")

    class Config:
        from_attributes = True


class ConversationWithMessages(Conversation):
    """包含消息的对话响应"""
    messages: List[Message] = Field([], description="对话消息列表")


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[Conversation] = Field(..., description="对话列表")
    total: int = Field(..., ge=0, description="总数")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, description="每页数量")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    conversation_id: Optional[str] = Field(None, description="对话ID（如果不提供则创建新对话）")
    model: Optional[str] = Field(None, description="指定使用的AI模型")
    use_knowledge_base: bool = Field(True, description="是否使用知识库")
    metadata: Optional[Dict[str, Any]] = Field(None, description="请求元数据")


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: str = Field(..., description="对话ID")
    message: Message = Field(..., description="AI助手的回复消息")
    suggestions: Optional[List[str]] = Field(None, description="建议的后续问题")
