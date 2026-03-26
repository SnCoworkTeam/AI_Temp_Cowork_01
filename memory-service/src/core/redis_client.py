"""
Redis客户端
用于缓存会话上下文和短期记忆
"""
import logging
import json
import os
from typing import List, Optional
try:
    import redis.asyncio as redis
except ImportError:
    # 如果redis.asyncio不可用，尝试使用同步版本
    import redis
    # 创建一个简单的异步包装器
    class AsyncRedis:
        def __init__(self, *args, **kwargs):
            self._client = redis.Redis(*args, **kwargs)
        
        async def get(self, key):
            return self._client.get(key)
        
        async def setex(self, key, time, value):
            return self._client.setex(key, time, value)
        
        async def delete(self, key):
            return self._client.delete(key)
        
        async def close(self):
            self._client.close()
    
    # 创建一个模拟的from_url函数
    def from_url(*args, **kwargs):
        return AsyncRedis()
    
    redis.from_url = from_url

from .memory_types import MemoryRecord

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis客户端"""
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )
        return self.redis_client
    
    async def get_session_context(self, session_id: str) -> Optional[List[MemoryRecord]]:
        """获取会话上下文缓存"""
        try:
            client = await self._get_client()
            key = f"session_context:{session_id}"
            data = await client.get(key)
            
            if data:
                memories_data = json.loads(data)
                return [MemoryRecord(**m) for m in memories_data]
            return None
        except Exception as e:
            logger.error(f"Failed to get session context: {e}", exc_info=True)
            return None
    
    async def set_session_context(self, session_id: str, memories: List[MemoryRecord], ttl: int = 3600):
        """设置会话上下文缓存"""
        try:
            client = await self._get_client()
            key = f"session_context:{session_id}"
            memories_data = [m.dict() for m in memories]
            data = json.dumps(memories_data, ensure_ascii=False)
            await client.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Failed to set session context: {e}", exc_info=True)
    
    async def invalidate_session_cache(self, session_id: str):
        """使会话缓存失效"""
        try:
            client = await self._get_client()
            key = f"session_context:{session_id}"
            await client.delete(key)
        except Exception as e:
            logger.error(f"Failed to invalidate session cache: {e}", exc_info=True)
    
    async def set_memory_ttl(self, memory_id: str, ttl: int):
        """设置记忆TTL（用于短期记忆）"""
        try:
            client = await self._get_client()
            key = f"memory:{memory_id}"
            await client.setex(key, ttl, "1")
        except Exception as e:
            logger.error(f"Failed to set memory TTL: {e}", exc_info=True)
    
    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

