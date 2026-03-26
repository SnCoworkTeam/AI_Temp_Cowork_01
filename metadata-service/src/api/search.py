"""
元数据搜索API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from ..services.search_service import SearchService
from ..models.data_asset import SearchResults
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """获取搜索服务"""
    return SearchService(db)


@router.get(
    "/search",
    summary="全局搜索",
    tags=["Search"]
)
async def search_all(
    q: str = Query(..., description="搜索关键词"),
    entity_types: Optional[str] = Query(None, description="实体类型，逗号分隔"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service)
):
    """全局搜索所有类型的元数据"""
    try:
        entity_type_list = entity_types.split(",") if entity_types else None
        tag_list = tags.split(",") if tags else None
        
        return service.search_all(
            query=q,
            entity_types=entity_type_list,
            tags=tag_list,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search/tags",
    summary="按标签搜索",
    tags=["Search"]
)
async def search_by_tags(
    tags: str = Query(..., description="标签，逗号分隔"),
    entity_types: Optional[str] = Query(None, description="实体类型，逗号分隔"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service)
):
    """按标签搜索元数据"""
    try:
        tag_list = tags.split(",")
        entity_type_list = entity_types.split(",") if entity_types else None
        
        return service.search_by_tags(
            tags=tag_list,
            entity_types=entity_type_list,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Tag search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search/popular-tags",
    summary="获取热门标签",
    tags=["Search"]
)
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service)
):
    """获取热门标签列表"""
    try:
        return service.get_popular_tags(limit=limit)
    except Exception as e:
        logger.error(f"Failed to get popular tags: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/metadata/search",
    response_model=SearchResults,
    summary="搜索元数据（元数据API）",
    tags=["Metadata"]
)
async def search_metadata(
    query: str = Query(..., description="搜索关键词"),
    asset_type: Optional[str] = Query(None, description="资产类型过滤"),
    entity_types: Optional[str] = Query(None, description="实体类型，逗号分隔"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service)
):
    """搜索元数据（返回结构化搜索结果）"""
    try:
        entity_type_list = entity_types.split(",") if entity_types else None
        if asset_type:
            # 如果指定了asset_type，添加到entity_types中
            if entity_type_list:
                entity_type_list.append("data_asset")
            else:
                entity_type_list = ["data_asset"]
        
        tag_list = tags.split(",") if tags else None
        
        # 执行搜索
        results = service.search_all(
            query=query,
            entity_types=entity_type_list,
            tags=tag_list,
            skip=skip,
            limit=limit
        )
        
        # 如果asset_type指定，进一步过滤
        if asset_type and results:
            filtered_results = [
                r for r in results
                if r.get("entity_type") == "data_asset" and 
                   r.get("metadata", {}).get("asset_type") == asset_type
            ]
            results = filtered_results
        
        # 构建分面信息
        facets = {}
        if results:
            # 按类型分组
            type_counts = {}
            for r in results:
                entity_type = r.get("entity_type", "unknown")
                type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
            facets["by_type"] = type_counts
        
        return SearchResults(
            query=query,
            total=len(results),
            results=results,
            facets=facets if facets else None
        )
    except Exception as e:
        logger.error(f"Metadata search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

