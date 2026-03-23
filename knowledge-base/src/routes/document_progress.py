"""
文档处理进度API路由
支持查询处理进度、预估剩余时间等
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from ..dependencies.database import get_db
from ..core.processing_progress import get_progress_tracker, remove_progress_tracker
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/documents/{document_id}/progress")
async def get_document_progress(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档处理进度
    
    Returns:
        进度信息（百分比、当前阶段、预估剩余时间等）
    """
    try:
        progress_tracker = get_progress_tracker(document_id)
        progress = progress_tracker.get_progress()
        
        return progress
    except Exception as e:
        logger.error(f"Error getting document progress: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting document progress: {str(e)}")


@router.delete("/documents/{document_id}/progress")
async def clear_document_progress(
    document_id: str,
    db: Session = Depends(get_db)
):
    """清除文档进度跟踪（处理完成后调用）"""
    try:
        remove_progress_tracker(document_id)
        return {"message": "Progress tracker removed"}
    except Exception as e:
        logger.error(f"Error clearing document progress: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing document progress: {str(e)}")


