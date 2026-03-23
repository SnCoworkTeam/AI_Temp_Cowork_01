"""
令牌Repository
令牌黑名单和数据访问层
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TokenRepository:
    """
    令牌Repository
    管理令牌黑名单和令牌状态
    注意：令牌黑名单存储在Redis中，这里提供接口层
    """
    
    def __init__(self, session: Session):
        self.session = session
        # 令牌黑名单存储在Redis中，不在这里实现
    
    def is_token_blacklisted(self, token: str, redis_client) -> bool:
        """
        检查令牌是否在黑名单中
        
        Args:
            token: 令牌
            redis_client: Redis客户端
        
        Returns:
            是否在黑名单中
        """
        try:
            # 使用Redis存储黑名单
            # 键格式：token:blacklist:{token_hash}
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"token:blacklist:{token_hash}"
            
            # 检查Redis中是否存在
            exists = redis_client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Error checking token blacklist: {str(e)}")
            return False
    
    def add_to_blacklist(
        self,
        token: str,
        expires_at: datetime,
        redis_client
    ) -> bool:
        """
        将令牌添加到黑名单
        
        Args:
            token: 令牌
            expires_at: 过期时间
            redis_client: Redis客户端
        
        Returns:
            是否成功
        """
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"token:blacklist:{token_hash}"
            
            # 计算TTL（秒）
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl > 0:
                redis_client.set(key, "1", ex=ttl)
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding token to blacklist: {str(e)}")
            return False
    
    def remove_from_blacklist(self, token: str, redis_client) -> bool:
        """
        从黑名单中移除令牌
        
        Args:
            token: 令牌
            redis_client: Redis客户端
        
        Returns:
            是否成功
        """
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"token:blacklist:{token_hash}"
            
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error removing token from blacklist: {str(e)}")
            return False
    
    def get_token_info(self, token: str, redis_client) -> Optional[Dict[str, Any]]:
        """
        获取令牌信息（从Redis）
        
        Args:
            token: 令牌
            redis_client: Redis客户端
        
        Returns:
            令牌信息字典
        """
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"token:info:{token_hash}"
            
            info = redis_client.get(key)
            if info:
                import json
                return json.loads(info) if isinstance(info, str) else info
            return None
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return None
    
    def save_token_info(
        self,
        token: str,
        info: Dict[str, Any],
        ttl: int,
        redis_client
    ) -> bool:
        """
        保存令牌信息到Redis
        
        Args:
            token: 令牌
            info: 令牌信息
            ttl: 过期时间（秒）
            redis_client: Redis客户端
        
        Returns:
            是否成功
        """
        try:
            import hashlib
            import json
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"token:info:{token_hash}"
            
            redis_client.set(key, json.dumps(info), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error saving token info: {str(e)}")
            return False









