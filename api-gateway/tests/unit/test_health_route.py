"""
健康检查路由单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """创建测试客户端（延迟导入以避免依赖问题）"""
    # 延迟导入以避免在导入时执行main.py的初始化
    from src.main import app
    return TestClient(app)


class TestHealthRoute:
    """健康检查路由测试"""
    
    def test_health_check_success(self, test_client: TestClient):
        """测试健康检查成功"""
        # Mock service_discovery模块
        with patch('src.main.service_discovery') as mock_service:
            mock_service.healthcheck = AsyncMock(return_value=True)
            
            response = test_client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert data["service"] == "api-gateway"
            assert data["status"] in ["healthy", "degraded"]
            assert "registry_connection" in data
    
    def test_health_check_degraded(self, test_client: TestClient):
        """测试健康检查降级状态"""
        with patch('src.main.service_discovery') as mock_service:
            mock_service.healthcheck = AsyncMock(return_value=False)
            
            response = test_client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["registry_connection"] == "disconnected"
    
    def test_health_check_structure(self, test_client: TestClient):
        """测试健康检查响应结构"""
        with patch('src.main.service_discovery') as mock_service:
            mock_service.healthcheck = AsyncMock(return_value=True)
            
            response = test_client.get("/health")
            data = response.json()
            
            # 验证必需字段
            required_fields = ["status", "service", "registry_connection"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # 验证字段类型
            assert isinstance(data["status"], str)
            assert isinstance(data["service"], str)
            assert isinstance(data["registry_connection"], str)




