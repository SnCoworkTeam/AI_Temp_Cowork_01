"""
系统相关数据模型
系统配置、审计日志
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Index, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum

from .base import BaseModel, TimestampMixin


class ConfigCategory(str, Enum):
    """配置类别"""
    SYSTEM = "system"
    FEATURE = "feature"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"


class SystemConfig(BaseModel):
    """系统配置模型"""
    __tablename__ = "system_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="配置ID")
    key = Column(String(200), unique=True, nullable=False, index=True, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值")
    value_type = Column(String(50), nullable=False, default="string", comment="值类型（string, int, float, bool, json）")
    category = Column(SQLEnum(ConfigCategory), nullable=False, default=ConfigCategory.SYSTEM, comment="配置类别")
    description = Column(Text, nullable=True, comment="配置描述")
    is_encrypted = Column(Boolean, default=False, nullable=False, comment="是否加密")
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开")
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, key={self.key})>"


class AuditLog(BaseModel):
    """审计日志模型"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="日志ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True, comment="用户ID")
    action = Column(SQLEnum(AuditAction, native_enum=False, values_callable=lambda x: [e.value for e in AuditAction]), nullable=False, index=True, comment="操作类型")
    resource_type = Column(String(100), nullable=True, index=True, comment="资源类型")
    resource_id = Column(String(200), nullable=True, comment="资源ID")
    
    # 请求信息
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    request_path = Column(String(500), nullable=True, comment="请求路径")
    request_method = Column(String(10), nullable=True, comment="请求方法")
    
    # 详细信息
    details = Column(JSONB, nullable=True, comment="详细信息")
    result = Column(String(50), nullable=True, comment="操作结果（success, failure）")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间戳
    timestamp = Column(DateTime, nullable=False, index=True, comment="操作时间")
    
    __table_args__ = (
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"


class Notification(BaseModel):
    """用户通知模型"""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="通知ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    type = Column(String(50), nullable=False, index=True, comment="通知类型（plan_changed, critical_task_delayed等）")
    title = Column(String(200), nullable=False, comment="通知标题")
    message = Column(Text, nullable=False, comment="通知消息")
    link = Column(String(500), nullable=True, comment="跳转链接")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    is_read = Column(Boolean, default=False, nullable=False, index=True, comment="是否已读")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")
    
    __table_args__ = (
        Index('idx_notifications_user_read', 'user_id', 'is_read'),
        Index('idx_notifications_type', 'type'),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"

