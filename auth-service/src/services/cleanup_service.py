"""
清理服务
定期清理过期的黑名单记录和其他临时数据
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from ..repositories.token_blacklist_repository import TokenBlacklistRepository

logger = logging.getLogger(__name__)


class CleanupService:
    """清理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.blacklist_repo = TokenBlacklistRepository(db)
    
    async def cleanup_expired_blacklist_tokens(self) -> int:
        """
        清理过期的黑名单记录
        
        Returns:
            清理的记录数
        """
        try:
            deleted_count = await self.blacklist_repo.cleanup_expired()
            logger.info(f"Cleaned up {deleted_count} expired blacklist records")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired blacklist tokens: {e}", exc_info=True)
            return 0
    
    async def cleanup_all(self) -> dict:
        """
        执行所有清理任务
        
        Returns:
            清理结果统计
        """
        results = {
            "blacklist_tokens": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # 清理过期的黑名单记录
            results["blacklist_tokens"] = await self.cleanup_expired_blacklist_tokens()
            
            logger.info(f"Cleanup completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return results


async def run_cleanup_task(db: Session) -> dict:
    """
    运行清理任务（用于定时任务）
    
    Args:
        db: 数据库会话
    
    Returns:
        清理结果统计
    """
    service = CleanupService(db)
    return await service.cleanup_all()

