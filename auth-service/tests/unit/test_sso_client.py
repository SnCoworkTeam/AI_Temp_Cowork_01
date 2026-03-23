"""
SSO客户端测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import httpx

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestSSOClient:
    """SSO客户端测试"""
    
    @pytest.fixture
    def mock_settings(self):
        """模拟设置"""
        settings = MagicMock()
        settings.SSO_CLIENT_ID = "test_client_id"
        settings.SSO_CLIENT_SECRET = "test_client_secret"
        settings.SSO_AUTHORIZATION_URL = "https://sso.example.com/auth"
        settings.SSO_TOKEN_URL = "https://sso.example.com/token"
        settings.SSO_USERINFO_URL = "https://sso.example.com/userinfo"
        settings.SSO_REDIRECT_URI = "https://app.example.com/callback"
        settings.SSO_SCOPES = ["openid", "profile", "email"]
        return settings
    
    @pytest.fixture
    def sso_client(self, mock_settings):
        """创建SSOClient实例"""
        with patch('src.sso.sso_client.settings', mock_settings):
            from src.sso.sso_client import SSOClient
            return SSOClient()
    
    def test_sso_client_initialization(self, sso_client, mock_settings):
        """测试SSOClient初始化"""
        assert sso_client is not None
        assert sso_client.client_id == mock_settings.SSO_CLIENT_ID
        assert sso_client.client_secret == mock_settings.SSO_CLIENT_SECRET
        assert sso_client.authorization_url == mock_settings.SSO_AUTHORIZATION_URL
        assert sso_client.token_url == mock_settings.SSO_TOKEN_URL
        assert sso_client.userinfo_url == mock_settings.SSO_USERINFO_URL
        assert sso_client.redirect_uri == mock_settings.SSO_REDIRECT_URI
        assert sso_client.scopes == mock_settings.SSO_SCOPES
    
    def test_get_authorization_url(self, sso_client):
        """测试获取授权URL"""
        state = "test_state_123"
        url = sso_client.get_authorization_url(state)
        
        assert url is not None
        assert isinstance(url, str)
        assert state in url
        assert "client_id" in url
        assert "redirect_uri" in url
        assert "scope" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, sso_client):
        """测试使用授权码交换令牌成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "expires_in": 3600,
            "token_type": "bearer"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await sso_client.exchange_code_for_tokens("test_code")
            
            assert result is not None
            assert "access_token" in result
            assert result["access_token"] == "access_token_123"
            mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_http_error(self, sso_client):
        """测试使用授权码交换令牌（HTTP错误）"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(httpx.HTTPStatusError):
                await sso_client.exchange_code_for_tokens("invalid_code")
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_exception(self, sso_client):
        """测试使用授权码交换令牌（异常）"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception):
                await sso_client.exchange_code_for_tokens("test_code")
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self, sso_client):
        """测试获取用户信息成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "name": "Test User"
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await sso_client.get_user_info("access_token_123")
            
            assert result is not None
            assert "sub" in result
            assert result["sub"] == "user123"
            mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_info_http_error(self, sso_client):
        """测试获取用户信息（HTTP错误）"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(httpx.HTTPStatusError):
                await sso_client.get_user_info("invalid_token")
    
    @pytest.mark.asyncio
    async def test_get_user_info_exception(self, sso_client):
        """测试获取用户信息（异常）"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception):
                await sso_client.get_user_info("access_token_123")
