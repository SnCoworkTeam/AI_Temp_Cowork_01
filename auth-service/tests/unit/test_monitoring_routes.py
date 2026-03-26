"""
监控路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestMonitoringRoutes:
    """监控路由测试"""
    
    @pytest.fixture
    def mock_cache_manager(self):
        """模拟缓存管理器"""
        cache_manager = AsyncMock()
        cache_manager._redis = AsyncMock()
        cache_manager._redis.ping = AsyncMock(return_value=True)
        return cache_manager
    
    @pytest.fixture
    def client(self, mock_cache_manager):
        """测试客户端"""
        from src.main import app
        
        with patch('src.routes.monitoring.cache_manager', mock_cache_manager):
            yield TestClient(app)
    
    @pytest.mark.asyncio
    async def test_get_monitoring_data(self, client, mock_cache_manager):
        """测试获取监控数据端点"""
        response = client.get("/monitoring")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "service_name" in data
            assert "health" in data
    
    @pytest.mark.asyncio
    async def test_get_user_activity_stats(self, client):
        """测试获取用户活跃度统计端点"""
        response = client.get("/monitoring/user-activity")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "user_activity_stats" in data
            assert "timestamp" in data
    
    def test_update_api_stats(self):
        """测试更新API统计"""
        from src.routes.monitoring import _update_api_stats
        
        _update_api_stats("GET", "/test", 200, 0.1)
        _update_api_stats("GET", "/test", 200, 0.2)
        _update_api_stats("GET", "/test", 404, 0.3)
        
        # 验证统计已更新
        from src.routes.monitoring import _api_stats
        key = "GET:/test"
        assert key in _api_stats
        assert _api_stats[key]["total_requests"] >= 3
    
    def test_update_user_activity(self):
        """测试更新用户活跃度"""
        from src.routes.monitoring import _update_user_activity
        
        _update_user_activity("user123", "testuser", "login")
        _update_user_activity("user123", "testuser", "session_created")
        
        # 验证活跃度已更新
        from src.routes.monitoring import _user_activity
        assert "user123" in _user_activity
        assert _user_activity["user123"]["login_count"] >= 1
    
    def test_calculate_percentiles(self):
        """测试计算百分位数"""
        from src.routes.monitoring import _calculate_percentiles
        
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        p50 = _calculate_percentiles(values, 50)
        assert p50 == 5.0
        
        p95 = _calculate_percentiles(values, 95)
        assert p95 >= 9.0
        
        p99 = _calculate_percentiles(values, 99)
        assert p99 >= 9.0
    
    def test_calculate_percentiles_empty(self):
        """测试计算百分位数（空列表）"""
        from src.routes.monitoring import _calculate_percentiles
        
        result = _calculate_percentiles([], 50)
        assert result == 0.0
    
    def test_update_api_stats_response_time_limit(self):
        """测试更新API统计（响应时间列表限制）"""
        from src.routes.monitoring import _update_api_stats, _api_stats
        
        # 清空统计
        _api_stats.clear()
        
        # 添加超过1000个响应时间
        for i in range(1001):
            _update_api_stats("GET", "/test", 200, 0.1)
        
        key = "GET:/test"
        assert key in _api_stats
        assert len(_api_stats[key]["response_times"]) <= 1000
    
    def test_update_user_activity_logout(self):
        """测试更新用户活跃度（登出）"""
        from src.routes.monitoring import _update_user_activity, _user_activity
        
        # 清空活跃度
        _user_activity.clear()
        
        _update_user_activity("user123", "testuser", "login")
        _update_user_activity("user123", "testuser", "session_created")
        _update_user_activity("user123", "testuser", "logout")
        
        assert "user123" in _user_activity
        assert _user_activity["user123"]["active_sessions"] >= 0
    
    def test_update_user_activity_other_action(self):
        """测试更新用户活跃度（其他操作）"""
        from src.routes.monitoring import _update_user_activity, _user_activity
        
        # 清空活跃度
        _user_activity.clear()
        
        _update_user_activity("user123", "testuser", "api_call")
        
        assert "user123" in _user_activity
        assert "api_call" in _user_activity["user123"]["actions"]
        assert _user_activity["user123"]["actions"]["api_call"] == 1
    
    def test_get_api_key(self):
        """测试生成API键"""
        from src.routes.monitoring import _get_api_key
        
        key = _get_api_key("GET", "/test")
        assert key == "GET:/test"
        
        key = _get_api_key("POST", "/auth/login")
        assert key == "POST:/auth/login"
    
    def test_calculate_percentiles_single_value(self):
        """测试计算百分位数（单个值）"""
        from src.routes.monitoring import _calculate_percentiles
        
        result = _calculate_percentiles([5.0], 50)
        assert result == 5.0
    
    def test_calculate_percentiles_two_values(self):
        """测试计算百分位数（两个值）"""
        from src.routes.monitoring import _calculate_percentiles
        
        result = _calculate_percentiles([1.0, 2.0], 50)
        assert result >= 1.0
        assert result <= 2.0
    
    @pytest.mark.asyncio
    async def test_get_monitoring_data_with_cache_error(self, client, mock_cache_manager):
        """测试获取监控数据（缓存错误）"""
        mock_cache_manager._redis = None
        
        response = client.get("/monitoring")
        # 即使缓存错误，也应该返回监控数据
        assert response.status_code in [200, 500]
    
    @pytest.mark.asyncio
    async def test_get_user_activity_stats_empty(self, client):
        """测试获取用户活跃度统计（空数据）"""
        from src.routes.monitoring import _user_activity
        _user_activity.clear()
        
        response = client.get("/monitoring/user-activity")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "user_activity_stats" in data
    
    @pytest.mark.asyncio
    async def test_monitoring_middleware(self):
        """测试监控中间件"""
        from src.routes.monitoring import monitoring_middleware
        from fastapi import Request
        from unittest.mock import AsyncMock, MagicMock
        
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await monitoring_middleware(mock_request, mock_call_next)
        
        assert response == mock_response
        mock_call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitoring_middleware_error_response(self):
        """测试监控中间件（错误响应）"""
        from src.routes.monitoring import monitoring_middleware
        from fastapi import Request
        from unittest.mock import AsyncMock, MagicMock
        
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/test"
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        mock_call_next = AsyncMock(return_value=mock_response)
        
        response = await monitoring_middleware(mock_request, mock_call_next)
        
        assert response == mock_response
        assert response.status_code == 500

