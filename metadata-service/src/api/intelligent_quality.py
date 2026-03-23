"""
智能数据质量检测API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.intelligent_quality_service import IntelligentQualityService
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/intelligent-quality", tags=["Intelligent Quality"])
logger = setup_logger(__name__)


@router.get("/detect-issues", summary="检测数据质量问题")
async def detect_quality_issues(
    entity_id: Optional[int] = Query(None, description="实体ID，如果提供则只检测该实体"),
    entity_type: Optional[str] = Query(None, description="实体类型，如果提供则只检测该类型"),
    db: Session = Depends(get_db)
):
    """
    检测数据质量问题
    
    支持：
    - 全量检测
    - 按实体ID检测
    - 按实体类型检测
    """
    try:
        service = IntelligentQualityService(db)
        issues = await service.detect_quality_issues(
            entity_id=entity_id,
            entity_type=entity_type
        )
        await service.close()
        
        return {
            "success": True,
            "issues": issues,
            "count": len(issues)
        }
    except Exception as e:
        logger.error(f"Failed to detect quality issues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-score/{entity_id}", summary="计算实体质量分数")
async def calculate_quality_score(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """
    计算实体质量分数
    
    基于多个维度评估实体质量：
    - 名称完整性
    - 描述完整性
    - 元数据完整性
    - 关联关系完整性
    """
    try:
        service = IntelligentQualityService(db)
        score = await service.calculate_quality_score(entity_id)
        await service.close()
        
        return {
            "success": True,
            "quality_score": score
        }
    except Exception as e:
        logger.error(f"Failed to calculate quality score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




