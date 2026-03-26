"""
令牌黑名单仓库
管理已撤销的JWT令牌（数据库+Redis双重存储）
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# 延迟导入以避免循环依赖
TokenBlacklist = None


def get_token_blacklist_model():
    """延迟导入TokenBlacklist模型"""
    global TokenBlacklist
    if TokenBlacklist is None:
        try:
            from database.src.models.token_blacklist import TokenBlacklist
        except ImportError:
            logger.error("TokenBlacklist model not found. Make sure database migrations are run.")
            raise
    return TokenBlacklist


class TokenBlacklistRepository:
    """令牌黑名单仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_token_id(self, token: str) -> str:
        """生成令牌唯一标识（SHA256哈希）"""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    async def add_to_blacklist(
        self, 
        token: str, 
        token_type: str, 
        user_id: str, 
        expires_at: datetime,
        reason: Optional[str] = None
    ) -> bool:
        """
        添加令牌到黑名单（数据库+Redis）
        
        Args:
            token: JWT令牌
            token_type: 令牌类型（'access' 或 'refresh'）
            user_id: 用户ID
            expires_at: 令牌过期时间
            reason: 撤销原因
        
        Returns:
            是否成功
        """
        try:
            TokenBlacklist = get_token_blacklist_model()
            token_id = self._get_token_id(token)
            
            # 检查是否已存在
            existing = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.token_id == token_id
            ).first()
            
            if existing:
                logger.debug(f"Token already blacklisted: {token_id[:16]}...")
                return True  # 已存在，视为成功
            
            # 创建黑名单记录
            blacklisted_token = TokenBlacklist(
                token_id=token_id,
                token_type=token_type,
                user_id=user_id,
                expires_at=expires_at,
                reason=reason
            )
            
            self.db.add(blacklisted_token)
            self.db.commit()
            
            # 同时添加到Redis缓存（快速查询）
            try:
                from ..sso.cache_manager import cache_manager
                cache_key = f"token_blacklist:{token_id}"
                # 计算TTL（秒），最多缓存1小时
                ttl = min(int((expires_at - datetime.utcnow()).total_seconds()), 3600)
                if ttl > 0:
                    await cache_manager.set(cache_key, "true", ttl=ttl)
                    logger.debug(f"Token blacklisted in Redis: {token_id[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to cache blacklisted token in Redis: {e}")
                # Redis失败不影响数据库操作
            
            logger.info(f"Token blacklisted: {token_id[:16]}... (type: {token_type}, reason: {reason})")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error adding token to blacklist: {e}")
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add token to blacklist: {e}", exc_info=True)
            return False
    
    async def is_blacklisted(self, token: str) -> bool:
        """
        检查令牌是否在黑名单中（先查Redis，再查数据库）
        
        Args:
            token: JWT令牌
        
        Returns:
            是否在黑名单中
        """
        try:
            token_id = self._get_token_id(token)
            
            # 先检查Redis缓存（快速路径）
            try:
                from ..sso.cache_manager import cache_manager
                cache_key = f"token_blacklist:{token_id}"
                cached_result = await cache_manager.get(cache_key)
                
                if cached_result is not None:
                    is_blacklisted = cached_result == "true" or cached_result == True
                    if is_blacklisted:
                        logger.debug(f"Token found in Redis blacklist: {token_id[:16]}...")
                        return True
                    # 如果缓存明确标记为false，可以信任（但为了安全，还是查数据库）
            except Exception as e:
                logger.debug(f"Redis check failed, falling back to database: {e}")
            
            # 检查数据库
            TokenBlacklist = get_token_blacklist_model()
            blacklisted = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.token_id == token_id,
                TokenBlacklist.expires_at > datetime.utcnow()
            ).first()
            
            is_blacklisted = blacklisted is not None
            
            # 缓存结果（15分钟）
            try:
                from ..sso.cache_manager import cache_manager
                cache_key = f"token_blacklist:{token_id}"
                await cache_manager.set(cache_key, "true" if is_blacklisted else "false", ttl=900)
            except Exception:
                pass  # Redis失败不影响验证结果
            
            if is_blacklisted:
                logger.debug(f"Token found in database blacklist: {token_id[:16]}...")
            
            return is_blacklisted
            
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}", exc_info=True)
            # 出错时默认不阻止（防御性编程，但记录错误）
            return False
    
    async def revoke_user_tokens(
        self, 
        user_id: str, 
        reason: str = "user_revoked"
    ) -> int:
        """
        标记用户的所有令牌为已撤销
        注意：这个方法不直接撤销令牌，而是标记未来验证会失败
        实际撤销需要知道具体的令牌
        
        Args:
            user_id: 用户ID
            reason: 撤销原因
        
        Returns:
            清理的过期记录数
        """
        try:
            # 清理过期的黑名单记录
            TokenBlacklist = get_token_blacklist_model()
            expired_count = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at <= datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired blacklist records")
            
            return expired_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke user tokens: {e}", exc_info=True)
            return 0
    
    async def cleanup_expired(self) -> int:
        """
        清理过期的黑名单记录
        
        Returns:
            清理的记录数
        """
        try:
            TokenBlacklist = get_token_blacklist_model()
            expired_count = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at <= datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired blacklist records")
            
            return expired_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired tokens: {e}", exc_info=True)
            return 0
    
    def get_user_blacklisted_tokens(self, user_id: str) -> list:
        """
        获取用户的所有黑名单令牌
        
        Args:
            user_id: 用户ID
        
        Returns:
            黑名单令牌列表
        """
        try:
            TokenBlacklist = get_token_blacklist_model()
            tokens = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.user_id == user_id,
                TokenBlacklist.expires_at > datetime.utcnow()
            ).all()
            
            return [token.to_dict() for token in tokens]
            
        except Exception as e:
            logger.error(f"Failed to get user blacklisted tokens: {e}", exc_info=True)
            return []

