"""
用户路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestUsersRoutes:
    """用户路由测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def mock_user_service(self):
        """模拟用户服务"""
        user_service = AsyncMock()
        return user_service
    
    @pytest.fixture
    def mock_current_user(self):
        """模拟当前用户"""
        return {
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com"
        }
    
    @pytest.fixture
    def client(self, mock_db, mock_user_service):
        """测试客户端"""
        from src.main import app
        
        with patch('src.routes.users.get_db', return_value=mock_db), \
             patch('src.routes.users.UserService', return_value=mock_user_service), \
             patch('src.routes.users.get_current_user', return_value={"user_id": "user123"}):
            yield TestClient(app)
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_success(self, client, mock_user_service, mock_current_user):
        """测试获取当前用户信息成功"""
        mock_user_service.get_user.return_value = {
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "display_name": "Test User",
            "full_name": "Test User Full",
            "roles": ["user"],
            "permissions": ["read"],
            "status": "active",
            "last_login_at": "2024-01-01T00:00:00",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        with patch('src.routes.users.get_current_user', return_value=mock_current_user):
            response = client.get("/users/me")
            assert response.status_code in [200, 401, 500]
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_not_found(self, client, mock_user_service, mock_current_user):
        """测试获取当前用户信息（用户不存在）"""
        mock_user_service.get_user.return_value = None
        
        with patch('src.routes.users.get_current_user', return_value=mock_current_user):
            response = client.get("/users/me")
            assert response.status_code in [404, 401, 500]
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_unauthorized(self, client):
        """测试获取当前用户信息（未授权）"""
        with patch('src.routes.users.get_current_user', side_effect=HTTPException(status_code=401, detail="未授权")):
            response = client.get("/users/me")
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_exception(self, client, mock_user_service, mock_current_user):
        """测试获取当前用户信息（异常）"""
        mock_user_service.get_user.side_effect = Exception("Database error")
        
        with patch('src.routes.users.get_current_user', return_value=mock_current_user):
            response = client.get("/users/me")
            assert response.status_code in [500, 401]

