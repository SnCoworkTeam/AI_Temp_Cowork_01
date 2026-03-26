"""
多级缓存管理器
L1: 内存缓存（热点数据）
L2: Redis缓存（跨服务共享）
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import hashlib

logger = logging.getLogger(__name__)

# 尝试导入Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available, L2 cache disabled")


class MultiLevelCache:
    """多级缓存管理器"""
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_ttl: int = 300,  # 5分钟
        redis_host: str = "localhost",
        redis_port: int = 6379,
        l2_ttl: int = 3600  # 1小时
    ):
        """
        初始化多级缓存
        
        Args:
            l1_max_size: L1缓存最大条目数
            l1_ttl: L1缓存TTL（秒）
            redis_host: Redis服务器地址
            redis_port: Redis服务器端口
            l2_ttl: L2缓存TTL（秒）
        """
        # L1缓存（内存）
        self.l1_cache: Dict[str, Dict[str, Any]] = {}
        self.l1_max_size = l1_max_size
        self.l1_ttl = l1_ttl
        
        # L2缓存（Redis）
        self.l2_enabled = REDIS_AVAILABLE
        self.l2_ttl = l2_ttl
        self.redis_client = None
        
        if self.l2_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True
                )
                logger.info("L2 cache (Redis) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                self.l2_enabled = False
    
    def _generate_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key = ":".join(key_parts)
        # 如果键太长，使用哈希
        if len(key) > 200:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        return key
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """检查条目是否过期"""
        if "expires_at" not in entry:
            return True
        return datetime.now() > entry["expires_at"]
    
    async def get(self, prefix: str, *args) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            prefix: 缓存前缀
            *args: 缓存键参数
        
        Returns:
            缓存的数据，如果不存在返回None
        """
        key = self._generate_key(prefix, *args)
        
        # 先查L1缓存
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not self._is_expired(entry):
                logger.debug(f"L1 cache hit: {key}")
                return entry["value"]
            else:
                # 过期，删除
                del self.l1_cache[key]
        
        # 再查L2缓存
        if self.l2_enabled and self.redis_client:
            try:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    logger.debug(f"L2 cache hit: {key}")
                    value = json.loads(cached_data)
                    # 回填L1缓存
                    await self.set(prefix, value, *args)
                    return value
            except Exception as e:
                logger.warning(f"L2 cache get error: {e}")
        
        return None
    
    async def set(
        self,
        prefix: str,
        value: Any,
        *args,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据
        
        Args:
            prefix: 缓存前缀
            value: 要缓存的值
            *args: 缓存键参数
            ttl: TTL（秒），如果为None则使用默认值
        
        Returns:
            是否成功
        """
        key = self._generate_key(prefix, *args)
        ttl_value = ttl or self.l1_ttl
        
        # 设置L1缓存
        try:
            # 如果L1缓存已满，删除最旧的条目
            if len(self.l1_cache) >= self.l1_max_size:
                # 删除最旧的条目（简单策略：删除第一个）
                oldest_key = next(iter(self.l1_cache))
                del self.l1_cache[oldest_key]
            
            self.l1_cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl_value),
                "created_at": datetime.now()
            }
            logger.debug(f"L1 cache set: {key}")
        except Exception as e:
            logger.warning(f"L1 cache set error: {e}")
        
        # 设置L2缓存
        if self.l2_enabled and self.redis_client:
            try:
                serialized = json.dumps(value, default=str)
                await self.redis_client.setex(
                    key,
                    ttl_value or self.l2_ttl,
                    serialized
                )
                logger.debug(f"L2 cache set: {key}")
            except Exception as e:
                logger.warning(f"L2 cache set error: {e}")
        
        return True
    
    async def delete(self, prefix: str, *args) -> bool:
        """删除缓存"""
        key = self._generate_key(prefix, *args)
        
        # 删除L1缓存
        if key in self.l1_cache:
            del self.l1_cache[key]
        
        # 删除L2缓存
        if self.l2_enabled and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"L2 cache delete error: {e}")
        
        return True
    
    async def clear(self, prefix: Optional[str] = None):
        """清空缓存"""
        if prefix:
            # 清空特定前缀的缓存
            keys_to_delete = [
                key for key in self.l1_cache.keys()
                if key.startswith(prefix)
            ]
            for key in keys_to_delete:
                del self.l1_cache[key]
            
            if self.l2_enabled and self.redis_client:
                try:
                    pattern = f"{prefix}:*"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"L2 cache clear error: {e}")
        else:
            # 清空所有缓存
            self.l1_cache.clear()
            if self.l2_enabled and self.redis_client:
                try:
                    await self.redis_client.flushdb()
                except Exception as e:
                    logger.warning(f"L2 cache flush error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "l1_cache": {
                "size": len(self.l1_cache),
                "max_size": self.l1_max_size,
                "enabled": True
            },
            "l2_cache": {
                "enabled": self.l2_enabled
            }
        }
        
        if self.l2_enabled and self.redis_client:
            try:
                # 同步获取Redis信息（简化版）
                stats["l2_cache"]["available"] = True
            except:
                stats["l2_cache"]["available"] = False
        
        return stats







