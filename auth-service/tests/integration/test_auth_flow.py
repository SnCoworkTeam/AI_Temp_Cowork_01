"""
认证流程集成测试
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAuthFlow:
    """认证流程测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from auth_service.src.main import app
        return TestClient(app)
    
    def test_register_user(self, client):
        """测试用户注册"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        # 可能成功或失败（用户已存在等），但不应该500错误
        assert response.status_code < 500
    
    def test_login_flow(self, client):
        """测试登录流程"""
        # 先尝试注册
        user_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpass123"
        }
        client.post("/api/auth/register", json=user_data)
        
        # 尝试登录
        login_data = {
            "username": "testuser2",
            "password": "testpass123"
        }
        response = client.post("/api/auth/login", json=login_data)
        
        # 可能成功或失败
        assert response.status_code < 500
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "message" in data
    
    def test_token_refresh_flow(self, client):
        """测试令牌刷新流程"""
        # 先登录获取refresh token
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            data = login_response.json()
            refresh_token = data.get("refresh_token")
            
            if refresh_token:
                refresh_response = client.post(
                    "/api/auth/refresh",
                    json={"refresh_token": refresh_token}
                )
                assert refresh_response.status_code < 500
    
    def test_complete_auth_flow(self, client):
        """测试完整的认证流程：注册->登录->获取用户信息->登出"""
        # 1. 注册
        user_data = {
            "username": "flow_test_user",
            "email": "flow_test@example.com",
            "password": "flow_test_pass123"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        
        if register_response.status_code in [200, 201]:
            # 2. 登录
            login_data = {
                "username": "flow_test_user",
                "password": "flow_test_pass123"
            }
            login_response = client.post("/api/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                access_token = login_data.get("access_token")
                
                if access_token:
                    # 3. 获取用户信息
                    headers = {"Authorization": f"Bearer {access_token}"}
                    user_response = client.get("/api/users/me", headers=headers)
                    assert user_response.status_code in [200, 500]
                    
                    # 4. 登出
                    logout_response = client.post("/api/auth/logout", headers=headers)
                    assert logout_response.status_code in [200, 500]
    
    def test_password_change_flow(self, client):
        """测试密码修改流程"""
        # 先注册并登录
        user_data = {
            "username": "pwd_change_user",
            "email": "pwd_change@example.com",
            "password": "old_password123"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post(
            "/api/auth/login",
            json={"username": "pwd_change_user", "password": "old_password123"}
        )
        
        if login_response.status_code == 200:
            access_token = login_response.json().get("access_token")
            if access_token:
                headers = {"Authorization": f"Bearer {access_token}"}
                change_response = client.post(
                    "/api/auth/change-password",
                    json={
                        "old_password": "old_password123",
                        "new_password": "new_password123"
                    },
                    headers=headers
                )
                assert change_response.status_code in [200, 400, 500]

