"""
分析统计API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import httpx
import logging
from ..config import settings

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


def get_knowledge_base_url() -> str:
    """获取knowledge-base服务的URL"""
    use_localhost = settings.LOCAL_DEV or settings.USE_LOCALHOST
    if use_localhost:
        return "http://localhost:8004"
    else:
        return "http://knowledge-base:8004"


def get_metadata_service_url() -> str:
    """获取metadata-service的URL"""
    use_localhost = settings.LOCAL_DEV or settings.USE_LOCALHOST
    if use_localhost:
        return "http://localhost:8005"
    else:
        return "http://metadata-service:8005"


@router.get("/stats", summary="获取统计数据")
async def get_stats() -> Dict[str, Any]:
    """
    获取平台统计数据
    包括文档数、知识库数、用户数、搜索次数等
    """
    try:
        kb_url = get_knowledge_base_url()
        metadata_url = get_metadata_service_url()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取知识库统计
            kb_response = await client.get(f"{kb_url}/api/knowledge-bases")
            kb_data = kb_response.json() if kb_response.status_code == 200 else {"knowledge_bases": []}
            kb_list = kb_data.get("knowledge_bases", []) if isinstance(kb_data, dict) else []
            
            # 获取文档统计
            docs_response = await client.get(f"{kb_url}/api/documents?page=1&page_size=1")
            docs_data = docs_response.json() if docs_response.status_code == 200 else {"total": 0}
            total_docs = docs_data.get("total", 0) if isinstance(docs_data, dict) else 0
            
            # 获取数据资产统计（从metadata-service）
            assets_response = await client.get(f"{metadata_url}/api/data-assets?limit=1")
            assets_data = assets_response.json() if assets_response.status_code == 200 else []
            total_assets = len(assets_data) if isinstance(assets_data, list) else 0
            
            return {
                "totalDocuments": total_docs,
                "totalKnowledgeBases": len(kb_list),
                "totalUsers": 0,  # 需要从auth-service获取
                "totalSearches": 0,  # 需要从搜索服务获取
                "totalAssets": total_assets
            }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        return {
            "totalDocuments": 0,
            "totalKnowledgeBases": 0,
            "totalUsers": 0,
            "totalSearches": 0,
            "totalAssets": 0
        }


@router.get("/trends", summary="获取趋势数据")
async def get_trends() -> Dict[str, Any]:
    """
    获取趋势数据
    包括文档增长趋势、知识库分布等
    """
    try:
        kb_url = get_knowledge_base_url()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 获取知识库列表
            kb_response = await client.get(f"{kb_url}/api/knowledge-bases")
            kb_data = kb_response.json() if kb_response.status_code == 200 else {"knowledge_bases": []}
            kb_list = kb_data.get("knowledge_bases", []) if isinstance(kb_data, dict) else []
            
            # 构建知识库分布数据
            kb_distribution = []
            for kb in kb_list[:10]:  # 限制前10个
                kb_distribution.append({
                    "name": kb.get("name", "未知"),
                    "value": kb.get("document_count", 0)
                })
            
            return {
                "documentGrowth": [],  # 需要从数据库查询历史数据
                "kbDistribution": kb_distribution,
                "searchTrends": []  # 需要从搜索服务获取
            }
    except Exception as e:
        logger.error(f"Failed to get trends: {e}", exc_info=True)
        return {
            "documentGrowth": [],
            "kbDistribution": [],
            "searchTrends": []
        }


@router.get("/user-behavior", summary="获取用户行为分析")
async def get_user_behavior() -> list:
    """
    获取用户行为分析数据
    """
    try:
        # TODO: 实现用户行为分析
        return []
    except Exception as e:
        logger.error(f"Failed to get user behavior: {e}", exc_info=True)
        return []



