"""
Redis客户端管理
提供Redis连接池和会话存储
"""
import logging
from typing import Optional, Any
import redis.asyncio as aioredis
import redis
from pydantic_settings import BaseSettings
import json
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisSettings(BaseSettings):
    """Redis配置"""
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    
    # 连接池配置
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


_settings = None


def get_redis_settings() -> RedisSettings:
    """获取Redis配置（单例）"""
    global _settings
    if _settings is None:
        _settings = RedisSettings()
    return _settings


class RedisClient:
    """Redis客户端（同步）"""
    
    def __init__(self, settings: Optional[RedisSettings] = None):
        """
        初始化Redis客户端
        
        Args:
            settings: Redis配置，如果为None则从环境变量加载
        """
        self.settings = settings or get_redis_settings()
        self._client: Optional[redis.Redis] = None
    
    def get_client(self) -> redis.Redis:
        """
        获取Redis客户端
        
        Returns:
            Redis客户端实例
        """
        if self._client is not None:
            return self._client
        
        # 创建连接池
        pool = redis.ConnectionPool(
            host=self.settings.REDIS_HOST,
            port=self.settings.REDIS_PORT,
            db=self.settings.REDIS_DB,
            password=self.settings.REDIS_PASSWORD,
            socket_timeout=self.settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=self.settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            max_connections=self.settings.REDIS_MAX_CONNECTIONS,
            retry_on_timeout=self.settings.REDIS_RETRY_ON_TIMEOUT,
            health_check_interval=self.settings.REDIS_HEALTH_CHECK_INTERVAL
        )
        
        self._client = redis.Redis(connection_pool=pool)
        
        # 测试连接
        try:
            self._client.ping()
            logger.info(f"Redis client connected: {self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
        
        return self._client
    
    def set(self, key: str, value: Any, ex: Optional[int] = None):
        """
        设置键值
        
        Args:
            key: 键
            value: 值（会自动序列化）
            ex: 过期时间（秒）
        """
        client = self.get_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        client.set(key, value, ex=ex)
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取值
        
        Args:
            key: 键
        
        Returns:
            值（如果不存在返回None）
        """
        client = self.get_client()
        value = client.get(key)
        if value is None:
            return None
        
        try:
            # 尝试JSON解析
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON，返回原始字符串
            return value.decode('utf-8') if isinstance(value, bytes) else value
    
    def delete(self, *keys: str):
        """删除键"""
        client = self.get_client()
        client.delete(*keys)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        client = self.get_client()
        return bool(client.exists(key))
    
    def expire(self, key: str, seconds: int):
        """设置过期时间"""
        client = self.get_client()
        client.expire(key, seconds)
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis client closed")


class AsyncRedisClient:
    """异步Redis客户端"""
    
    def __init__(self, settings: Optional[RedisSettings] = None):
        """
        初始化异步Redis客户端
        
        Args:
            settings: Redis配置
        """
        self.settings = settings or get_redis_settings()
        self._client: Optional[aioredis.Redis] = None
    
    async def get_client(self) -> aioredis.Redis:
        """
        获取异步Redis客户端
        
        Returns:
            异步Redis客户端实例
        """
        if self._client is not None:
            return self._client
        
        self._client = await aioredis.from_url(
            f"redis://{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}/{self.settings.REDIS_DB}",
            password=self.settings.REDIS_PASSWORD,
            socket_timeout=self.settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=self.settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            max_connections=self.settings.REDIS_MAX_CONNECTIONS,
            retry_on_timeout=self.settings.REDIS_RETRY_ON_TIMEOUT,
            health_check_interval=self.settings.REDIS_HEALTH_CHECK_INTERVAL
        )
        
        # 测试连接
        try:
            await self._client.ping()
            logger.info(f"Async Redis client connected: {self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Async Redis connection failed: {str(e)}")
            raise
        
        return self._client
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        """异步设置键值"""
        client = await self.get_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await client.set(key, value, ex=ex)
    
    async def get(self, key: str) -> Optional[Any]:
        """异步获取值"""
        client = await self.get_client()
        value = await client.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value.decode('utf-8') if isinstance(value, bytes) else value
    
    async def delete(self, *keys: str):
        """异步删除键"""
        client = await self.get_client()
        await client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """异步检查键是否存在"""
        client = await self.get_client()
        return bool(await client.exists(key))
    
    async def close(self):
        """关闭异步连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Async Redis client closed")


# 全局Redis客户端实例
_redis_client: Optional[RedisClient] = None
_async_redis_client: Optional[AsyncRedisClient] = None


def get_redis_client() -> RedisClient:
    """获取Redis客户端实例（单例）"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


def get_async_redis_client() -> AsyncRedisClient:
    """获取异步Redis客户端实例（单例）"""
    global _async_redis_client
    if _async_redis_client is None:
        _async_redis_client = AsyncRedisClient()
    return _async_redis_client









