"""
统一搜索缓存管理器
用于缓存统一搜索结果，提升性能
"""
import logging
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 尝试导入Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available, using memory cache only")


class UnifiedSearchCache:
    """统一搜索缓存管理器"""
    
    def __init__(
        self,
        redis_host: str = "redis",
        redis_port: int = 6379,
        redis_db: int = 0,
        default_ttl: int = 300,  # 5分钟
        max_memory_size: int = 1000  # 内存缓存最大条目数
    ):
        """
        初始化统一搜索缓存
        
        Args:
            redis_host: Redis服务器地址
            redis_port: Redis服务器端口
            redis_db: Redis数据库编号
            default_ttl: 默认TTL（秒）
            max_memory_size: 内存缓存最大条目数
        """
        self.default_ttl = default_ttl
        self.max_memory_size = max_memory_size
        
        # 内存缓存（L1）
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Redis缓存（L2）
        self.redis_enabled = REDIS_AVAILABLE
        self.redis_client = None
        
        if self.redis_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("Unified search cache (Redis) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}, using memory cache only")
                self.redis_enabled = False
                self.redis_client = None
        else:
            logger.info("Unified search cache (memory only) initialized")
    
    def _generate_cache_key(
        self,
        query: str,
        types: List[str],
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成缓存键"""
        key_data = {
            "query": query.lower().strip(),
            "types": sorted(types) if types else [],
            "limit": limit,
            "filters": filters or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"unified_search:{key_hash}"
    
    def get(
        self,
        query: str,
        types: List[str],
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从缓存获取搜索结果
        
        Args:
            query: 搜索查询
            types: 搜索类型列表
            limit: 返回数量限制
            filters: 过滤条件
        
        Returns:
            缓存的搜索结果，如果不存在返回None
        """
        cache_key = self._generate_cache_key(query, types, limit, filters)
        
        # 先查内存缓存
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not self._is_expired(entry):
                logger.debug(f"Memory cache hit: {query}")
                return entry["data"]
            else:
                # 过期，删除
                del self.memory_cache[cache_key]
        
        # 再查Redis缓存
        if self.redis_enabled and self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Redis cache hit: {query}")
                    result = json.loads(cached_data)
                    # 回填内存缓存
                    self.set(query, types, limit, result, filters)
                    return result
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        
        return None
    
    def set(
        self,
        query: str,
        types: List[str],
        limit: int,
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据
        
        Args:
            query: 搜索查询
            types: 搜索类型列表
            limit: 返回数量限制
            data: 搜索结果数据
            filters: 过滤条件
            ttl: TTL（秒），如果为None则使用默认值
        
        Returns:
            是否成功
        """
        cache_key = self._generate_cache_key(query, types, limit, filters)
        ttl_value = ttl or self.default_ttl
        
        # 设置内存缓存
        try:
            # 如果内存缓存已满，删除最旧的条目
            if len(self.memory_cache) >= self.max_memory_size:
                # 删除最旧的条目
                oldest_key = min(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k].get("created_at", datetime.now())
                )
                del self.memory_cache[oldest_key]
            
            self.memory_cache[cache_key] = {
                "data": data,
                "expires_at": datetime.now() + timedelta(seconds=ttl_value),
                "created_at": datetime.now()
            }
            logger.debug(f"Memory cache set: {query}")
        except Exception as e:
            logger.warning(f"Memory cache set error: {e}")
        
        # 设置Redis缓存
        if self.redis_enabled and self.redis_client:
            try:
                serialized = json.dumps(data, default=str)
                self.redis_client.setex(
                    cache_key,
                    ttl_value,
                    serialized
                )
                logger.debug(f"Redis cache set: {query}")
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
        
        return True
    
    def delete(
        self,
        query: Optional[str] = None,
        types: Optional[List[str]] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """删除缓存"""
        if query and types and limit is not None:
            # 删除特定缓存
            cache_key = self._generate_cache_key(query, types, limit, filters)
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            if self.redis_enabled and self.redis_client:
                try:
                    self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Redis cache delete error: {e}")
        else:
            # 清空所有缓存
            self.memory_cache.clear()
            if self.redis_enabled and self.redis_client:
                try:
                    # 删除所有unified_search:开头的键
                    pattern = "unified_search:*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis cache clear error: {e}")
        
        return True
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """检查条目是否过期"""
        if "expires_at" not in entry:
            return True
        return datetime.now() > entry["expires_at"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "memory_cache": {
                "size": len(self.memory_cache),
                "max_size": self.max_memory_size,
                "enabled": True
            },
            "redis_cache": {
                "enabled": self.redis_enabled,
                "available": False
            }
        }
        
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.ping()
                stats["redis_cache"]["available"] = True
            except:
                stats["redis_cache"]["available"] = False
        
        return stats






