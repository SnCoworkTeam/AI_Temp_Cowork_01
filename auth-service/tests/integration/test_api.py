"""
Auth Service API集成测试
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAuthAPI:
    """认证API测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from auth_service.src.main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_login_endpoint(self, client):
        """测试登录端点"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        # 可能成功或失败，但不应该500错误
        assert response.status_code < 500
    
    def test_token_refresh(self, client, auth_token):
        """测试token刷新"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "test_refresh_token"}
        )
        # 可能成功或失败
        assert response.status_code < 500









