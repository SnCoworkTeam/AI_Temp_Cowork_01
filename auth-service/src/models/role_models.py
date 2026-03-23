"""
角色数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Role(BaseModel):
    """角色模型"""
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称", min_length=1, max_length=100)
    code: str = Field(
        ...,
        description="角色代码（唯一标识）",
        pattern=r"^[a-z_]+$",
        example="admin"
    )
    description: str = Field(default="", description="角色描述", max_length=500)
    permissions: List[str] = Field(default_factory=list, description="权限ID列表")
    is_system: bool = Field(default=False, description="是否系统角色（不可删除）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class RoleCreate(BaseModel):
    """创建角色请求"""
    name: str = Field(..., description="角色名称", min_length=1, max_length=100)
    code: str = Field(
        ...,
        description="角色代码",
        pattern=r"^[a-z_]+$",
        example="admin"
    )
    description: str = Field(default="", description="角色描述", max_length=500)
    permissions: List[str] = Field(default_factory=list, description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(None, description="角色名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="角色描述", max_length=500)
    permissions: Optional[List[str]] = Field(None, description="权限ID列表")


class RoleResponse(BaseModel):
    """角色响应"""
    id: str
    name: str
    code: str
    description: str
    permissions: List[str]
    is_system: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RoleListResponse(BaseModel):
    """角色列表响应"""
    roles: List[RoleResponse]
    total: int
    page: int
    page_size: int









