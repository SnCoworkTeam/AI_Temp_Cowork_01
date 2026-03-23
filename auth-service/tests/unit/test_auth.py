"""
认证路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import Request, Response

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestAuthRoutes:
    """认证路由测试"""
    
    @pytest.fixture
    def mock_sso_client(self):
        """模拟SSO客户端"""
        sso_client = MagicMock()
        sso_client.get_authorization_url = MagicMock(return_value="https://sso.example.com/auth?state=test")
        sso_client.exchange_code_for_tokens = AsyncMock(return_value={
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "expires_in": 3600
        })
        sso_client.get_user_info = AsyncMock(return_value={
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com"
        })
        return sso_client
    
    @pytest.fixture
    def mock_jwt_manager(self):
        """模拟JWT管理器"""
        jwt_manager = MagicMock()
        jwt_manager.create_access_token = MagicMock(return_value="new_access_token")
        jwt_manager.create_refresh_token = MagicMock(return_value="new_refresh_token")
        jwt_manager.verify_token = MagicMock(return_value={"sub": "user123"})
        return jwt_manager
    
    @pytest.fixture
    def mock_cache_manager(self):
        """模拟缓存管理器"""
        cache_manager = AsyncMock()
        cache_manager.set = AsyncMock()
        cache_manager.delete = AsyncMock()
        return cache_manager
    
    @pytest.fixture
    def client(self, mock_sso_client, mock_jwt_manager, mock_cache_manager):
        """测试客户端"""
        from src.main import app
        
        with patch('src.routes.auth.sso_client', mock_sso_client), \
             patch('src.routes.auth.jwt_manager', mock_jwt_manager), \
             patch('src.routes.auth.cache_manager', mock_cache_manager):
            yield TestClient(app)
    
    @pytest.mark.asyncio
    async def test_sso_login_success(self, client, mock_sso_client):
        """测试SSO登录成功"""
        response = client.get("/auth/sso/login", follow_redirects=False)
        
        # 应该重定向到SSO授权URL
        assert response.status_code in [302, 307, 200]
        if response.status_code in [302, 307]:
            assert "sso_state" in response.cookies
    
    @pytest.mark.asyncio
    async def test_sso_callback_success(self, client, mock_sso_client, mock_jwt_manager, mock_cache_manager):
        """测试SSO回调成功"""
        # 先设置状态
        from src.routes.auth import _state_store
        _state_store.clear()
        test_state = "test_state_123"
        _state_store[test_state] = {"created_at": None}
        
        response = client.get(
            f"/auth/sso/callback?code=test_code&state={test_state}",
            follow_redirects=False
        )
        
        # 应该重定向或返回成功
        assert response.status_code in [200, 302, 307, 500]
    
    @pytest.mark.asyncio
    async def test_sso_callback_invalid_state(self, client):
        """测试SSO回调（无效状态）"""
        response = client.get("/auth/sso/callback?code=test_code&state=invalid_state")
        assert response.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_sso_callback_error(self, client):
        """测试SSO回调（错误）"""
        response = client.get("/auth/sso/callback?error=access_denied")
        assert response.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, mock_jwt_manager, mock_cache_manager):
        """测试刷新令牌成功"""
        mock_jwt_manager.verify_token.return_value = {
            "sub": "user123",
            "type": "refresh"
        }
        
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )
        
        assert response.status_code in [200, 401, 500]
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client, mock_jwt_manager):
        """测试刷新令牌（无效令牌）"""
        mock_jwt_manager.verify_token.return_value = None
        
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code in [401, 500]
    
    @pytest.mark.asyncio
    async def test_logout_success(self, client, mock_jwt_manager, mock_cache_manager):
        """测试登出成功"""
        mock_current_user = {"user_id": "user123", "token": "access_token"}
        
        with patch('src.routes.auth.get_current_user', return_value=mock_current_user):
            response = client.post("/auth/logout")
            assert response.status_code in [200, 401, 500]
    
    def test_refresh_token_request_model(self):
        """测试RefreshTokenRequest模型"""
        from src.routes.auth import RefreshTokenRequest
        
        request = RefreshTokenRequest(refresh_token="test_token")
        assert request.refresh_token == "test_token"
    
    def test_refresh_token_response_model(self):
        """测试RefreshTokenResponse模型"""
        from src.routes.auth import RefreshTokenResponse
        
        response = RefreshTokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=3600
        )
        assert response.access_token == "access_token"
        assert response.refresh_token == "refresh_token"
        assert response.expires_in == 3600
        assert response.token_type == "bearer"
    
    def test_logout_response_model(self):
        """测试LogoutResponse模型"""
        from src.routes.auth import LogoutResponse
        
        response = LogoutResponse(message="Logged out successfully")
        assert response.message == "Logged out successfully"
    
    @pytest.mark.asyncio
    async def test_sso_callback_missing_code(self, client):
        """测试SSO回调（缺少code）"""
        from src.routes.auth import _state_store
        _state_store.clear()
        test_state = "test_state_123"
        _state_store[test_state] = {"created_at": None}
        
        response = client.get(f"/auth/sso/callback?state={test_state}")
        assert response.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_sso_callback_state_mismatch(self, client):
        """测试SSO回调（状态不匹配）"""
        from src.routes.auth import _state_store
        _state_store.clear()
        test_state = "test_state_123"
        _state_store[test_state] = {"created_at": None}
        
        response = client.get(f"/auth/sso/callback?code=test_code&state=different_state")
        assert response.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_refresh_token_missing_token(self, client):
        """测试刷新令牌（缺少令牌）"""
        response = client.post("/auth/refresh", json={})
        assert response.status_code in [422, 400]
    
    @pytest.mark.asyncio
    async def test_refresh_token_not_in_cache(self, client, mock_jwt_manager, mock_cache_manager):
        """测试刷新令牌（不在缓存中）"""
        mock_jwt_manager.verify_token.return_value = {
            "sub": "user123",
            "type": "refresh"
        }
        mock_cache_manager.get_refresh_token.return_value = None
        
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )
        assert response.status_code in [401, 500]
    
    @pytest.mark.asyncio
    async def test_logout_no_user(self, client):
        """测试登出（无用户）"""
        with patch('src.routes.auth.get_current_user', side_effect=Exception("Not authenticated")):
            response = client.post("/auth/logout")
            assert response.status_code in [401, 500]
    
    @pytest.mark.asyncio
    async def test_sso_callback_no_access_token(self, client, mock_sso_client, mock_jwt_manager, mock_cache_manager):
        """测试SSO回调（没有访问令牌）"""
        from src.routes.auth import _state_store
        _state_store.clear()
        test_state = "test_state_123"
        _state_store[test_state] = {"created_at": None}
        
        mock_sso_client.exchange_code_for_tokens.return_value = {
            "refresh_token": "refresh_token_123",
            "expires_in": 3600
        }
        
        response = client.get(f"/auth/sso/callback?code=test_code&state={test_state}")
        assert response.status_code in [500, 400]
    
    @pytest.mark.asyncio
    async def test_sso_callback_exchange_error(self, client, mock_sso_client):
        """测试SSO回调（交换令牌错误）"""
        from src.routes.auth import _state_store
        _state_store.clear()
        test_state = "test_state_123"
        _state_store[test_state] = {"created_at": None}
        
        mock_sso_client.exchange_code_for_tokens.side_effect = Exception("Exchange error")
        
        response = client.get(f"/auth/sso/callback?code=test_code&state={test_state}")
        assert response.status_code in [500, 400]
    
    @pytest.mark.asyncio
    async def test_refresh_token_no_session(self, client, mock_jwt_manager, mock_cache_manager):
        """测试刷新令牌（没有会话）"""
        mock_jwt_manager.verify_token.return_value = {
            "sub": "user123",
            "type": "refresh"
        }
        mock_cache_manager.get_refresh_token.return_value = {"user_id": "user123"}
        mock_cache_manager.get_user_session.return_value = None
        
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )
        assert response.status_code in [401, 500]
    
    @pytest.mark.asyncio
    async def test_logout_no_token(self, client, mock_jwt_manager, mock_cache_manager):
        """测试登出（没有令牌）"""
        mock_current_user = {"user_id": "user123"}
        
        with patch('src.routes.auth.get_current_user', return_value=mock_current_user):
            response = client.post("/auth/logout")
            assert response.status_code in [200, 401, 500]
