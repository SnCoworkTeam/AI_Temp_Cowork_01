"""
推荐结果缓存服务
提供推荐结果的缓存和优化
"""
import logging
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)


class RecommendationCache:
    """推荐结果缓存"""
    
    def __init__(
        self,
        redis_host: str = "redis",
        redis_port: int = 6379,
        default_ttl: int = 3600  # 1小时
    ):
        """
        初始化推荐缓存
        
        Args:
            redis_host: Redis主机
            redis_port: Redis端口
            default_ttl: 默认TTL（秒）
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        self.default_ttl = default_ttl
        self.cache_prefix = "recommendation:"
    
    def _generate_cache_key(
        self,
        cache_type: str,
        entity_id: int,
        **kwargs
    ) -> str:
        """
        生成缓存键
        
        Args:
            cache_type: 缓存类型（related, similar, impact等）
            entity_id: 实体ID
            **kwargs: 其他参数
        
        Returns:
            缓存键
        """
        # 构建参数字符串
        params = f"{entity_id}"
        if kwargs:
            sorted_params = sorted(kwargs.items())
            params += ":" + ":".join(f"{k}={v}" for k, v in sorted_params)
        
        # 生成哈希
        key_hash = hashlib.md5(params.encode()).hexdigest()[:8]
        return f"{self.cache_prefix}{cache_type}:{key_hash}"
    
    def get(
        self,
        cache_type: str,
        entity_id: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存
        
        Args:
            cache_type: 缓存类型
            entity_id: 实体ID
            **kwargs: 其他参数
        
        Returns:
            缓存数据，如果不存在返回None
        """
        try:
            cache_key = self._generate_cache_key(cache_type, entity_id, **kwargs)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get cache: {e}")
            return None
    
    def set(
        self,
        cache_type: str,
        entity_id: int,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        设置缓存
        
        Args:
            cache_type: 缓存类型
            entity_id: 实体ID
            data: 缓存数据
            ttl: TTL（秒），如果为None使用默认值
            **kwargs: 其他参数
        
        Returns:
            是否设置成功
        """
        try:
            cache_key = self._generate_cache_key(cache_type, entity_id, **kwargs)
            ttl = ttl or self.default_ttl
            
            cached_data = json.dumps(data, default=str)
            self.redis_client.setex(cache_key, ttl, cached_data)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache: {e}")
            return False
    
    def invalidate(
        self,
        cache_type: str,
        entity_id: int,
        **kwargs
    ) -> bool:
        """
        使缓存失效
        
        Args:
            cache_type: 缓存类型
            entity_id: 实体ID
            **kwargs: 其他参数
        
        Returns:
            是否删除成功
        """
        try:
            cache_key = self._generate_cache_key(cache_type, entity_id, **kwargs)
            self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
            return False
    
    def invalidate_all_for_entity(self, entity_id: int) -> int:
        """
        使实体的所有缓存失效
        
        Args:
            entity_id: 实体ID
        
        Returns:
            删除的缓存数量
        """
        try:
            pattern = f"{self.cache_prefix}*:{entity_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                return self.redis_client.delete(*keys)
            
            return 0
        except Exception as e:
            logger.warning(f"Failed to invalidate all cache for entity: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息
        """
        try:
            pattern = f"{self.cache_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            stats = {
                "total_keys": len(keys),
                "cache_prefix": self.cache_prefix,
                "default_ttl": self.default_ttl
            }
            
            # 按类型统计
            by_type = {}
            for key in keys:
                parts = key.split(":")
                if len(parts) >= 2:
                    cache_type = parts[1]
                    by_type[cache_type] = by_type.get(cache_type, 0) + 1
            
            stats["by_type"] = by_type
            return stats
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "error": str(e)
            }




