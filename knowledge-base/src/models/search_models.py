"""
搜索相关数据模型
搜索历史、用户行为、反馈等
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    """搜索类型"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class FeedbackType(str, Enum):
    """反馈类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SearchHistory(BaseModel):
    """搜索历史模型"""
    search_id: str = Field(..., description="搜索ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    query: str = Field(..., description="搜索查询")
    search_type: SearchType = Field(..., description="搜索类型")
    results_count: int = Field(default=0, description="结果数量")
    result_document_ids: List[str] = Field(default_factory=list, description="结果文档ID列表")
    execution_time: float = Field(default=0.0, description="执行时间（秒）")
    filters: Dict[str, Any] = Field(default_factory=dict, description="搜索过滤条件")
    created_at: datetime = Field(..., description="搜索时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class UserBehavior(BaseModel):
    """用户行为模型"""
    behavior_id: str = Field(..., description="行为ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    action_type: str = Field(..., description="行为类型（search, view, download, share等）")
    target_type: str = Field(..., description="目标类型（document, chunk, node等）")
    target_id: str = Field(..., description="目标ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="行为上下文")
    created_at: datetime = Field(..., description="行为时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class SearchFeedback(BaseModel):
    """搜索反馈模型"""
    feedback_id: str = Field(..., description="反馈ID")
    search_id: str = Field(..., description="搜索ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    feedback_type: FeedbackType = Field(..., description="反馈类型")
    document_id: Optional[str] = Field(None, description="相关文档ID")
    relevance_score: Optional[int] = Field(None, ge=1, le=5, description="相关性评分（1-5）")
    comment: Optional[str] = Field(None, description="反馈评论")
    created_at: datetime = Field(..., description="反馈时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")









