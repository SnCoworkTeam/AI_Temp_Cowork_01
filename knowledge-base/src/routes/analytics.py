"""
知识库分析和统计API路由
提供搜索质量评估、用户行为分析等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..repositories.search_history_repository import (
    SearchHistoryRepository,
    UserBehaviorRepository,
    SearchFeedbackRepository
)
from ..repositories.document_repository import DocumentRepository
from ..dependencies.database import get_db
from luminaos_common.common.logger import setup_logger
from sqlalchemy.orm import Session

router = APIRouter(prefix="/analytics", tags=["知识库分析"])
logger = setup_logger(__name__)


@router.get(
    "/search/quality",
    summary="搜索质量评估",
    description="分析搜索质量指标",
    responses={
        200: {"description": "搜索质量评估数据"}
    }
)
async def get_search_quality(
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取搜索质量评估数据"""
    try:
        feedback_repo = SearchFeedbackRepository(db)
        
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                pass
        
        stats = feedback_repo.get_feedback_stats(
            document_id=None,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # 计算搜索质量指标
        total_feedback = stats.get("total_feedback", 0)
        positive_count = stats.get("feedback_counts", {}).get("positive", 0)
        avg_score = stats.get("average_relevance_score", 0.0)
        
        quality_score = 0.0
        if total_feedback > 0:
            positive_rate = positive_count / total_feedback
            quality_score = (positive_rate * 0.6 + (avg_score / 5.0) * 0.4) * 100
        
        return {
            "quality_score": quality_score,
            "total_feedback": total_feedback,
            "positive_rate": positive_count / total_feedback if total_feedback > 0 else 0.0,
            "average_relevance_score": avg_score,
            "feedback_breakdown": stats.get("feedback_counts", {}),
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting search quality: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting search quality: {str(e)}"
        )


@router.get(
    "/documents/{document_id}/stats",
    summary="文档统计信息",
    description="获取文档的查看统计和用户行为分析",
    responses={
        200: {"description": "文档统计数据"}
    }
)
async def get_document_stats(
    document_id: str = Path(..., description="文档ID"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取文档统计信息"""
    try:
        behavior_repo = UserBehaviorRepository(db)
        
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                pass
        
        view_stats = behavior_repo.get_document_view_stats(
            document_id=document_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "document_id": document_id,
            "view_statistics": view_stats,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document stats: {str(e)}"
        )


@router.get(
    "/user-behavior",
    summary="用户行为分析",
    description="分析用户行为模式",
    responses={
        200: {"description": "用户行为分析数据"}
    }
)
async def get_user_behavior_analysis(
    user_id: Optional[str] = Query(None, description="用户ID"),
    action_type: Optional[str] = Query(None, description="行为类型"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取用户行为分析"""
    try:
        behavior_repo = UserBehaviorRepository(db)
        
        behaviors = behavior_repo.get_user_behaviors(
            user_id=user_id,
            action_type=action_type,
            skip=0,
            limit=1000
        )
        
        # 过滤日期范围
        if start_date or end_date:
            start_dt = None
            end_dt = None
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except:
                    pass
            
            filtered_behaviors = []
            for behavior in behaviors:
                created_at_str = behavior.get("created_at")
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if start_dt and created_at < start_dt:
                            continue
                        if end_dt and created_at > end_dt:
                            continue
                        filtered_behaviors.append(behavior)
                    except:
                        pass
            behaviors = filtered_behaviors
        
        # 统计行为类型
        action_counts = {}
        target_type_counts = {}
        
        for behavior in behaviors:
            action_type_value = behavior.get("action_type", "unknown")
            target_type_value = behavior.get("target_type", "unknown")
            
            action_counts[action_type_value] = action_counts.get(action_type_value, 0) + 1
            target_type_counts[target_type_value] = target_type_counts.get(target_type_value, 0) + 1
        
        return {
            "total_behaviors": len(behaviors),
            "action_breakdown": action_counts,
            "target_type_breakdown": target_type_counts,
            "recent_behaviors": behaviors[:20],  # 最近20条
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user behavior analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting user behavior analysis: {str(e)}"
        )


@router.get(
    "/documents/popular",
    summary="热门文档",
    description="获取热门文档列表（基于查看次数）",
    responses={
        200: {"description": "热门文档列表"}
    }
)
async def get_popular_documents(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取热门文档"""
    try:
        behavior_repo = UserBehaviorRepository(db)
        document_repo = DocumentRepository(db)
        
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                pass
        
        # 获取所有文档
        documents = document_repo.list_documents(skip=0, limit=10000)
        
        # 统计每个文档的查看次数
        document_views = {}
        for doc in documents:
            doc_id = str(doc.id)
            stats = behavior_repo.get_document_view_stats(
                document_id=doc_id,
                start_date=start_dt,
                end_date=end_dt
            )
            document_views[doc_id] = stats.get("total_views", 0)
        
        # 排序并返回前N个
        popular_docs = sorted(
            document_views.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        # 获取文档详情
        popular_documents = []
        for doc_id, views in popular_docs:
            doc = document_repo.get_by_id(doc_id)
            if doc:
                popular_documents.append({
                    "document_id": doc_id,
                    "filename": doc.filename,
                    "views": views,
                    "category": doc.category,
                    "tags": doc.tags or []
                })
        
        return {
            "documents": popular_documents,
            "total": len(popular_documents),
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting popular documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting popular documents: {str(e)}"
        )









