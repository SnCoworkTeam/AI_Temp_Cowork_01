"""
知识库搜索工具
提供语义搜索和关键词搜索功能
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings
from ..models.tool_models import ToolDefinition, ToolType, ToolStatus

logger = logging.getLogger(__name__)

# 知识库服务URL（从环境变量或配置获取）
KNOWLEDGE_BASE_URL = getattr(settings, 'KNOWLEDGE_BASE_URL', 'http://knowledge-base:8004')


async def semantic_search(query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    语义搜索
    
    Args:
        query: 搜索查询文本
        limit: 返回结果数量限制
        filters: 过滤条件（可选）
    
    Returns:
        搜索结果
    """
    try:
        request_data = {
            "query": query,
            "top_k": limit,
            "min_score": 0.3,
        }
        
        if filters:
            request_data["filters"] = filters
        
        async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
            response = await client.post("/api/search/semantic", data=request_data)
        
        return {
            "success": True,
            "query": query,
            "results": response.get("results", []),
            "total": response.get("total", 0),
            "search_type": "semantic"
        }
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


async def keyword_search(query: str, filters: Optional[Dict[str, Any]] = None, match_all: bool = False) -> Dict[str, Any]:
    """
    关键词搜索
    
    Args:
        query: 搜索关键词（逗号分隔）
        filters: 过滤条件（可选）
        match_all: 是否匹配所有关键词
    
    Returns:
        搜索结果
    """
    try:
        # 解析关键词
        keywords = [kw.strip() for kw in query.split(',') if kw.strip()]
        
        request_data = {
            "keywords": keywords,
            "match_all": match_all,
            "page": 1,
            "page_size": 10
        }
        
        if filters:
            request_data["filters"] = filters
        
        async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
            response = await client.post("/api/search/keyword", data=request_data)
        
        return {
            "success": True,
            "keywords": keywords,
            "results": response.get("results", []),
            "total": response.get("total", 0),
            "search_type": "keyword"
        }
    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


async def execute_knowledge_search(parameters: Dict[str, Any]) -> Any:
    """
    执行知识库搜索工具
    
    Args:
        parameters: 工具参数
            - query: 搜索查询（必需）
            - search_type: 搜索类型（semantic/keyword，默认semantic）
            - limit: 结果数量限制（默认5）
            - filters: 过滤条件（可选）
            - match_all: 关键词搜索时是否匹配所有（默认False）
    
    Returns:
        搜索结果
    """
    query = parameters.get("query", "")
    if not query:
        raise ValueError("Query parameter is required")
    
    search_type = parameters.get("search_type", "semantic")
    limit = parameters.get("limit", 5)
    filters = parameters.get("filters")
    match_all = parameters.get("match_all", False)
    
    if search_type == "semantic":
        return await semantic_search(query, limit=limit, filters=filters)
    elif search_type == "keyword":
        return await keyword_search(query, filters=filters, match_all=match_all)
    else:
        raise ValueError(f"Unsupported search type: {search_type}")


# 工具定义
KNOWLEDGE_SEARCH_TOOL = ToolDefinition(
    name="knowledge_search",
    description="从企业知识库中搜索相关信息，用于回答问题和支持决策。支持语义搜索和关键词搜索两种模式。",
    version="1.0.0",
    tool_type=ToolType.FUNCTION,
    status=ToolStatus.ACTIVE,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询文本",
                "required": True
            },
            "search_type": {
                "type": "string",
                "description": "搜索类型：semantic（语义搜索）或keyword（关键词搜索）",
                "enum": ["semantic", "keyword"],
                "default": "semantic"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量限制",
                "minimum": 1,
                "maximum": 20,
                "default": 5
            },
            "filters": {
                "type": "object",
                "description": "过滤条件（如文档ID、标签等）",
                "required": False
            },
            "match_all": {
                "type": "boolean",
                "description": "关键词搜索时是否匹配所有关键词（仅对keyword类型有效）",
                "default": False
            }
        },
        "required": ["query"]
    },
    required_parameters=["query"],
    returns={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "query": {"type": "string"},
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "chunk_id": {"type": "string"},
                        "document_id": {"type": "string"},
                        "document_name": {"type": "string"},
                        "content": {"type": "string"},
                        "score": {"type": "number"}
                    }
                }
            },
            "total": {"type": "integer"},
            "search_type": {"type": "string"}
        }
    },
    metadata={
        "category": "knowledge_base",
        "author": "system",
        "service": "knowledge-base"
    }
)

