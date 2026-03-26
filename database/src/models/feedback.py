"""
反馈和查询日志数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel as Base, TimestampMixin


class Feedback(Base, TimestampMixin):
    """用户反馈数据模型"""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(255), nullable=False, index=True)
    query = Column(Text, nullable=False)
    feedback_type = Column(String(20), nullable=False)  # positive, negative
    result_id = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    extra_metadata = Column(JSONB, nullable=True)  # 重命名为extra_metadata避免与SQLAlchemy保留字冲突
    
    __table_args__ = (
        Index('idx_feedback_query_id', 'query_id'),
        Index('idx_feedback_user_id', 'user_id'),
        Index('idx_feedback_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, query_id='{self.query_id}', feedback_type='{self.feedback_type}')>"


class QueryLog(Base, TimestampMixin):
    """查询日志数据模型"""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(255), nullable=False, index=True)
    query = Column(Text, nullable=False)
    success = Column(String(10), nullable=False)  # true, false
    response_time_ms = Column(Integer, nullable=True)
    result_count = Column(Integer, nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    extra_metadata = Column(JSONB, nullable=True)  # 重命名为extra_metadata避免与SQLAlchemy保留字冲突
    
    __table_args__ = (
        Index('idx_query_log_query_id', 'query_id'),
        Index('idx_query_log_user_id', 'user_id'),
        Index('idx_query_log_created_at', 'created_at'),
        Index('idx_query_log_success', 'success'),
    )
    
    def __repr__(self):
        return f"<QueryLog(id={self.id}, query_id='{self.query_id}', success='{self.success}')>"

