"""
Knowledge Base 测试数据
"""
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any


def create_document_data(
    title: str = "Test Document",
    content: str = "Test content"
) -> Dict[str, Any]:
    """创建文档测试数据"""
    return {
        "id": str(uuid4()),
        "title": title,
        "content": content,
        "document_type": "text",
        "metadata": {},
        "created_at": datetime.utcnow().isoformat()
    }


def create_search_query(
    query: str = "test query",
    limit: int = 10
) -> Dict[str, Any]:
    """创建搜索查询测试数据"""
    return {
        "query": query,
        "limit": limit,
        "filters": {}
    }









