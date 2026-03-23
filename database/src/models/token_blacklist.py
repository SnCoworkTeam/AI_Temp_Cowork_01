"""
令牌黑名单数据模型
用于存储已撤销的JWT令牌
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import Base, TimestampMixin


class TokenBlacklist(Base, TimestampMixin):
    """令牌黑名单模型"""
    
    __tablename__ = "token_blacklist"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="主键ID"
    )
    
    token_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="令牌唯一标识（SHA256哈希）"
    )
    
    token_type = Column(
        String(20),
        nullable=False,
        comment="令牌类型：access或refresh"
    )
    
    user_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="令牌过期时间"
    )
    
    revoked_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="撤销时间"
    )
    
    reason = Column(
        Text,
        nullable=True,
        comment="撤销原因：logout, password_change, security_breach等"
    )
    
    # 创建复合索引以提高查询性能
    __table_args__ = (
        Index('idx_token_blacklist_user_expires', 'user_id', 'expires_at'),
        Index('idx_token_blacklist_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<TokenBlacklist {self.token_id[:16]}... ({self.token_type})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "token_id": self.token_id,
            "token_type": self.token_type,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

