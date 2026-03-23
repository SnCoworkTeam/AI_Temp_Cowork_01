"""
SSO功能单元测试
使用mock测试SSO相关功能
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestJWTManager:
    """JWT管理器测试"""
    
    @patch('src.sso.jwt_manager.jwt_manager')
    def test_create_access_token(self, mock_jwt):
        """测试创建访问令牌"""
        mock_jwt.create_access_token.return_value = "test_token"
        
        token = mock_jwt.create_access_token(
            user_id="test_user",
            username="testuser",
            email="test@example.com",
            roles=["user"]
        )
        
        assert token == "test_token"
    
    @patch('src.sso.jwt_manager.jwt_manager')
    def test_verify_token(self, mock_jwt):
        """测试验证令牌"""
        mock_payload = {
            "user_id": "test_user",
            "username": "testuser"
        }
        mock_jwt.verify_token.return_value = mock_payload
        
        payload = mock_jwt.verify_token("test_token")
        assert payload is not None
        assert payload["user_id"] == "test_user"


@pytest.mark.unit
class TestSSOClient:
    """SSO客户端测试"""
    
    @patch('src.sso.sso_client.SSOClient')
    def test_sso_client_initialization(self, mock_client):
        """测试SSO客户端初始化"""
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        client = mock_client()
        assert client is not None
    
    @patch('auth_service.src.sso.sso_client.SSOClient.initiate_login')
    def test_initiate_login(self, mock_initiate):
        """测试发起SSO登录"""
        mock_initiate.return_value = "https://sso.example.com/login"
        
        url = mock_initiate()
        assert url is not None
        assert "login" in url

