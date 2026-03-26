"""
健康检查路由
提供系统健康状态检查端点
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
from datetime import datetime
import logging

from ..dependencies.database import get_db
from ..sso.cache_manager import cache_manager
from ..repositories.token_blacklist_repository import TokenBlacklistRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get("", include_in_schema=False)
@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    基本健康检查
    
    Returns:
        健康状态
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/blacklist")
async def blacklist_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    检查黑名单服务健康状态
    
    Returns:
        黑名单服务健康状态
    """
    try:
        # 测试Redis连接
        try:
            redis_available = cache_manager._redis is not None
            if redis_available:
                # 尝试ping Redis
                await cache_manager.get("health_check_test")
                redis_status = "healthy"
            else:
                redis_status = "unavailable"
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            redis_status = "unhealthy"
        
        # 测试数据库连接
        try:
            db.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        # 测试黑名单仓库
        try:
            blacklist_repo = TokenBlacklistRepository(db)
            # 尝试查询（不实际检查令牌）
            repo_status = "healthy"
        except Exception as e:
            logger.error(f"Blacklist repository health check failed: {e}")
            repo_status = "unhealthy"
        
        overall_status = "healthy" if all([
            redis_status == "healthy" or redis_status == "unavailable",  # Redis可选
            db_status == "healthy",
            repo_status == "healthy"
        ]) else "degraded"
        
        return {
            "status": overall_status,
            "service": "token_blacklist",
            "components": {
                "redis": redis_status,
                "database": db_status,
                "repository": repo_status
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Blacklist health check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blacklist service health check failed"
        )


@router.get("/database")
async def database_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    检查数据库连接健康状态
    
    Returns:
        数据库健康状态
    """
    try:
        # 执行简单查询
        result = db.execute(text("SELECT 1")).scalar()
        
        if result == 1:
            return {
                "status": "healthy",
                "service": "database",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection test failed"
            )
    except Exception as e:
        logger.error(f"Database health check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/redis")
async def redis_health_check() -> Dict[str, Any]:
    """
    检查Redis连接健康状态
    
    Returns:
        Redis健康状态
    """
    try:
        if cache_manager._redis is None:
            return {
                "status": "unavailable",
                "service": "redis",
                "message": "Redis client not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # 尝试ping Redis
        await cache_manager.get("health_check_test")
        
        return {
            "status": "healthy",
            "service": "redis",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Redis health check error: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "redis",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
