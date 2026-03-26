"""
价值指标API路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..services.value_metrics_service import ValueMetricsService

logger = logging.getLogger(__name__)

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

router = APIRouter(prefix="/api/value-metrics", tags=["Value Metrics"])


class RecordTimeRequest(BaseModel):
    operation: str = Field(..., description="操作类型")
    time_saved: float = Field(..., description="节省时间（秒）")
    user_id: Optional[str] = Field(None, description="用户ID（可选）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据（可选）")


class RecordErrorRequest(BaseModel):
    operation: str = Field(..., description="操作类型")
    error_reduced: int = Field(..., description="减少错误数")
    user_id: Optional[str] = Field(None, description="用户ID（可选）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据（可选）")


@router.post("/record-time", summary="记录操作时间节省")
async def record_operation_time(
    request: RecordTimeRequest,
    db: Session = Depends(get_db)
):
    """
    记录操作时间节省
    
    Args:
        request: 时间记录请求
    
    Returns:
        记录结果
    """
    try:
        service = ValueMetricsService(db)
        result = await service.record_operation_time(
            operation=request.operation,
            time_saved=request.time_saved,
            user_id=request.user_id,
            metadata=request.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Failed to record operation time: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-error", summary="记录错误减少")
async def record_error_reduction(
    request: RecordErrorRequest,
    db: Session = Depends(get_db)
):
    """
    记录错误减少
    
    Args:
        request: 错误记录请求
    
    Returns:
        记录结果
    """
    try:
        service = ValueMetricsService(db)
        result = await service.record_error_reduction(
            operation=request.operation,
            error_reduced=request.error_reduced,
            user_id=request.user_id,
            metadata=request.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Failed to record error reduction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-savings", summary="获取时间节省统计")
async def get_time_savings(
    time_range: str = Query("7d", description="时间范围：7d, 30d, 90d, all"),
    operation: Optional[str] = Query(None, description="操作类型过滤（可选）"),
    db: Session = Depends(get_db)
):
    """
    获取时间节省统计
    
    Args:
        time_range: 时间范围
        operation: 操作类型过滤
    
    Returns:
        时间节省统计信息
    """
    try:
        service = ValueMetricsService(db)
        stats = await service.get_time_savings(time_range, operation)
        return stats
    except Exception as e:
        logger.error(f"Failed to get time savings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/error-reduction", summary="获取错误减少统计")
async def get_error_reduction(
    time_range: str = Query("7d", description="时间范围：7d, 30d, 90d, all"),
    operation: Optional[str] = Query(None, description="操作类型过滤（可选）"),
    db: Session = Depends(get_db)
):
    """
    获取错误减少统计
    
    Args:
        time_range: 时间范围
        operation: 操作类型过滤
    
    Returns:
        错误减少统计信息
    """
    try:
        service = ValueMetricsService(db)
        stats = await service.get_error_reduction(time_range, operation)
        return stats
    except Exception as e:
        logger.error(f"Failed to get error reduction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

