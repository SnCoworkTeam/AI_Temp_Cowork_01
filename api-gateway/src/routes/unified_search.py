"""
统一搜索API路由
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..services.unified_search_service import UnifiedSearchService
import logging

router = APIRouter(prefix="/api/unified", tags=["Unified Search"])
logger = logging.getLogger(__name__)


class UnifiedSearchRequest(BaseModel):
    """统一搜索请求"""
    query: str
    types: List[str] = ["document", "metadata"]
    limit: int = 20
    filters: Optional[Dict[str, Any]] = None


@router.post("/search", summary="统一搜索（带缓存优化）")
async def unified_search(
    request: UnifiedSearchRequest,
    use_cache: bool = True
):
    """
    统一搜索接口（带缓存优化）
    
    整合knowledge-base和metadata-service的搜索结果
    
    **性能优化**:
    - 多级缓存（内存+Redis）
    - 并行服务调用
    - 智能超时控制
    
    **一致性模型**: 最终一致性（Eventual Consistency）
    - 实体映射关系可能延迟更新（通常<5分钟）
    - 新创建的实体需要等待自动映射任务执行
    - 搜索结果可能不包含最新的映射关系
    
    **服务降级**: 即使部分服务失败，也会返回可用结果
    """
    try:
        service = UnifiedSearchService()
        result = await service.unified_search(
            query=request.query,
            types=request.types,
            limit=request.limit,
            filters=request.filters,
            use_cache=use_cache
        )
        await service.close()
        return result
    except Exception as e:
        logger.error(f"Unified search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", summary="获取缓存统计信息")
async def get_cache_stats():
    """获取统一搜索缓存统计信息"""
    try:
        service = UnifiedSearchService()
        stats = service.get_cache_stats()
        await service.close()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache", summary="清空缓存")
async def clear_cache():
    """清空统一搜索缓存"""
    try:
        service = UnifiedSearchService()
        if service.cache_enabled and service.cache:
            service.cache.delete()
            await service.close()
            return {"success": True, "message": "Cache cleared"}
        else:
            await service.close()
            return {"success": False, "message": "Cache not enabled"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="统一搜索（GET方式，带缓存优化）")
async def unified_search_get(
    query: str = Query(..., description="搜索查询"),
    types: str = Query("document,metadata", description="搜索类型，逗号分隔"),
    limit: int = Query(20, ge=1, le=100, description="返回结果数量"),
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    统一搜索接口（GET方式）
    
    **一致性模型**: 最终一致性（Eventual Consistency）
    - 实体映射关系可能延迟更新（通常<5分钟）
    - 新创建的实体需要等待自动映射任务执行
    - 搜索结果可能不包含最新的映射关系
    
    **服务降级**: 即使部分服务失败，也会返回可用结果
    """
    try:
        type_list = [t.strip() for t in types.split(",")]
        service = UnifiedSearchService()
        result = await service.unified_search(
            query=query,
            types=type_list,
            limit=limit,
            use_cache=use_cache
        )
        await service.close()
        return result
    except Exception as e:
        logger.error(f"Unified search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", summary="获取缓存统计信息")
async def get_cache_stats():
    """获取统一搜索缓存统计信息"""
    try:
        service = UnifiedSearchService()
        stats = service.get_cache_stats()
        await service.close()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache", summary="清空缓存")
async def clear_cache():
    """清空统一搜索缓存"""
    try:
        service = UnifiedSearchService()
        if service.cache_enabled and service.cache:
            service.cache.delete()
            await service.close()
            return {"success": True, "message": "Cache cleared"}
        else:
            await service.close()
            return {"success": False, "message": "Cache not enabled"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


