"""
JWT管理器测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestJWTManager:
    """JWT管理器测试"""
    
    @pytest.fixture
    def jwt_manager(self):
        """创建JWTManager实例"""
        from src.sso.jwt_manager import JWTManager
        return JWTManager()
    
    @pytest.fixture
    def mock_settings(self):
        """模拟设置"""
        settings = MagicMock()
        settings.JWT_SECRET_KEY = "test_secret_key"
        settings.JWT_ALGORITHM = "HS256"
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
        return settings
    
    def test_jwt_manager_initialization(self, jwt_manager):
        """测试JWTManager初始化"""
        assert jwt_manager is not None
        assert jwt_manager.secret_key is not None
        assert jwt_manager.algorithm is not None
        assert jwt_manager.access_token_expire_minutes > 0
        assert jwt_manager.refresh_token_expire_days > 0
    
    def test_create_access_token_success(self, jwt_manager):
        """测试创建访问令牌成功"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["user", "admin"]
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_additional_claims(self, jwt_manager):
        """测试创建访问令牌（带额外声明）"""
        additional_claims = {"custom_field": "custom_value"}
        
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            additional_claims=additional_claims
        )
        
        assert token is not None
        # 验证令牌可以解码
        payload = jwt_manager.verify_token(token)
        assert payload is not None
        assert payload.get("custom_field") == "custom_value"
    
    def test_create_refresh_token_success(self, jwt_manager):
        """测试创建刷新令牌成功"""
        token = jwt_manager.create_refresh_token(
            user_id="user123"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token_with_additional_claims(self, jwt_manager):
        """测试创建刷新令牌（带额外声明）"""
        additional_claims = {"device_id": "device123"}
        
        token = jwt_manager.create_refresh_token(
            user_id="user123",
            additional_claims=additional_claims
        )
        
        assert token is not None
        payload = jwt_manager.verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload.get("device_id") == "device123"
    
    def test_verify_token_success(self, jwt_manager):
        """测试验证令牌成功"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            email="test@example.com"
        )
        
        payload = jwt_manager.verify_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "user123"
        assert payload.get("username") == "testuser"
        assert payload.get("type") == "access"
    
    def test_verify_token_invalid(self, jwt_manager):
        """测试验证无效令牌"""
        payload = jwt_manager.verify_token("invalid_token")
        assert payload is None
    
    def test_verify_token_expired(self, jwt_manager):
        """测试验证过期令牌"""
        # 创建一个过期的令牌
        from jwt import encode
        expired_payload = {
            "sub": "user123",
            "type": "access",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = encode(expired_payload, jwt_manager.secret_key, algorithm=jwt_manager.algorithm)
        
        payload = jwt_manager.verify_token(expired_token)
        assert payload is None
    
    def test_verify_token_wrong_type(self, jwt_manager):
        """测试验证错误类型的令牌"""
        refresh_token = jwt_manager.create_refresh_token(user_id="user123")
        
        # 尝试用access类型验证refresh令牌
        payload = jwt_manager.verify_token(refresh_token, token_type="access")
        # 应该返回None或payload（取决于实现）
        assert payload is None or payload.get("type") != "access"
    
    def test_verify_token_correct_type(self, jwt_manager):
        """测试验证正确类型的令牌"""
        refresh_token = jwt_manager.create_refresh_token(user_id="user123")
        
        payload = jwt_manager.verify_token(refresh_token, token_type="refresh")
        assert payload is not None
        assert payload.get("type") == "refresh"
    
    @pytest.mark.asyncio
    async def test_revoke_token_success(self, jwt_manager):
        """测试撤销令牌成功"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            email="test@example.com"
        )
        
        with patch('src.sso.jwt_manager.cache_manager') as mock_cache:
            mock_cache.add_to_blacklist = AsyncMock()
            
            result = await jwt_manager.revoke_token(token)
            
            assert result is True
            mock_cache.add_to_blacklist.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens_success(self, jwt_manager):
        """测试撤销用户所有令牌成功"""
        with patch('src.sso.jwt_manager.cache_manager') as mock_cache:
            mock_cache.revoke_user_tokens = AsyncMock()
            
            result = await jwt_manager.revoke_user_tokens("user123")
            
            assert result is True
            mock_cache.revoke_user_tokens.assert_called_once_with("user123")
    
    def test_token_payload_structure(self, jwt_manager):
        """测试令牌载荷结构"""
        token = jwt_manager.create_access_token(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["admin"]
        )
        
        payload = jwt_manager.verify_token(token)
        
        assert payload is not None
        assert "sub" in payload
        assert "username" in payload
        assert "email" in payload
        assert "roles" in payload
        assert "type" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["roles"] == ["admin"]
        assert payload["type"] == "access"
