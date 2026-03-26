"""
中间件测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import HTTPException, status

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestAuthMiddleware:
    """认证中间件测试"""
    
    @pytest.fixture
    def mock_request(self):
        """模拟FastAPI请求"""
        request = MagicMock()
        request.cookies = {}
        request.headers = {}
        request.state = MagicMock()
        return request
    
    @pytest.fixture
    def mock_jwt_manager(self):
        """模拟JWT管理器"""
        jwt_manager = MagicMock()
        jwt_manager.verify_token.return_value = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["user"]
        }
        return jwt_manager
    
    @pytest.fixture
    def mock_cache_manager(self):
        """模拟缓存管理器"""
        cache_manager = AsyncMock()
        cache_manager.get_access_token.return_value = {
            "user_id": "user123",
            "username": "testuser"
        }
        return cache_manager
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_header(self, mock_request, mock_jwt_manager, mock_cache_manager):
        """测试从Authorization头获取用户"""
        from src.middleware.auth_middleware import get_current_user
        
        mock_request.headers = {"authorization": "Bearer test_token"}
        
        with patch('src.middleware.auth_middleware.jwt_manager', mock_jwt_manager), \
             patch('src.middleware.auth_middleware.cache_manager', mock_cache_manager):
            
            # 模拟HTTPBearer
            with patch('src.middleware.auth_middleware.security') as mock_security:
                mock_credentials = MagicMock()
                mock_credentials.credentials = "test_token"
                mock_security.return_value = mock_credentials
                
                user = await get_current_user(mock_request, mock_credentials)
                
                assert user is not None
                assert user["user_id"] == "user123"
                assert user["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_cookie(self, mock_request, mock_jwt_manager, mock_cache_manager):
        """测试从Cookie获取用户"""
        from src.middleware.auth_middleware import get_current_user
        
        mock_request.cookies = {"access_token": "test_token"}
        
        with patch('src.middleware.auth_middleware.jwt_manager', mock_jwt_manager), \
             patch('src.middleware.auth_middleware.cache_manager', mock_cache_manager):
            
            with patch('src.middleware.auth_middleware.security') as mock_security:
                mock_security.return_value = None
                
                user = await get_current_user(mock_request, None)
                
                assert user is not None
                assert user["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, mock_request):
        """测试没有令牌时抛出异常"""
        from src.middleware.auth_middleware import get_current_user
        
        mock_request.cookies = {}
        
        with patch('src.middleware.auth_middleware.security') as mock_security:
            mock_security.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_request):
        """测试无效令牌"""
        from src.middleware.auth_middleware import get_current_user
        
        mock_request.cookies = {"access_token": "invalid_token"}
        
        mock_jwt_manager = MagicMock()
        mock_jwt_manager.verify_token.return_value = None
        
        with patch('src.middleware.auth_middleware.jwt_manager', mock_jwt_manager), \
             patch('src.middleware.auth_middleware.security') as mock_security:
            mock_security.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, None)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_optional_auth_authenticated(self, mock_request):
        """测试可选认证（已认证）"""
        from src.middleware.auth_middleware import optional_auth
        
        with patch('src.middleware.auth_middleware.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"user_id": "user123"}
            
            user = await optional_auth(mock_request)
            assert user is not None
            assert user["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_optional_auth_not_authenticated(self, mock_request):
        """测试可选认证（未认证）"""
        from src.middleware.auth_middleware import optional_auth
        
        with patch('src.middleware.auth_middleware.get_current_user') as mock_get_user:
            mock_get_user.side_effect = HTTPException(status_code=401, detail="Not authenticated")
            
            user = await optional_auth(mock_request)
            assert user is None


@pytest.mark.unit
class TestPermissionMiddleware:
    """权限中间件测试"""
    
    @pytest.fixture
    def mock_user_service(self):
        """模拟用户服务"""
        user_service = AsyncMock()
        user = MagicMock()
        user.permissions = ["perm1", "perm2"]
        user.roles = ["role1"]
        user_service.get_user.return_value = user
        return user_service
    
    @pytest.fixture
    def mock_role_service(self):
        """模拟角色服务"""
        role_service = AsyncMock()
        role = MagicMock()
        role.permissions = ["perm3"]
        role_service.get_role.return_value = role
        return role_service
    
    @pytest.fixture
    def mock_permission_service(self):
        """模拟权限服务"""
        permission_service = AsyncMock()
        permission = MagicMock()
        permission.id = "perm1"
        permission_service.get_permission_by_code.return_value = permission
        return permission_service
    
    @pytest.mark.asyncio
    async def test_check_permission_success(self, mock_user_service, mock_role_service, mock_permission_service):
        """测试权限检查成功"""
        from src.middleware.permission_middleware import check_permission
        
        current_user = {"user_id": "user123"}
        
        with patch('src.middleware.permission_middleware.user_service', mock_user_service), \
             patch('src.middleware.permission_middleware.role_service', mock_role_service), \
             patch('src.middleware.permission_middleware.permission_service', mock_permission_service):
            
            result = await check_permission("test:permission", current_user)
            assert result == current_user
    
    @pytest.mark.asyncio
    async def test_check_permission_no_user(self):
        """测试权限检查（无用户）"""
        from src.middleware.permission_middleware import check_permission
        
        current_user = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await check_permission("test:permission", current_user)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_check_permission_not_found(self, mock_user_service, mock_role_service, mock_permission_service):
        """测试权限检查（权限不存在）"""
        from src.middleware.permission_middleware import check_permission
        
        current_user = {"user_id": "user123"}
        mock_permission_service.get_permission_by_code.return_value = None
        
        with patch('src.middleware.permission_middleware.user_service', mock_user_service), \
             patch('src.middleware.permission_middleware.role_service', mock_role_service), \
             patch('src.middleware.permission_middleware.permission_service', mock_permission_service):
            
            with pytest.raises(HTTPException) as exc_info:
                await check_permission("test:permission", current_user)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_require_admin_success(self, mock_user_service, mock_role_service):
        """测试要求管理员权限（成功）"""
        from src.middleware.permission_middleware import require_admin
        
        current_user = {"user_id": "user123"}
        
        user = MagicMock()
        user.roles = ["admin_role_id"]
        mock_user_service.get_user.return_value = user
        
        role = MagicMock()
        role.code = "admin"
        mock_role_service.get_role.return_value = role
        
        with patch('src.middleware.permission_middleware.user_service', mock_user_service), \
             patch('src.middleware.permission_middleware.role_service', mock_role_service):
            
            result = await require_admin(current_user)
            assert result == current_user
    
    @pytest.mark.asyncio
    async def test_require_admin_failure(self, mock_user_service, mock_role_service):
        """测试要求管理员权限（失败）"""
        from src.middleware.permission_middleware import require_admin
        
        current_user = {"user_id": "user123"}
        
        user = MagicMock()
        user.roles = ["user_role_id"]
        mock_user_service.get_user.return_value = user
        
        role = MagicMock()
        role.code = "user"
        mock_role_service.get_role.return_value = role
        
        with patch('src.middleware.permission_middleware.user_service', mock_user_service), \
             patch('src.middleware.permission_middleware.role_service', mock_role_service):
            
            with pytest.raises(HTTPException) as exc_info:
                await require_admin(current_user)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_require_roles_success(self, mock_request):
        """测试require_roles装饰器（成功）"""
        from src.middleware.auth_middleware import require_roles
        
        mock_user = {
            "user_id": "user123",
            "username": "testuser",
            "roles": ["admin", "user"]
        }
        
        role_checker = await require_roles("admin", "manager")
        result = await role_checker(mock_user)
        
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_require_roles_failure(self, mock_request):
        """测试require_roles装饰器（失败）"""
        from src.middleware.auth_middleware import require_roles
        
        mock_user = {
            "user_id": "user123",
            "username": "testuser",
            "roles": ["user"]
        }
        
        role_checker = await require_roles("admin", "manager")
        
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_require_roles_no_user(self, mock_request):
        """测试require_roles装饰器（无用户）"""
        from src.middleware.auth_middleware import require_roles, get_current_user
        
        role_checker = await require_roles("admin")
        
        with patch('src.middleware.auth_middleware.get_current_user') as mock_get_user:
            mock_get_user.side_effect = HTTPException(status_code=401, detail="Not authenticated")
            
            with pytest.raises(HTTPException) as exc_info:
                await role_checker(None)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_token_not_in_cache(self, mock_request, mock_jwt_manager):
        """测试令牌不在缓存中但仍有效"""
        from src.middleware.auth_middleware import get_current_user
        
        mock_request.cookies = {"access_token": "test_token"}
        mock_credentials = MagicMock()
        mock_credentials.credentials = "test_token"
        
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_access_token.return_value = None
        
        with patch('src.middleware.auth_middleware.jwt_manager', mock_jwt_manager), \
             patch('src.middleware.auth_middleware.cache_manager', mock_cache_manager), \
             patch('src.middleware.auth_middleware.security') as mock_security:
            mock_security.return_value = None
            
            user = await get_current_user(mock_request, None)
            
            assert user is not None
            assert user["user_id"] == "user123"

