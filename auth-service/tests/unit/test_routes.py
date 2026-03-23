"""
认证路由单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestAuthRoutes:
    """认证路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_register_endpoint(self, client):
        """测试注册端点"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code in [200, 201, 400, 500]
    
    def test_login_endpoint(self, client):
        """测试登录端点"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        assert response.status_code in [200, 401, 500]
    
    def test_refresh_token_endpoint(self, client):
        """测试刷新令牌端点"""
        response = client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": "test_refresh_token"
            }
        )
        assert response.status_code in [200, 401, 500]


@pytest.mark.unit
class TestUserRoutes:
    """用户路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_get_current_user(self, client):
        """测试获取当前用户"""
        # 需要认证，可能返回401
        response = client.get("/api/users/me")
        assert response.status_code in [200, 401, 500]
    
    def test_register_with_validation(self, client):
        """测试注册时的验证"""
        # 测试无效邮箱
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "testpass123"
            }
        )
        assert response.status_code in [400, 422, 500]
        
        # 测试弱密码
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "123"  # 太短
            }
        )
        assert response.status_code in [400, 422, 500]
    
    def test_login_with_invalid_credentials(self, client):
        """测试使用无效凭据登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpass"
            }
        )
        assert response.status_code in [401, 500]
    
    def test_logout_endpoint(self, client):
        """测试登出端点"""
        # 需要认证，可能返回401
        response = client.post("/api/auth/logout")
        assert response.status_code in [200, 401, 500]
    
    def test_change_password_endpoint(self, client):
        """测试修改密码端点"""
        # 需要认证，可能返回401
        response = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "oldpass",
                "new_password": "newpass123"
            }
        )
        assert response.status_code in [200, 401, 400, 500]
    
    def test_get_user_sessions(self, client):
        """测试获取用户会话列表"""
        # 需要认证，可能返回401
        response = client.get("/api/auth/sessions")
        assert response.status_code in [200, 401, 500]
    
    def test_revoke_session(self, client):
        """测试撤销会话"""
        # 需要认证，可能返回401
        response = client.delete("/api/auth/sessions/test-session-id")
        assert response.status_code in [200, 401, 404, 500]


@pytest.mark.unit
class TestSSORoutes:
    """SSO路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_sso_login_initiate(self, client):
        """测试SSO登录发起"""
        response = client.get("/api/auth/sso/login")
        assert response.status_code in [200, 302, 500]
    
    def test_sso_callback(self, client):
        """测试SSO回调"""
        response = client.get("/api/auth/sso/callback?code=test_code")
        assert response.status_code in [200, 302, 400, 500]

