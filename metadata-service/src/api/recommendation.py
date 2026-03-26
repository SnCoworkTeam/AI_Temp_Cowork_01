"""
智能推荐API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.entity_recommendation_service import EntityRecommendationService
from ..services.decision_support_service import DecisionSupportService
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/recommendation", tags=["Recommendation"])
logger = setup_logger(__name__)


@router.get("/entities/{entity_id}/related", summary="推荐相关实体")
async def recommend_related_entities(
    entity_id: int,
    max_depth: int = Query(2, ge=1, le=5, description="最大遍历深度"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    relationship_types: Optional[str] = Query(None, description="关系类型过滤，逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    基于知识图谱推荐相关实体
    
    Args:
        entity_id: 源实体ID
        max_depth: 最大遍历深度
        limit: 返回数量限制
        relationship_types: 关系类型过滤
    
    Returns:
        推荐实体列表
    """
    try:
        service = EntityRecommendationService(db)
        
        rel_types = None
        if relationship_types:
            rel_types = [t.strip() for t in relationship_types.split(",")]
        
        recommendations = await service.recommend_related_entities(
            entity_id=entity_id,
            max_depth=max_depth,
            limit=limit,
            relationship_types=rel_types
        )
        
        return {
            "success": True,
            "entity_id": entity_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to recommend entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/similar", summary="推荐相似实体")
async def recommend_similar_entities(
    entity_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    基于相似度推荐实体
    
    Args:
        entity_id: 源实体ID
        limit: 返回数量限制
    
    Returns:
        推荐实体列表
    """
    try:
        service = EntityRecommendationService(db)
        recommendations = await service.recommend_by_similarity(
            entity_id=entity_id,
            limit=limit
        )
        
        return {
            "success": True,
            "entity_id": entity_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to recommend similar entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decision/analyze-impact", summary="分析实体影响范围")
async def analyze_entity_impact(
    entity_id: int = Body(..., description="实体ID"),
    analysis_type: str = Body("full", description="分析类型：full, direct, indirect"),
    db: Session = Depends(get_db)
):
    """
    分析实体影响范围
    
    Args:
        entity_id: 实体ID
        analysis_type: 分析类型
    
    Returns:
        影响分析结果
    """
    try:
        service = DecisionSupportService(db)
        result = await service.analyze_entity_impact(
            entity_id=entity_id,
            analysis_type=analysis_type
        )
        
        return {
            "success": True,
            "analysis": result
        }
    except Exception as e:
        logger.error(f"Failed to analyze entity impact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decision/find-path", summary="查找实体间最优路径")
async def find_optimal_path(
    source_entity_id: int = Body(..., description="源实体ID"),
    target_entity_id: int = Body(..., description="目标实体ID"),
    max_depth: int = Body(5, ge=1, le=10, description="最大深度"),
    db: Session = Depends(get_db)
):
    """
    查找两个实体之间的最优路径
    
    Args:
        source_entity_id: 源实体ID
        target_entity_id: 目标实体ID
        max_depth: 最大深度
    
    Returns:
        路径分析结果
    """
    try:
        service = DecisionSupportService(db)
        result = await service.find_optimal_path(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            max_depth=max_depth
        )
        
        return {
            "success": True,
            "path_analysis": result
        }
    except Exception as e:
        logger.error(f"Failed to find optimal path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision/insights/{entity_id}", summary="获取实体洞察")
async def get_entity_insights(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """
    获取实体洞察信息
    
    Args:
        entity_id: 实体ID
    
    Returns:
        洞察信息
    """
    try:
        service = DecisionSupportService(db)
        insights = await service.get_entity_insights(entity_id)
        
        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Failed to get entity insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", summary="获取缓存统计信息")
async def get_cache_stats(
    db: Session = Depends(get_db)
):
    """获取推荐缓存统计信息"""
    try:
        service = EntityRecommendationService(db)
        if service.cache:
            stats = service.cache.get_stats()
            return {
                "success": True,
                "stats": stats
            }
        else:
            return {
                "success": True,
                "stats": {"enabled": False}
            }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache", summary="清空推荐缓存")
async def clear_cache(
    entity_id: Optional[int] = Query(None, description="实体ID，如果提供则只清除该实体的缓存"),
    db: Session = Depends(get_db)
):
    """清空推荐缓存"""
    try:
        service = EntityRecommendationService(db)
        if service.cache:
            if entity_id:
                count = service.cache.invalidate_all_for_entity(entity_id)
                return {
                    "success": True,
                    "message": f"Cleared {count} cache entries for entity {entity_id}"
                }
            else:
                return {
                    "success": True,
                    "message": "Use entity_id parameter to clear specific cache"
                }
        else:
            return {
                "success": True,
                "message": "Cache not enabled"
            }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

