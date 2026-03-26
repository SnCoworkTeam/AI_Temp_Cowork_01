"""
健康检查API路由
"""
import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入shared_libs
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db, get_database_engine
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "metadata-service"
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """就绪检查（检查数据库连接）"""
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": "metadata-service",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not_ready",
            "service": "metadata-service",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/health/live")
async def liveness_check():
    """存活检查"""
    return {
        "status": "alive",
        "service": "metadata-service"
    }

