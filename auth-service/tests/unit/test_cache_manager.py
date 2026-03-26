"""
缓存管理器测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestCacheManager:
    """缓存管理器测试"""
    
    @pytest.fixture
    def cache_manager(self):
        """创建CacheManager实例"""
        from src.sso.cache_manager import CacheManager
        return CacheManager()
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        redis = AsyncMock()
        redis.ping = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.exists = AsyncMock(return_value=False)
        redis.expire = AsyncMock()
        redis.close = AsyncMock()
        return redis
    
    @pytest.fixture
    def mock_connection_pool(self):
        """模拟连接池"""
        pool = AsyncMock()
        pool.disconnect = AsyncMock()
        return pool
    
    def test_cache_manager_initialization(self, cache_manager):
        """测试CacheManager初始化"""
        assert cache_manager is not None
        assert cache_manager._redis is None
        assert cache_manager._connection_pool is None
    
    @pytest.mark.asyncio
    async def test_connect_success(self, cache_manager, mock_redis, mock_connection_pool):
        """测试连接Redis成功"""
        with patch('src.sso.cache_manager.aioredis.ConnectionPool', return_value=mock_connection_pool), \
             patch('src.sso.cache_manager.aioredis.Redis', return_value=mock_redis):
            
            await cache_manager.connect()
            
            assert cache_manager._redis is not None
            assert cache_manager._connection_pool is not None
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, cache_manager):
        """测试连接Redis失败"""
        with patch('src.sso.cache_manager.aioredis.ConnectionPool', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                await cache_manager.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, cache_manager, mock_redis, mock_connection_pool):
        """测试断开Redis连接"""
        cache_manager._redis = mock_redis
        cache_manager._connection_pool = mock_connection_pool
        
        await cache_manager.disconnect()
        
        mock_redis.close.assert_called_once()
        mock_connection_pool.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_success(self, cache_manager, mock_redis):
        """测试获取缓存值成功"""
        test_value = {"key": "value"}
        mock_redis.get.return_value = json.dumps(test_value)
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get("test_key")
        
        assert result == test_value
        mock_redis.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, cache_manager, mock_redis):
        """测试获取不存在的缓存值"""
        mock_redis.get.return_value = None
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get("nonexistent_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_string_value(self, cache_manager, mock_redis):
        """测试获取字符串值"""
        mock_redis.get.return_value = "simple_string"
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get("string_key")
        
        assert result == "simple_string"
    
    @pytest.mark.asyncio
    async def test_get_invalid_json(self, cache_manager, mock_redis):
        """测试获取无效JSON值"""
        mock_redis.get.return_value = "invalid json{"
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get("invalid_json_key")
        
        assert result == "invalid json{"
    
    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_manager, mock_redis):
        """测试设置缓存值（带TTL）"""
        cache_manager._redis = mock_redis
        
        await cache_manager.set("test_key", {"data": "value"}, ttl=3600)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_without_ttl(self, cache_manager, mock_redis):
        """测试设置缓存值（不带TTL）"""
        cache_manager._redis = mock_redis
        
        await cache_manager.set("test_key", {"data": "value"})
        
        mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_string_value(self, cache_manager, mock_redis):
        """测试设置字符串值"""
        cache_manager._redis = mock_redis
        
        await cache_manager.set("test_key", "simple_string", ttl=3600)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_success(self, cache_manager, mock_redis):
        """测试删除缓存值成功"""
        cache_manager._redis = mock_redis
        
        await cache_manager.delete("test_key")
        
        mock_redis.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_exists_true(self, cache_manager, mock_redis):
        """测试检查缓存键存在"""
        mock_redis.exists.return_value = True
        cache_manager._redis = mock_redis
        
        result = await cache_manager.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_exists_false(self, cache_manager, mock_redis):
        """测试检查缓存键不存在"""
        mock_redis.exists.return_value = False
        cache_manager._redis = mock_redis
        
        result = await cache_manager.exists("nonexistent_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_expire(self, cache_manager, mock_redis):
        """测试设置过期时间"""
        cache_manager._redis = mock_redis
        
        await cache_manager.expire("test_key", 3600)
        
        mock_redis.expire.assert_called_once_with("test_key", 3600)
    
    @pytest.mark.asyncio
    async def test_set_user_session(self, cache_manager, mock_redis):
        """测试设置用户会话"""
        session_data = {"session_id": "session123", "user_id": "user123"}
        cache_manager._redis = mock_redis
        
        await cache_manager.set_user_session("session123", session_data, ttl=3600)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_session(self, cache_manager, mock_redis):
        """测试获取用户会话"""
        session_data = {"session_id": "session123", "user_id": "user123"}
        mock_redis.get.return_value = json.dumps(session_data)
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get_user_session("session123")
        
        assert result == session_data
    
    @pytest.mark.asyncio
    async def test_delete_user_session(self, cache_manager, mock_redis):
        """测试删除用户会话"""
        cache_manager._redis = mock_redis
        
        await cache_manager.delete_user_session("session123")
        
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_access_token(self, cache_manager, mock_redis):
        """测试设置访问令牌"""
        token_data = {"user_id": "user123", "username": "testuser"}
        cache_manager._redis = mock_redis
        
        await cache_manager.set_access_token("token123", token_data, ttl=3600)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_access_token(self, cache_manager, mock_redis):
        """测试获取访问令牌"""
        token_data = {"user_id": "user123", "username": "testuser"}
        mock_redis.get.return_value = json.dumps(token_data)
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get_access_token("token123")
        
        assert result == token_data
    
    @pytest.mark.asyncio
    async def test_delete_access_token(self, cache_manager, mock_redis):
        """测试删除访问令牌"""
        cache_manager._redis = mock_redis
        
        await cache_manager.delete_access_token("token123")
        
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_refresh_token(self, cache_manager, mock_redis):
        """测试设置刷新令牌"""
        token_data = {"user_id": "user123"}
        cache_manager._redis = mock_redis
        
        await cache_manager.set_refresh_token("refresh123", token_data, ttl=604800)
        
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_refresh_token(self, cache_manager, mock_redis):
        """测试获取刷新令牌"""
        token_data = {"user_id": "user123"}
        mock_redis.get.return_value = json.dumps(token_data)
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get_refresh_token("refresh123")
        
        assert result == token_data
    
    @pytest.mark.asyncio
    async def test_delete_refresh_token(self, cache_manager, mock_redis):
        """测试删除刷新令牌"""
        cache_manager._redis = mock_redis
        
        await cache_manager.delete_refresh_token("refresh123")
        
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_user_token(self, cache_manager, mock_redis):
        """测试添加用户令牌"""
        cache_manager._redis = mock_redis
        
        await cache_manager.add_user_token("user123", "access", "token123")
        
        mock_redis.sadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_tokens(self, cache_manager, mock_redis):
        """测试获取用户令牌列表"""
        mock_redis.smembers.return_value = {"token1", "token2"}
        cache_manager._redis = mock_redis
        
        result = await cache_manager.get_user_tokens("user123", "access")
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_delete_user_tokens(self, cache_manager, mock_redis):
        """测试删除用户所有令牌"""
        cache_manager._redis = mock_redis
        
        await cache_manager.delete_user_tokens("user123", "access")
        
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_client(self, cache_manager, mock_redis):
        """测试获取Redis客户端"""
        cache_manager._redis = mock_redis
        
        client = await cache_manager.get_client()
        
        assert client == mock_redis
    
    @pytest.mark.asyncio
    async def test_get_client_auto_connect(self, cache_manager, mock_redis):
        """测试获取Redis客户端（自动连接）"""
        with patch.object(cache_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = None
            cache_manager._redis = mock_redis
            
            client = await cache_manager.get_client()
            
            assert client == mock_redis
