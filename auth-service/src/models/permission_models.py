"""
权限数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PermissionType(str, Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """资源类型"""
    USER = "user"
    WORKFLOW = "workflow"
    TOOL = "tool"
    ADMIN = "admin"
    SYSTEM = "system"


class Permission(BaseModel):
    """权限模型"""
    id: str = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称", min_length=1, max_length=100)
    code: str = Field(
        ...,
        description="权限代码（唯一标识）",
        pattern=r"^[a-z_]+:[a-z_]+$",
        example="workflow:execute"
    )
    resource_type: ResourceType = Field(..., description="资源类型")
    permission_type: PermissionType = Field(..., description="权限类型")
    description: str = Field(default="", description="权限描述", max_length=500)
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class PermissionCreate(BaseModel):
    """创建权限请求"""
    name: str = Field(..., description="权限名称", min_length=1, max_length=100)
    code: str = Field(
        ...,
        description="权限代码",
        pattern=r"^[a-z_]+:[a-z_]+$",
        example="workflow:execute"
    )
    resource_type: ResourceType = Field(..., description="资源类型")
    permission_type: PermissionType = Field(..., description="权限类型")
    description: str = Field(default="", description="权限描述", max_length=500)


class PermissionUpdate(BaseModel):
    """更新权限请求"""
    name: Optional[str] = Field(None, description="权限名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="权限描述", max_length=500)


class PermissionResponse(BaseModel):
    """权限响应"""
    id: str
    name: str
    code: str
    resource_type: str
    permission_type: str
    description: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PermissionListResponse(BaseModel):
    """权限列表响应"""
    permissions: List[PermissionResponse]
    total: int
    page: int
    page_size: int









