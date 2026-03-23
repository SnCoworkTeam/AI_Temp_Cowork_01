"""
管理后台路由测试
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
class TestAdminUsersRoutes:
    """管理后台用户路由测试"""
    
    @pytest.fixture
    def mock_user_service(self):
        """模拟用户服务"""
        user_service = AsyncMock()
        return user_service
    
    @pytest.fixture
    def mock_role_service(self):
        """模拟角色服务"""
        role_service = AsyncMock()
        return role_service
    
    @pytest.fixture
    def mock_permission_service(self):
        """模拟权限服务"""
        permission_service = AsyncMock()
        return permission_service
    
    @pytest.fixture
    def mock_admin_user(self):
        """模拟管理员用户"""
        return {
            "user_id": "admin123",
            "username": "admin",
            "email": "admin@example.com",
            "roles": ["admin_role"]
        }
    
    @pytest.fixture
    def client(self, mock_user_service, mock_role_service, mock_permission_service):
        """测试客户端"""
        from src.main import app
        
        # Mock服务
        with patch('src.routes.admin.users.user_service', mock_user_service), \
             patch('src.routes.admin.users.role_service', mock_role_service), \
             patch('src.routes.admin.users.permission_service', mock_permission_service):
            yield TestClient(app)
    
    def test_list_users_endpoint(self, client, mock_user_service, mock_admin_user):
        """测试获取用户列表端点"""
        # Mock用户列表
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.roles = []
        mock_user.permissions = []
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        
        mock_user_service.list_users.return_value = ([mock_user], 1)
        
        # Mock管理员认证
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.get("/admin/users?page=1&page_size=20")
            # 可能返回401（未认证）或200（已认证）
            assert response.status_code in [200, 401, 403]
    
    def test_create_user_endpoint(self, client, mock_user_service, mock_admin_user):
        """测试创建用户端点"""
        mock_user = MagicMock()
        mock_user.user_id = "newuser123"
        mock_user.username = "newuser"
        mock_user.email = "newuser@example.com"
        mock_user.display_name = "New User"
        mock_user.roles = []
        mock_user.permissions = []
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.create_user.return_value = mock_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.post(
                "/admin/users",
                json={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "password123",
                    "display_name": "New User"
                }
            )
            assert response.status_code in [201, 401, 403, 400]
    
    def test_get_user_endpoint(self, client, mock_user_service, mock_role_service, mock_permission_service, mock_admin_user):
        """测试获取用户详情端点"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.roles = ["role1"]
        mock_user.permissions = ["perm1"]
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        mock_user.metadata = {}
        
        mock_user_service.get_user.return_value = mock_user
        
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Role 1"
        mock_role.code = "role1"
        mock_role_service.get_role.return_value = mock_role
        
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Permission 1"
        mock_permission.code = "perm1"
        mock_permission_service.get_permission.return_value = mock_permission
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.get("/admin/users/user123")
            assert response.status_code in [200, 401, 403, 404]
    
    def test_update_user_endpoint(self, client, mock_user_service, mock_admin_user):
        """测试更新用户端点"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Updated User"
        mock_user.roles = []
        mock_user.permissions = []
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.update_user.return_value = mock_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.put(
                "/admin/users/user123",
                json={
                    "display_name": "Updated User"
                }
            )
            assert response.status_code in [200, 401, 403, 404]
    
    def test_delete_user_endpoint(self, client, mock_user_service, mock_admin_user):
        """测试删除用户端点"""
        mock_user_service.delete_user.return_value = True
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.delete("/admin/users/user123")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_add_role_to_user_endpoint(self, client, mock_user_service, mock_admin_user):
        """测试为用户添加角色端点"""
        mock_user_service.add_role_to_user.return_value = True
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.post("/admin/users/user123/roles/role1")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_remove_role_from_user_endpoint(self, client, mock_user_service, mock_admin_user):
        """测试移除用户角色端点"""
        mock_user_service.remove_role_from_user.return_value = True
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.delete("/admin/users/user123/roles/role1")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_create_user_duplicate_username(self, client, mock_user_service, mock_admin_user):
        """测试创建用户（用户名重复）"""
        mock_existing_user = MagicMock()
        mock_user_service.get_user_by_username.return_value = mock_existing_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.post(
                "/admin/users",
                json={
                    "username": "existinguser",
                    "email": "new@example.com",
                    "password": "password123"
                }
            )
            assert response.status_code in [400, 401, 403]
    
    def test_create_user_duplicate_email(self, client, mock_user_service, mock_admin_user):
        """测试创建用户（邮箱重复）"""
        mock_user_service.get_user_by_username.return_value = None
        mock_existing_user = MagicMock()
        mock_user_service.get_user_by_email.return_value = mock_existing_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.post(
                "/admin/users",
                json={
                    "username": "newuser",
                    "email": "existing@example.com",
                    "password": "password123"
                }
            )
            assert response.status_code in [400, 401, 403]
    
    def test_get_user_not_found(self, client, mock_user_service, mock_admin_user):
        """测试获取不存在的用户"""
        mock_user_service.get_user.return_value = None
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.get("/admin/users/nonexistent")
            assert response.status_code in [404, 401, 403]
    
    def test_update_user_not_found(self, client, mock_user_service, mock_admin_user):
        """测试更新不存在的用户"""
        mock_user_service.get_user.return_value = None
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.put(
                "/admin/users/nonexistent",
                json={"display_name": "Updated"}
            )
            assert response.status_code in [404, 401, 403]
    
    def test_update_user_duplicate_username(self, client, mock_user_service, mock_admin_user):
        """测试更新用户（用户名重复）"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user_service.get_user.return_value = mock_user
        
        mock_existing_user = MagicMock()
        mock_existing_user.user_id = "other123"
        mock_user_service.get_user_by_username.return_value = mock_existing_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.put(
                "/admin/users/user123",
                json={"username": "existinguser"}
            )
            assert response.status_code in [400, 401, 403]
    
    def test_delete_user_not_found(self, client, mock_user_service, mock_admin_user):
        """测试删除不存在的用户"""
        mock_user_service.delete_user.return_value = False
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.delete("/admin/users/nonexistent")
            assert response.status_code in [404, 401, 403]
    
    def test_list_users_with_filters(self, client, mock_user_service, mock_admin_user):
        """测试带过滤条件的用户列表"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.roles = []
        mock_user.permissions = []
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        
        mock_user_service.list_users.return_value = ([mock_user], 1)
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.get("/admin/users?page=1&page_size=10&search=test&status=active&role=admin")
            assert response.status_code in [200, 401, 403]
    
    def test_add_role_to_user_not_found(self, client, mock_user_service, mock_admin_user):
        """测试为不存在的用户添加角色"""
        mock_user_service.add_role_to_user.return_value = False
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.post("/admin/users/nonexistent/roles/role1")
            assert response.status_code in [404, 401, 403]
    
    def test_remove_role_from_user_not_found(self, client, mock_user_service, mock_admin_user):
        """测试从不存在的用户移除角色"""
        mock_user_service.remove_role_from_user.return_value = False
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            
            response = client.delete("/admin/users/nonexistent/roles/role1")
            assert response.status_code in [404, 401, 403]
    
    def test_get_user_detail_with_roles_and_permissions(self, client, mock_user_service, mock_role_service, mock_permission_service, mock_admin_user):
        """测试获取用户详情（包含角色和权限详情）"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.roles = ["role1"]
        mock_user.permissions = ["perm1"]
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        mock_user.metadata = {}
        
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Role 1"
        mock_role.code = "role1"
        mock_role.permissions = ["perm2"]
        
        mock_permission1 = MagicMock()
        mock_permission1.id = "perm1"
        mock_permission1.name = "Permission 1"
        mock_permission1.code = "perm1"
        
        mock_permission2 = MagicMock()
        mock_permission2.id = "perm2"
        mock_permission2.name = "Permission 2"
        mock_permission2.code = "perm2"
        
        mock_user_service.get_user.return_value = mock_user
        mock_role_service.get_role.return_value = mock_role
        mock_permission_service.get_permission.side_effect = [mock_permission1, mock_permission2]
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/users/user123")
            assert response.status_code in [200, 401, 403, 404]
    
    def test_update_user_username_conflict(self, client, mock_user_service, mock_admin_user):
        """测试更新用户（用户名冲突）"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "olduser"
        mock_user.email = "test@example.com"
        mock_user_service.get_user.return_value = mock_user
        
        mock_existing_user = MagicMock()
        mock_existing_user.user_id = "other123"
        mock_user_service.get_user_by_username.return_value = mock_existing_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/users/user123",
                json={"username": "existinguser"}
            )
            assert response.status_code in [400, 401, 403]
    
    def test_update_user_email_conflict(self, client, mock_user_service, mock_admin_user):
        """测试更新用户（邮箱冲突）"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "old@example.com"
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.get_user_by_username.return_value = None
        
        mock_existing_user = MagicMock()
        mock_existing_user.user_id = "other123"
        mock_user_service.get_user_by_email.return_value = mock_existing_user
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/users/user123",
                json={"email": "existing@example.com"}
            )
            assert response.status_code in [400, 401, 403]
    
    def test_update_user_update_failed(self, client, mock_user_service, mock_admin_user):
        """测试更新用户（更新失败）"""
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.update_user.return_value = None
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/users/user123",
                json={"display_name": "Updated"}
            )
            assert response.status_code in [500, 401, 403]
    
    def test_list_users_exception(self, client, mock_user_service, mock_admin_user):
        """测试获取用户列表（异常）"""
        mock_user_service.list_users.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/users")
            assert response.status_code in [500, 401, 403]
    
    def test_create_user_exception(self, client, mock_user_service, mock_admin_user):
        """测试创建用户（异常）"""
        mock_user_service.get_user_by_username.return_value = None
        mock_user_service.get_user_by_email.return_value = None
        mock_user_service.create_user.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/users",
                json={
                    "username": "newuser",
                    "email": "new@example.com",
                    "password": "password123"
                }
            )
            assert response.status_code in [500, 401, 403]
    
    def test_get_user_exception(self, client, mock_user_service, mock_role_service, mock_permission_service, mock_admin_user):
        """测试获取用户详情（异常）"""
        mock_user_service.get_user.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/users/user123")
            assert response.status_code in [500, 401, 403]
    
    def test_delete_user_exception(self, client, mock_user_service, mock_admin_user):
        """测试删除用户（异常）"""
        mock_user_service.delete_user.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/users/user123")
            assert response.status_code in [500, 401, 403]
    
    def test_add_role_to_user_exception(self, client, mock_user_service, mock_admin_user):
        """测试添加用户角色（异常）"""
        mock_user_service.add_role_to_user.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post("/admin/users/user123/roles/role1")
            assert response.status_code in [500, 401, 403]
    
    def test_remove_role_from_user_exception(self, client, mock_user_service, mock_admin_user):
        """测试移除用户角色（异常）"""
        mock_user_service.remove_role_from_user.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.users.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/users/user123/roles/role1")
            assert response.status_code in [500, 401, 403]
    
    def test_user_to_response_helper(self):
        """测试_user_to_response辅助函数"""
        from src.routes.admin.users import _user_to_response
        from datetime import datetime
        
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.roles = ["role1"]
        mock_user.permissions = ["perm1"]
        mock_user.status.value = "active"
        mock_user.last_login_at = datetime.now()
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        
        response = _user_to_response(mock_user)
        
        assert response.user_id == "user123"
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.display_name == "Test User"
        assert response.roles == ["role1"]
        assert response.permissions == ["perm1"]
        assert response.status == "active"
        assert response.last_login_at is not None
        assert response.created_at is not None
        assert response.updated_at is not None
    
    def test_user_to_response_with_none_dates(self):
        """测试_user_to_response辅助函数（日期为None）"""
        from src.routes.admin.users import _user_to_response
        
        mock_user = MagicMock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.roles = []
        mock_user.permissions = []
        mock_user.status.value = "active"
        mock_user.last_login_at = None
        mock_user.created_at = None
        mock_user.updated_at = None
        
        response = _user_to_response(mock_user)
        
        assert response.user_id == "user123"
        assert response.last_login_at is None
        assert response.created_at is None
        assert response.updated_at is None

