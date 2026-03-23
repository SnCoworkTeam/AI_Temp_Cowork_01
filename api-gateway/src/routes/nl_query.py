"""
自然语言查询API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from ..services.nl_query_service import NLQueryService
from ..services.unified_search_service import UnifiedSearchService
import logging

router = APIRouter(prefix="/api/nl-query", tags=["Natural Language Query"])
logger = logging.getLogger(__name__)


class NLQueryRequest(BaseModel):
    """自然语言查询请求"""
    query: str = Field(..., description="自然语言查询")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


@router.post("/query", summary="执行自然语言查询")
async def execute_nl_query(
    request: NLQueryRequest,
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    执行自然语言查询
    
    支持：
    - 搜索查询（"查找物料相关的实体"）
    - 图查询（"显示与客户相关的所有实体"）
    - 问答查询（"什么是业务实体？"）
    """
    try:
        nl_service = NLQueryService()
        
        # 解析查询
        parsed_query = await nl_service.parse_query(
            query=request.query,
            context=request.context
        )
        
        # 根据查询类型执行
        result = None
        if parsed_query.get("query_type") == "graph_query":
            # 执行图查询
            result = await nl_service.execute_graph_query(parsed_query)
        else:
            # 执行统一搜索
            search_service = UnifiedSearchService(use_cache=use_cache)
            search_result = await search_service.search(
                query=request.query,
                types=["entity", "document", "metadata"],
                limit=20
            )
            result = search_result
        
        # 生成自然语言解释
        explanation = await nl_service.explain_result(request.query, result)
        
        await nl_service.close()
        if hasattr(search_service, 'close'):
            await search_service.close()
        
        return {
            "success": True,
            "query": request.query,
            "parsed_query": parsed_query,
            "result": result,
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Failed to execute NL query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse", summary="解析自然语言查询")
async def parse_query(
    request: NLQueryRequest
):
    """
    仅解析自然语言查询，不执行
    
    返回解析后的查询结构
    """
    try:
        nl_service = NLQueryService()
        parsed_query = await nl_service.parse_query(
            query=request.query,
            context=request.context
        )
        await nl_service.close()
        
        return {
            "success": True,
            "query": request.query,
            "parsed_query": parsed_query
        }
    except Exception as e:
        logger.error(f"Failed to parse query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

