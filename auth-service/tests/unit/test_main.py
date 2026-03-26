"""
主应用测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestMain:
    """主应用测试"""
    
    @pytest.fixture
    def mock_cache_manager(self):
        """模拟缓存管理器"""
        cache_manager = AsyncMock()
        cache_manager.connect = AsyncMock()
        cache_manager.disconnect = AsyncMock()
        return cache_manager
    
    @pytest.fixture
    def mock_init_database(self):
        """模拟数据库初始化"""
        return MagicMock(return_value=True)
    
    @pytest.fixture
    def mock_close_database(self):
        """模拟数据库关闭"""
        return MagicMock()
    
    @pytest.fixture
    def client(self, mock_cache_manager, mock_init_database, mock_close_database):
        """测试客户端"""
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.init_database', mock_init_database), \
             patch('src.main.close_database', mock_close_database):
            from src.main import app
            yield TestClient(app)
    
    def test_root_endpoint(self, client):
        """测试根路径端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth-service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_global_exception_handler(self, client):
        """测试全局异常处理"""
        # 创建一个会抛出异常的路由来测试异常处理
        # 由于我们无法直接触发未处理的异常，这里只测试异常处理器的存在
        from src.main import app
        assert app.exception_handlers.get(Exception) is not None
    
    def test_cors_middleware(self, client):
        """测试CORS中间件"""
        # 发送OPTIONS请求测试CORS
        response = client.options("/")
        # CORS中间件应该处理OPTIONS请求
        assert response.status_code in [200, 405]
    
    def test_request_logging_middleware(self, client):
        """测试请求日志中间件"""
        response = client.get("/")
        # 中间件应该记录请求，但不影响响应
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_lifespan_startup(self, mock_cache_manager, mock_init_database):
        """测试应用启动生命周期"""
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.init_database', mock_init_database):
            from src.main import lifespan, app
            
            # 模拟启动
            async with lifespan(app):
                mock_init_database.assert_called_once()
                mock_cache_manager.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_database_failure(self, mock_cache_manager):
        """测试应用启动生命周期（数据库初始化失败）"""
        mock_init_database = MagicMock(return_value=False)
        
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.init_database', mock_init_database):
            from src.main import lifespan, app
            
            # 即使数据库初始化失败，应用也应该启动
            async with lifespan(app):
                mock_init_database.assert_called_once()
                mock_cache_manager.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_cache_failure(self, mock_init_database):
        """测试应用启动生命周期（缓存连接失败）"""
        mock_cache_manager = AsyncMock()
        mock_cache_manager.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.init_database', mock_init_database):
            from src.main import lifespan, app
            
            # 即使缓存连接失败，应用也应该启动
            async with lifespan(app):
                mock_init_database.assert_called_once()
                mock_cache_manager.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown(self, mock_cache_manager, mock_close_database):
        """测试应用关闭生命周期"""
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.close_database', mock_close_database), \
             patch('src.main.init_database', MagicMock(return_value=True)):
            from src.main import lifespan, app
            
            # 模拟关闭
            async with lifespan(app):
                pass  # 进入关闭阶段
            
            mock_cache_manager.disconnect.assert_called_once()
            mock_close_database.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown_cache_failure(self, mock_close_database):
        """测试应用关闭生命周期（缓存断开失败）"""
        mock_cache_manager = AsyncMock()
        mock_cache_manager.connect = AsyncMock()
        mock_cache_manager.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))
        
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.close_database', mock_close_database), \
             patch('src.main.init_database', MagicMock(return_value=True)):
            from src.main import lifespan, app
            
            # 即使缓存断开失败，应用也应该正常关闭
            async with lifespan(app):
                pass  # 进入关闭阶段
            
            mock_cache_manager.disconnect.assert_called_once()
            mock_close_database.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown_database_failure(self, mock_cache_manager):
        """测试应用关闭生命周期（数据库关闭失败）"""
        mock_close_database = MagicMock(side_effect=Exception("Close failed"))
        
        with patch('src.main.cache_manager', mock_cache_manager), \
             patch('src.main.close_database', mock_close_database), \
             patch('src.main.init_database', MagicMock(return_value=True)):
            from src.main import lifespan, app
            
            # 即使数据库关闭失败，应用也应该正常关闭
            async with lifespan(app):
                pass  # 进入关闭阶段
            
            mock_cache_manager.disconnect.assert_called_once()
            mock_close_database.assert_called_once()
    
    def test_app_has_routers(self, client):
        """测试应用已注册路由"""
        from src.main import app
        
        # 检查主要路由是否已注册
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes or any("/health" in r for r in routes)
    
    def test_app_cors_config(self):
        """测试CORS配置"""
        from src.main import app
        
        # 检查CORS中间件是否存在
        middleware_types = [type(middleware).__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in str(middleware_types)
    
    @pytest.mark.asyncio
    async def test_log_and_monitor_requests(self, client):
        """测试请求日志和监控中间件"""
        from src.main import log_and_monitor_requests
        from fastapi import Request
        from unittest.mock import AsyncMock
        
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await log_and_monitor_requests(mock_request, mock_call_next)
        
        assert response == mock_response
        mock_call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_and_monitor_requests_error(self, client):
        """测试请求日志和监控中间件（错误响应）"""
        from src.main import log_and_monitor_requests
        from fastapi import Request
        from unittest.mock import AsyncMock
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/test"
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await log_and_monitor_requests(mock_request, mock_call_next)
        
        assert response == mock_response
        assert response.status_code == 500
    
    def test_global_exception_handler_with_exception(self, client):
        """测试全局异常处理器（实际异常）"""
        from src.main import app, global_exception_handler
        from fastapi import Request
        from unittest.mock import MagicMock
        
        mock_request = MagicMock(spec=Request)
        test_exception = Exception("Test exception")
        
        with patch('src.main.logger') as mock_logger:
            response = global_exception_handler(mock_request, test_exception)
            
            # 应该返回错误响应
            assert response is not None
            mock_logger.error.assert_called_once()
    
    def test_app_includes_all_routers(self):
        """测试应用包含所有路由"""
        from src.main import app
        
        routes = [route.path for route in app.routes]
        
        # 检查主要路由是否存在
        assert "/" in routes
        assert any("/health" in r for r in routes)
        assert any("/auth" in r for r in routes)
        assert any("/users" in r for r in routes)
        assert any("/monitoring" in r for r in routes)

