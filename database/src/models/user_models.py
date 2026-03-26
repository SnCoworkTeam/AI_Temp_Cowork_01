"""
用户相关数据模型
用户、角色、权限管理
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, Table, Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum

from .base import BaseModel, TimestampMixin


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# 用户-角色关联表
user_role_table = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now(), nullable=False)
)

# 角色-权限关联表
role_permission_table = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now(), nullable=False)
)


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="用户ID")
    username = Column(String(100), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(200), nullable=True, comment="全名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    status = Column(SQLEnum(UserStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=UserStatus.ACTIVE.value, nullable=False, comment="用户状态")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(50), nullable=True, comment="最后登录IP")
    user_metadata = Column(JSONB, nullable=True, default=dict, comment="用户元数据")
    
    # 关系
    roles = relationship("Role", secondary=user_role_table, back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Role(BaseModel):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="角色ID")
    code = Column(String(100), unique=True, nullable=False, index=True, comment="角色代码")
    name = Column(String(200), nullable=False, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    is_system = Column(Boolean, default=False, nullable=False, comment="是否系统角色")
    
    # 关系
    users = relationship("User", secondary=user_role_table, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permission_table, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, code={self.code})>"


class Permission(BaseModel):
    """权限模型"""
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="权限ID")
    code = Column(String(100), unique=True, nullable=False, index=True, comment="权限代码")
    name = Column(String(200), nullable=False, comment="权限名称")
    description = Column(Text, nullable=True, comment="权限描述")
    resource = Column(String(100), nullable=True, comment="资源类型")
    action = Column(String(100), nullable=True, comment="操作类型")
    
    # 关系
    roles = relationship("Role", secondary=role_permission_table, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, code={self.code})>"


class UserSession(BaseModel):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="会话ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, comment="用户ID")
    access_token = Column(String(500), nullable=True, comment="访问令牌")
    refresh_token = Column(String(500), nullable=True, comment="刷新令牌")
    ip_address = Column(String(50), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否活跃")
    
    # 关系
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"

