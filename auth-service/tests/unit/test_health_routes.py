"""
健康检查路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestHealthRoutes:
    """健康检查路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-service"
        assert "version" in data
    
    def test_readiness_check(self, client):
        """测试就绪检查端点"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_liveness_check(self, client):
        """测试存活检查端点"""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

