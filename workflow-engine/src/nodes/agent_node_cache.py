"""
智能体节点缓存策略
实现内存+Redis分层缓存，提升执行性能
"""
import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

# 导入Redis客户端
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.redis_client import get_async_redis_client, AsyncRedisClient

logger = logging.getLogger(__name__)


class HybridCache:
    """
    内存 + Redis分层缓存
    L1: 内存缓存（快速访问，进程内）
    L2: Redis缓存（持久化，跨进程共享）
    """
    
    def __init__(self, memory_cache_size: int = 1000, default_ttl: int = 300):
        """
        初始化混合缓存
        
        Args:
            memory_cache_size: 内存缓存最大条目数
            default_ttl: 默认TTL（秒）
        """
        # L1: 内存缓存
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cache_size = memory_cache_size
        self.default_ttl = default_ttl
        
        # L2: Redis缓存（延迟初始化）
        self._redis_client = None  # 存储aioredis.Redis实例
        self._cache_prefix = "agent_cache:"
    
    async def _get_redis_client(self):
        """获取Redis客户端实例（延迟初始化）"""
        if self._redis_client is None:
            try:
                redis_client_wrapper = get_async_redis_client()
                self._redis_client = await redis_client_wrapper.get_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}. Using memory cache only.")
                return None
        return self._redis_client
    
    def _is_expired(self, cache_item: Dict[str, Any]) -> bool:
        """检查缓存项是否过期"""
        if "expires_at" not in cache_item:
            return False
        return datetime.now() > cache_item["expires_at"]
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值（先查L1，再查L2，L2命中时回填L1）
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        # 1. 先检查L1内存缓存
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]
            if not self._is_expired(cache_item):
                logger.debug(f"Cache hit (L1): {key}")
                return cache_item["data"]
            else:
                # 过期，删除
                del self.memory_cache[key]
        
        # 2. 检查L2 Redis缓存
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                redis_key = f"{self._cache_prefix}{key}"
                redis_data = await redis_client.get(redis_key)
                
                if redis_data:
                    # 解析数据
                    try:
                        cache_data = json.loads(redis_data)
                        logger.debug(f"Cache hit (L2): {key}")
                        
                        # 回填L1内存缓存
                        self.memory_cache[key] = {
                            "data": cache_data["data"],
                            "expires_at": datetime.fromisoformat(cache_data["expires_at"])
                        }
                        
                        # 检查是否过期
                        if not self._is_expired(self.memory_cache[key]):
                            return cache_data["data"]
                        else:
                            # Redis中的数据也过期了，删除
                            await redis_client.delete(redis_key)
                            del self.memory_cache[key]
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse cache data from Redis: {e}")
                        await redis_client.delete(redis_key)
            except Exception as e:
                logger.warning(f"Error reading from Redis cache: {e}")
        
        # 缓存未命中
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值（同时写入L1和L2）
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认TTL
            
        Returns:
            是否成功
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # 1. 设置L1内存缓存
        # 检查缓存大小，如果超过限制则删除最旧的项
        if len(self.memory_cache) >= self.memory_cache_size:
            # 删除最旧的项（简单策略：删除第一个）
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = {
            "data": value,
            "expires_at": expires_at
        }
        
        # 2. 设置L2 Redis缓存
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                redis_key = f"{self._cache_prefix}{key}"
                cache_data = {
                    "data": value,
                    "expires_at": expires_at.isoformat()
                }
                await redis_client.setex(
                    redis_key,
                    ttl,
                    json.dumps(cache_data, ensure_ascii=False, default=str)
                )
                logger.debug(f"Cache set (L1+L2): {key}, TTL={ttl}s")
            except Exception as e:
                logger.warning(f"Error writing to Redis cache: {e}")
                # Redis失败不影响内存缓存
        else:
            logger.debug(f"Cache set (L1 only): {key}, TTL={ttl}s")
        
        return True
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存（同时删除L1和L2）
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        # 删除L1
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # 删除L2
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                redis_key = f"{self._cache_prefix}{key}"
                await redis_client.delete(redis_key)
            except Exception as e:
                logger.warning(f"Error deleting from Redis cache: {e}")
        
        return True
    
    async def clear(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                # 删除所有agent_cache:开头的键
                pattern = f"{self._cache_prefix}*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Error clearing Redis cache: {e}")
    
    def _cleanup_expired(self):
        """清理过期的内存缓存项"""
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")


def generate_cache_key(agent_id: str, input_data: Dict[str, Any], context_hash: Optional[str] = None) -> str:
    """
    生成缓存键
    
    Args:
        agent_id: 智能体ID
        input_data: 输入数据
        context_hash: 上下文哈希（可选）
        
    Returns:
        缓存键
    """
    # 构建缓存键的组成部分
    key_parts = {
        "agent_id": agent_id,
        "input": input_data.get("content", ""),
        "context": context_hash or ""
    }
    
    # 生成哈希
    key_string = json.dumps(key_parts, sort_keys=True, ensure_ascii=False)
    key_hash = hashlib.sha256(key_string.encode('utf-8')).hexdigest()[:16]
    
    return f"agent:{agent_id}:{key_hash}"

