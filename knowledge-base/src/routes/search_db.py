"""
智能搜索API路由（数据库集成版本）
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List

from ..models.document_models import (
    SemanticSearchRequest, KeywordSearchRequest,
    SearchResponse, SearchResult, ChunkMetadata
)
from ..services.search_service import SearchService
from ..dependencies.database import get_db
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response
from sqlalchemy.orm import Session

router = APIRouter()
logger = setup_logger(__name__)


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """获取搜索服务"""
    return SearchService(db)


@router.post(
    "/search/semantic",
    response_model=SearchResponse,
    summary="语义搜索",
    description="基于向量相似度的语义搜索（数据库集成版本）",
    tags=["Search"]
)
async def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = None  # 可以从认证中间件获取
) -> SearchResponse:
    """
    语义搜索
    
    将查询文本转换为向量，在向量数据库中进行相似度搜索
    """
    try:
        service = get_search_service(db)
        
        result = await service.semantic_search(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score,
            filters=request.filters,
            document_ids=request.document_ids,
            user_id=user_id
        )
        
        # 转换为Pydantic模型
        search_results = []
        for r in result["results"]:
            chunk_metadata = ChunkMetadata(
                chunk_id=r["chunk_id"],
                chunk_index=r["chunk_metadata"].get("chunk_index", 0),
                start_char=r["chunk_metadata"].get("start_char", 0),
                end_char=r["chunk_metadata"].get("end_char", 0),
                page_number=r["chunk_metadata"].get("page_number"),
                metadata=r["chunk_metadata"]
            )
            
            search_results.append(SearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                document_name=r["document_name"],
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"],
                chunk_metadata=chunk_metadata
            ))
        
        return SearchResponse(
            query=result["query"],
            results=search_results,
            total=result["total"],
            search_type="semantic",
            execution_time=result.get("execution_time"),
            search_id=result.get("search_id")
        )
        
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in semantic search: {str(e)}")


@router.post(
    "/search/keyword",
    response_model=SearchResponse,
    summary="关键词搜索",
    description="基于关键词的文档搜索（数据库集成版本）",
    tags=["Search"]
)
async def keyword_search(
    request: KeywordSearchRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = None  # 可以从认证中间件获取
) -> SearchResponse:
    """
    关键词搜索
    
    在文档内容中搜索关键词
    """
    try:
        service = get_search_service(db)
        
        result = await service.keyword_search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            document_ids=request.document_ids,
            user_id=user_id
        )
        
        # 转换为Pydantic模型
        search_results = []
        for r in result["results"]:
            chunk_metadata = ChunkMetadata(
                chunk_id=r["chunk_id"],
                chunk_index=r["chunk_metadata"].get("chunk_index", 0),
                start_char=r["chunk_metadata"].get("start_char", 0),
                end_char=r["chunk_metadata"].get("end_char", 0),
                page_number=r["chunk_metadata"].get("page_number"),
                metadata=r["chunk_metadata"]
            )
            
            search_results.append(SearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                document_name=r["document_name"],
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"],
                chunk_metadata=chunk_metadata
            ))
        
        return SearchResponse(
            query=result["query"],
            results=search_results,
            total=result["total"],
            search_type="keyword",
            execution_time=result.get("execution_time"),
            search_id=result.get("search_id")
        )
        
    except Exception as e:
        logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in keyword search: {str(e)}")


@router.post(
    "/search/feedback",
    summary="提交搜索反馈",
    description="提交搜索结果的反馈，用于改进搜索质量",
    tags=["Search"]
)
async def submit_search_feedback(
    search_id: str = Query(..., description="搜索ID"),
    feedback_type: str = Query(..., description="反馈类型（positive/negative/neutral）"),
    document_id: Optional[str] = Query(None, description="相关文档ID"),
    relevance_score: Optional[int] = Query(None, ge=1, le=5, description="相关性评分（1-5）"),
    comment: Optional[str] = Query(None, description="反馈评论"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = None  # 可以从认证中间件获取
) -> Dict[str, Any]:
    """提交搜索反馈"""
    try:
        service = get_search_service(db)
        
        feedback = await service.submit_feedback(
            search_id=search_id,
            user_id=user_id,
            feedback_type=feedback_type,
            document_id=document_id,
            relevance_score=relevance_score,
            comment=comment
        )
        
        return {
            "message": "Feedback submitted successfully",
            "feedback": feedback
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@router.get(
    "/search/history",
    summary="获取搜索历史",
    description="获取用户的搜索历史记录",
    tags=["Search"]
)
async def get_search_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="用户ID")
) -> Dict[str, Any]:
    """获取搜索历史"""
    try:
        service = get_search_service(db)
        
        history = await service.get_search_history(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting search history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting search history: {str(e)}")


@router.get(
    "/search/popular",
    summary="获取热门搜索",
    description="获取热门搜索查询列表",
    tags=["Search"]
)
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取热门搜索查询"""
    try:
        service = get_search_service(db)
        
        popular = await service.get_popular_queries(limit=limit)
        
        return {
            "queries": popular,
            "total": len(popular)
        }
        
    except Exception as e:
        logger.error(f"Error getting popular queries: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting popular queries: {str(e)}")









