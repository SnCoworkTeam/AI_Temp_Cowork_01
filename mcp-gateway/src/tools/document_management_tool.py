"""
文档管理工具
提供文档上传、查询和管理功能
"""
from typing import Dict, Any, List, Optional
import logging
import os
from pathlib import Path

from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings
from ..models.tool_models import ToolDefinition, ToolType, ToolStatus

logger = logging.getLogger(__name__)

# 知识库服务URL
KNOWLEDGE_BASE_URL = getattr(settings, 'KNOWLEDGE_BASE_URL', 'http://knowledge-base:8004')


async def upload_document(file_path: str, metadata: Optional[Dict[str, Any]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    上传文档到知识库
    
    Args:
        file_path: 文件路径
        metadata: 文档元数据（可选）
        tags: 文档标签列表（可选）
    
    Returns:
        上传结果
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = Path(file_path).name
        
        # 读取文件
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 使用httpx发送multipart请求
        import httpx
        
        files = {
            'file': (filename, file_content)
        }
        
        data = {}
        if tags:
            data['tags'] = ','.join(tags)
        if metadata:
            import json
            data['metadata'] = json.dumps(metadata)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KNOWLEDGE_BASE_URL}/api/documents/upload",
                files=files,
                data=data,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        return {
            "success": True,
            "document_id": result.get("document_id"),
            "filename": filename,
            "status": result.get("status"),
            "message": result.get("message", "Document uploaded successfully")
        }
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


async def get_document_info(doc_id: str) -> Dict[str, Any]:
    """
    获取文档信息
    
    Args:
        doc_id: 文档ID
    
    Returns:
        文档信息
    """
    try:
        async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
            response = await client.get(f"/api/documents/{doc_id}")
        
        return {
            "success": True,
            "document": response
        }
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "document_id": doc_id
        }


async def list_documents(filters: Optional[Dict[str, Any]] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    列出文档
    
    Args:
        filters: 过滤条件（可选）
            - file_type: 文件类型
            - status: 文档状态
            - tags: 标签列表
            - search: 搜索关键词
        page: 页码
        page_size: 每页大小
    
    Returns:
        文档列表
    """
    try:
        params = {
            "page": page,
            "page_size": page_size
        }
        
        if filters:
            if "file_type" in filters:
                params["file_type"] = filters["file_type"]
            if "status" in filters:
                params["status"] = filters["status"]
            if "tags" in filters:
                params["tags"] = ','.join(filters["tags"]) if isinstance(filters["tags"], list) else filters["tags"]
            if "search" in filters:
                params["search"] = filters["search"]
        
        async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
            response = await client.get("/api/documents", params=params)
        
        return {
            "success": True,
            "documents": response.get("documents", []),
            "total": response.get("total", 0),
            "page": response.get("page", page),
            "page_size": response.get("page_size", page_size),
            "total_pages": response.get("total_pages", 0)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def execute_document_management(parameters: Dict[str, Any]) -> Any:
    """
    执行文档管理工具
    
    Args:
        parameters: 工具参数
            - action: 操作类型（upload/get/list/delete）
            - file_path: 文件路径（upload时必需）
            - document_id: 文档ID（get/delete时必需）
            - metadata: 文档元数据（upload时可选）
            - tags: 文档标签（upload时可选）
            - filters: 过滤条件（list时可选）
            - page: 页码（list时可选）
            - page_size: 每页大小（list时可选）
    
    Returns:
        操作结果
    """
    action = parameters.get("action", "list")
    
    if action == "upload":
        file_path = parameters.get("file_path")
        if not file_path:
            raise ValueError("file_path is required for upload action")
        
        metadata = parameters.get("metadata")
        tags = parameters.get("tags")
        
        return await upload_document(file_path, metadata=metadata, tags=tags)
    
    elif action == "get":
        doc_id = parameters.get("document_id")
        if not doc_id:
            raise ValueError("document_id is required for get action")
        
        return await get_document_info(doc_id)
    
    elif action == "list":
        filters = parameters.get("filters")
        page = parameters.get("page", 1)
        page_size = parameters.get("page_size", 20)
        
        return await list_documents(filters=filters, page=page, page_size=page_size)
    
    elif action == "delete":
        doc_id = parameters.get("document_id")
        if not doc_id:
            raise ValueError("document_id is required for delete action")
        
        try:
            async with HTTPClient(base_url=KNOWLEDGE_BASE_URL) as client:
                response = await client.delete(f"/api/documents/{doc_id}")
            return {
                "success": True,
                "message": response.get("message", "Document deleted successfully"),
                "document_id": doc_id
            }
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "document_id": doc_id
            }
    
    else:
        raise ValueError(f"Unsupported action: {action}. Supported actions: upload, get, list, delete")


# 工具定义
DOCUMENT_MANAGEMENT_TOOL = ToolDefinition(
    name="document_management",
    description="管理企业知识库中的文档，包括上传、查询、列表和删除操作。",
    version="1.0.0",
    tool_type=ToolType.FUNCTION,
    status=ToolStatus.ACTIVE,
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "操作类型",
                "enum": ["upload", "get", "list", "delete"],
                "required": True
            },
            "file_path": {
                "type": "string",
                "description": "文件路径（upload时必需）",
                "required": False
            },
            "document_id": {
                "type": "string",
                "description": "文档ID（get/delete时必需）",
                "required": False
            },
            "metadata": {
                "type": "object",
                "description": "文档元数据（upload时可选）",
                "required": False
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "文档标签列表（upload时可选）",
                "required": False
            },
            "filters": {
                "type": "object",
                "description": "过滤条件（list时可选）",
                "properties": {
                    "file_type": {"type": "string"},
                    "status": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "search": {"type": "string"}
                },
                "required": False
            },
            "page": {
                "type": "integer",
                "description": "页码（list时可选）",
                "minimum": 1,
                "default": 1
            },
            "page_size": {
                "type": "integer",
                "description": "每页大小（list时可选）",
                "minimum": 1,
                "maximum": 100,
                "default": 20
            }
        },
        "required": ["action"]
    },
    required_parameters=["action"],
    returns={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "document_id": {"type": "string"},
            "documents": {"type": "array"},
            "total": {"type": "integer"},
            "message": {"type": "string"},
            "error": {"type": "string"}
        }
    },
    metadata={
        "category": "knowledge_base",
        "author": "system",
        "service": "knowledge-base"
    }
)

