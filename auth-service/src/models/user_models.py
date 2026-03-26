"""
用户数据模型
扩展用户模型，增加角色和权限字段
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(BaseModel):
    """用户模型"""
    user_id: str = Field(..., description="用户ID（唯一标识）")
    username: str = Field(..., description="用户名", min_length=1, max_length=100)
    email: EmailStr = Field(..., description="邮箱")
    display_name: Optional[str] = Field(None, description="显示名称", max_length=200)
    roles: List[str] = Field(default_factory=list, description="角色ID列表")
    permissions: List[str] = Field(default_factory=list, description="权限ID列表（直接分配的权限）")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., description="用户名", min_length=1, max_length=100)
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码", min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=200)
    roles: List[str] = Field(default_factory=list, description="角色ID列表")
    permissions: List[str] = Field(default_factory=list, description="权限ID列表")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, description="用户名", min_length=1, max_length=100)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, description="密码", min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=200)
    roles: Optional[List[str]] = Field(None, description="角色ID列表")
    permissions: Optional[List[str]] = Field(None, description="权限ID列表")
    status: Optional[UserStatus] = Field(None, description="用户状态")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class UserResponse(BaseModel):
    """用户响应"""
    user_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    roles: List[str]
    permissions: List[str]
    status: str
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserDetailResponse(UserResponse):
    """用户详情响应"""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    role_details: List[Dict[str, Any]] = Field(default_factory=list, description="角色详情")
    permission_details: List[Dict[str, Any]] = Field(default_factory=list, description="权限详情")


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserSearchParams(BaseModel):
    """用户搜索参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(None, description="搜索关键词（用户名、邮箱）")
    status: Optional[UserStatus] = Field(None, description="状态过滤")
    role: Optional[str] = Field(None, description="角色过滤")








