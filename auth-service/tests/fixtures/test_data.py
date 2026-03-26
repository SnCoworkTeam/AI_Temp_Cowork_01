"""
Auth Service 测试数据
"""
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any


def create_user_data(
    username: str = "testuser",
    email: str = "test@example.com"
) -> Dict[str, Any]:
    """创建用户测试数据"""
    return {
        "id": str(uuid4()),
        "username": username,
        "email": email,
        "hashed_password": "hashed_password",
        "created_at": datetime.utcnow().isoformat()
    }


def create_role_data(
    name: str = "test_role",
    description: str = "Test role"
) -> Dict[str, Any]:
    """创建角色测试数据"""
    return {
        "id": str(uuid4()),
        "name": name,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }









