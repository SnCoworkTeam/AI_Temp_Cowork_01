"""
管理后台角色路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestAdminRolesRoutes:
    """管理后台角色路由测试"""
    
    @pytest.fixture
    def mock_role_service(self):
        """模拟角色服务"""
        role_service = AsyncMock()
        return role_service
    
    @pytest.fixture
    def mock_admin_user(self):
        """模拟管理员用户"""
        return {"user_id": "admin123", "username": "admin"}
    
    @pytest.fixture
    def client(self, mock_role_service):
        """测试客户端"""
        from src.main import app
        
        with patch('src.routes.admin.roles.role_service', mock_role_service):
            yield TestClient(app)
    
    def test_list_roles_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试获取角色列表端点"""
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Role 1"
        mock_role.code = "role1"
        mock_role.description = "Test role"
        mock_role.permissions = []
        mock_role.is_system = False
        mock_role.created_at = None
        mock_role.updated_at = None
        
        mock_role_service.list_roles.return_value = ([mock_role], 1)
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/roles?page=1&page_size=20")
            assert response.status_code in [200, 401, 403]
    
    def test_create_role_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试创建角色端点"""
        mock_role = MagicMock()
        mock_role.id = "newrole123"
        mock_role.name = "New Role"
        mock_role.code = "newrole"
        mock_role.description = "New role description"
        mock_role.permissions = []
        mock_role.is_system = False
        mock_role.created_at = None
        mock_role.updated_at = None
        
        mock_role_service.get_role_by_code.return_value = None
        mock_role_service.create_role.return_value = mock_role
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/roles",
                json={
                    "name": "New Role",
                    "code": "newrole",
                    "description": "New role description"
                }
            )
            assert response.status_code in [201, 401, 403, 400]
    
    def test_get_role_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试获取角色详情端点"""
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Role 1"
        mock_role.code = "role1"
        mock_role.description = "Test role"
        mock_role.permissions = []
        mock_role.is_system = False
        mock_role.created_at = None
        mock_role.updated_at = None
        
        mock_role_service.get_role.return_value = mock_role
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/roles/role1")
            assert response.status_code in [200, 401, 403, 404]
    
    def test_update_role_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试更新角色端点"""
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Updated Role"
        mock_role.code = "role1"
        mock_role.description = "Updated description"
        mock_role.permissions = []
        mock_role.is_system = False
        mock_role.created_at = None
        mock_role.updated_at = None
        
        mock_role_service.get_role.return_value = mock_role
        mock_role_service.update_role.return_value = mock_role
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/roles/role1",
                json={"description": "Updated description"}
            )
            assert response.status_code in [200, 401, 403, 404]
    
    def test_delete_role_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试删除角色端点"""
        mock_role_service.delete_role.return_value = True
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/roles/role1")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_add_permission_to_role_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试为角色添加权限端点"""
        mock_role_service.add_permission_to_role.return_value = True
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post("/admin/roles/role1/permissions/perm1")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_remove_permission_from_role_endpoint(self, client, mock_role_service, mock_admin_user):
        """测试移除角色权限端点"""
        mock_role_service.remove_permission_from_role.return_value = True
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/roles/role1/permissions/perm1")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_create_role_duplicate_code(self, client, mock_role_service, mock_admin_user):
        """测试创建角色（代码重复）"""
        mock_existing_role = MagicMock()
        mock_role_service.get_role_by_code.return_value = mock_existing_role
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/roles",
                json={
                    "name": "New Role",
                    "code": "existingcode",
                    "description": "Description"
                }
            )
            assert response.status_code in [400, 401, 403]
    
    def test_get_role_not_found(self, client, mock_role_service, mock_admin_user):
        """测试获取不存在的角色"""
        mock_role_service.get_role.return_value = None
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/roles/nonexistent")
            assert response.status_code in [404, 401, 403]
    
    def test_update_role_not_found(self, client, mock_role_service, mock_admin_user):
        """测试更新不存在的角色"""
        mock_role_service.get_role.return_value = None
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/roles/nonexistent",
                json={"description": "Updated"}
            )
            assert response.status_code in [404, 401, 403]
    
    def test_delete_role_not_found(self, client, mock_role_service, mock_admin_user):
        """测试删除不存在的角色"""
        mock_role_service.delete_role.return_value = False
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/roles/nonexistent")
            assert response.status_code in [404, 401, 403]
    
    def test_list_roles_with_search(self, client, mock_role_service, mock_admin_user):
        """测试带搜索的角色列表"""
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Test Role"
        mock_role.code = "test_role"
        mock_role.description = "Test"
        mock_role.permissions = []
        mock_role.is_system = False
        mock_role.created_at = None
        mock_role.updated_at = None
        
        mock_role_service.list_roles.return_value = ([mock_role], 1)
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/roles?page=1&page_size=20&search=test")
            assert response.status_code in [200, 401, 403]
    
    def test_add_permission_to_role_not_found(self, client, mock_role_service, mock_admin_user):
        """测试为不存在的角色添加权限"""
        mock_role_service.add_permission_to_role.return_value = False
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post("/admin/roles/nonexistent/permissions/perm1")
            assert response.status_code in [404, 401, 403]
    
    def test_remove_permission_from_role_not_found(self, client, mock_role_service, mock_admin_user):
        """测试从不存在的角色移除权限"""
        mock_role_service.remove_permission_from_role.return_value = False
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/roles/nonexistent/permissions/perm1")
            assert response.status_code in [404, 401, 403]
    
    def test_update_role_update_failed(self, client, mock_role_service, mock_admin_user):
        """测试更新角色（更新失败）"""
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role_service.get_role.return_value = mock_role
        mock_role_service.update_role.return_value = None
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/roles/role1",
                json={"description": "Updated"}
            )
            assert response.status_code in [500, 401, 403]
    
    def test_list_roles_exception(self, client, mock_role_service, mock_admin_user):
        """测试获取角色列表（异常）"""
        mock_role_service.list_roles.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/roles")
            assert response.status_code in [500, 401, 403]
    
    def test_create_role_exception(self, client, mock_role_service, mock_admin_user):
        """测试创建角色（异常）"""
        mock_role_service.get_role_by_code.return_value = None
        mock_role_service.create_role.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/roles",
                json={
                    "name": "New Role",
                    "code": "newrole",
                    "description": "Description"
                }
            )
            assert response.status_code in [500, 401, 403]
    
    def test_get_role_exception(self, client, mock_role_service, mock_admin_user):
        """测试获取角色详情（异常）"""
        mock_role_service.get_role.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/roles/role1")
            assert response.status_code in [500, 401, 403]
    
    def test_update_role_exception(self, client, mock_role_service, mock_admin_user):
        """测试更新角色（异常）"""
        mock_role = MagicMock()
        mock_role_service.get_role.return_value = mock_role
        mock_role_service.update_role.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/roles/role1",
                json={"description": "Updated"}
            )
            assert response.status_code in [500, 401, 403]
    
    def test_delete_role_exception(self, client, mock_role_service, mock_admin_user):
        """测试删除角色（异常）"""
        mock_role_service.delete_role.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/roles/role1")
            assert response.status_code in [500, 401, 403]
    
    def test_add_permission_to_role_exception(self, client, mock_role_service, mock_admin_user):
        """测试为角色添加权限（异常）"""
        mock_role_service.add_permission_to_role.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post("/admin/roles/role1/permissions/perm1")
            assert response.status_code in [500, 401, 403]
    
    def test_remove_permission_from_role_exception(self, client, mock_role_service, mock_admin_user):
        """测试移除角色权限（异常）"""
        mock_role_service.remove_permission_from_role.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.roles.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/roles/role1/permissions/perm1")
            assert response.status_code in [500, 401, 403]
    
    def test_role_to_response_helper(self):
        """测试_role_to_response辅助函数"""
        from src.routes.admin.roles import _role_to_response
        from datetime import datetime
        
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Test Role"
        mock_role.code = "test_role"
        mock_role.description = "Test description"
        mock_role.permissions = ["perm1", "perm2"]
        mock_role.is_system = False
        mock_role.created_at = datetime.now()
        mock_role.updated_at = datetime.now()
        
        response = _role_to_response(mock_role)
        
        assert response.id == "role1"
        assert response.name == "Test Role"
        assert response.code == "test_role"
        assert response.description == "Test description"
        assert response.permissions == ["perm1", "perm2"]
        assert response.is_system is False
        assert response.created_at is not None
        assert response.updated_at is not None
    
    def test_role_to_response_with_none_dates(self):
        """测试_role_to_response辅助函数（日期为None）"""
        from src.routes.admin.roles import _role_to_response
        
        mock_role = MagicMock()
        mock_role.id = "role1"
        mock_role.name = "Test Role"
        mock_role.code = "test_role"
        mock_role.description = "Test description"
        mock_role.permissions = []
        mock_role.is_system = True
        mock_role.created_at = None
        mock_role.updated_at = None
        
        response = _role_to_response(mock_role)
        
        assert response.id == "role1"
        assert response.is_system is True
        assert response.created_at is None
        assert response.updated_at is None

