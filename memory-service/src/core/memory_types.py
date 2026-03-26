"""
记忆类型定义
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, List, Optional
import time
import uuid


class MemoryType(str, Enum):
    """记忆类型枚举"""
    SHORT_TERM = "short_term"      # 会话记忆（短期）
    LONG_TERM = "long_term"        # 长期记忆
    EPISODIC = "episodic"          # 事件记忆
    SEMANTIC = "semantic"          # 语义记忆
    PROCEDURAL = "procedural"      # 程序记忆（执行模式）


class MemoryRecord(BaseModel):
    """记忆记录模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="用户ID")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    type: MemoryType = Field(..., description="记忆类型")
    content: dict = Field(..., description="记忆内容")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="记忆重要性 0-1")
    access_count: int = Field(0, description="访问次数")
    last_accessed: float = Field(default_factory=time.time, description="最后访问时间")
    created_at: float = Field(default_factory=time.time, description="创建时间")
    metadata: Optional[dict] = Field(None, description="元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "mem_123",
                "user_id": "user_456",
                "agent_id": "agent_789",
                "session_id": "session_abc",
                "type": "short_term",
                "content": {
                    "user_input": "我叫张三",
                    "agent_response": "你好张三！",
                    "timestamp": 1234567890.0
                },
                "importance": 0.7,
                "access_count": 3,
                "last_accessed": 1234567890.0,
                "created_at": 1234567800.0
            }
        }


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="搜索查询")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    memory_types: Optional[List[MemoryType]] = Field(None, description="记忆类型过滤")
    limit: int = Field(10, ge=1, le=100, description="返回数量限制")
    min_importance: float = Field(0.0, ge=0.0, le=1.0, description="最小重要性")


class MemoryStoreRequest(BaseModel):
    """记忆存储请求"""
    user_id: str = Field(..., description="用户ID")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    type: MemoryType = Field(..., description="记忆类型")
    content: dict = Field(..., description="记忆内容")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="记忆重要性")
    metadata: Optional[dict] = Field(None, description="元数据")
    ttl: Optional[int] = Field(None, description="过期时间（秒），仅用于短期记忆")




