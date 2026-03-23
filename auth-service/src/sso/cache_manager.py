"""
Redis缓存管理器
管理用户会话、令牌等缓存数据
"""
from typing import Optional, Any, Dict
import json
import logging
import redis.asyncio as aioredis
from datetime import timedelta

from ..config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None
    
    async def connect(self):
        """连接到Redis"""
        try:
            self._connection_pool = aioredis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                max_connections=50
            )
            self._redis = aioredis.Redis(connection_pool=self._connection_pool)
            
            # 测试连接
            await self._redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值，如果不存在则返回None
        """
        try:
            if not self._redis:
                await self.connect()
            
            value = await self._redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Failed to get cache key '{key}': {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则不过期
        """
        try:
            if not self._redis:
                await self.connect()
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if ttl:
                await self._redis.setex(key, ttl, value)
            else:
                await self._redis.set(key, value)
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {str(e)}")
    
    async def delete(self, key: str):
        """
        删除缓存键
        
        Args:
            key: 缓存键
        """
        try:
            if not self._redis:
                await self.connect()
            
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
        
        Returns:
            是否存在
        """
        try:
            if not self._redis:
                await self.connect()
            
            return bool(await self._redis.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key '{key}': {str(e)}")
            return False
    
    async def expire(self, key: str, ttl: int):
        """
        设置键的过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
        """
        try:
            if not self._redis:
                await self.connect()
            
            await self._redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Failed to set expire for key '{key}': {str(e)}")

    async def get_client(self) -> Optional[aioredis.Redis]:
        """获取Redis客户端实例（需要时自动连接）"""
        try:
            if not self._redis:
                await self.connect()
            return self._redis
        except Exception as e:
            logger.error(f"Failed to get redis client: {str(e)}")
            return None
    
    # 用户会话缓存方法
    async def set_user_session(
        self,
        session_id: str,
        user_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """设置用户会话缓存"""
        key = f"session:{session_id}"
        ttl = ttl or settings.CACHE_SESSION_TTL
        await self.set(key, user_data, ttl)
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取用户会话缓存"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_user_session(self, session_id: str):
        """删除用户会话缓存"""
        key = f"session:{session_id}"
        await self.delete(key)
    
    # 访问令牌缓存方法
    async def set_access_token(
        self,
        token: str,
        token_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """设置访问令牌缓存"""
        key = f"access_token:{token}"
        ttl = ttl or settings.CACHE_ACCESS_TOKEN_TTL
        await self.set(key, token_data, ttl)
    
    async def get_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """获取访问令牌缓存"""
        key = f"access_token:{token}"
        return await self.get(key)
    
    async def delete_access_token(self, token: str):
        """删除访问令牌缓存"""
        key = f"access_token:{token}"
        await self.delete(key)
    
    # 刷新令牌缓存方法
    async def set_refresh_token(
        self,
        token: str,
        token_data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """设置刷新令牌缓存"""
        key = f"refresh_token:{token}"
        ttl = ttl or settings.CACHE_REFRESH_TOKEN_TTL
        await self.set(key, token_data, ttl)
    
    async def get_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """获取刷新令牌缓存"""
        key = f"refresh_token:{token}"
        return await self.get(key)
    
    async def delete_refresh_token(self, token: str):
        """删除刷新令牌缓存"""
        key = f"refresh_token:{token}"
        await self.delete(key)
    
    # 用户令牌映射（用于查找用户的所有令牌）
    async def add_user_token(self, user_id: str, token_type: str, token: str):
        """添加用户令牌到映射"""
        if not self._redis:
            await self.connect()
        key = f"user_tokens:{user_id}:{token_type}"
        await self._redis.sadd(key, token)
        # 设置过期时间
        max_ttl = max(
            settings.CACHE_ACCESS_TOKEN_TTL,
            settings.CACHE_REFRESH_TOKEN_TTL
        )
        await self.expire(key, max_ttl)
    
    async def get_user_tokens(self, user_id: str, token_type: str) -> list:
        """获取用户的所有令牌"""
        key = f"user_tokens:{user_id}:{token_type}"
        if not self._redis:
            await self.connect()
        return list(await self._redis.smembers(key))
    
    async def delete_user_tokens(self, user_id: str, token_type: str):
        """删除用户的所有令牌"""
        key = f"user_tokens:{user_id}:{token_type}"
        await self.delete(key)


# 全局缓存管理器实例
cache_manager = CacheManager()
