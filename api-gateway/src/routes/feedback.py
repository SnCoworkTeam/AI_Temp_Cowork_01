"""
反馈API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# 尝试从database模块导入，如果失败则使用metadata-service的数据库
try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../database/src'))
    from core.database import get_db
except ImportError:
    # 如果导入失败，使用metadata-service的数据库连接
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('DB_USER', 'ai_user')}:{os.getenv('DB_PASSWORD', 'ai_password')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'ai_platform')}"
    )
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
from ..services.feedback_service import FeedbackService
import logging

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])
logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    query_id: str = Field(..., description="查询ID")
    feedback_type: str = Field(..., description="反馈类型：positive/negative")
    query: str = Field(..., description="查询内容")
    result_id: Optional[str] = Field(None, description="结果ID（可选）")
    comment: Optional[str] = Field(None, description="反馈评论（可选）")
    user_id: Optional[str] = Field(None, description="用户ID（可选）")


class QueryLogRequest(BaseModel):
    query_id: str = Field(..., description="查询ID")
    query: str = Field(..., description="查询内容")
    success: bool = Field(..., description="是否成功")
    response_time_ms: Optional[int] = Field(None, description="响应时间（毫秒）")
    result_count: Optional[int] = Field(None, description="结果数量")
    user_id: Optional[str] = Field(None, description="用户ID（可选）")


@router.post("/submit", summary="提交用户反馈")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    提交用户反馈（👍/👎）
    
    Args:
        request: 反馈请求
    
    Returns:
        反馈提交结果
    """
    try:
        if request.feedback_type not in ["positive", "negative"]:
            raise HTTPException(status_code=400, detail="feedback_type must be 'positive' or 'negative'")
        
        service = FeedbackService(db)
        result = await service.submit_feedback(
            query_id=request.query_id,
            feedback_type=request.feedback_type,
            query=request.query,
            result_id=request.result_id,
            comment=request.comment,
            user_id=request.user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-query", summary="记录查询日志")
async def log_query(
    request: QueryLogRequest,
    db: Session = Depends(get_db)
):
    """
    记录查询日志（用于质量监控）
    
    Args:
        request: 查询日志请求
    
    Returns:
        日志记录结果
    """
    try:
        service = FeedbackService(db)
        await service.log_query(
            query_id=request.query_id,
            query=request.query,
            success=request.success,
            response_time_ms=request.response_time_ms,
            result_count=request.result_count,
            user_id=request.user_id
        )
        return {"success": True, "message": "Query logged successfully"}
    except Exception as e:
        logger.error(f"Failed to log query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="获取反馈统计")
async def get_feedback_stats(
    time_range: str = Query("7d", description="时间范围：7d, 30d, 90d, all"),
    db: Session = Depends(get_db)
):
    """
    获取反馈统计信息
    
    Args:
        time_range: 时间范围
    
    Returns:
        反馈统计信息
    """
    try:
        service = FeedbackService(db)
        stats = await service.get_feedback_stats(time_range)
        return stats
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-stats", summary="获取质量统计")
async def get_quality_stats(
    time_range: str = Query("7d", description="时间范围：7d, 30d, 90d, all"),
    db: Session = Depends(get_db)
):
    """
    获取质量统计（问答成功率、用户满意度）
    
    Args:
        time_range: 时间范围
    
    Returns:
        质量统计信息
    """
    try:
        service = FeedbackService(db)
        stats = await service.get_quality_stats(time_range)
        return stats
    except Exception as e:
        logger.error(f"Failed to get quality stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

