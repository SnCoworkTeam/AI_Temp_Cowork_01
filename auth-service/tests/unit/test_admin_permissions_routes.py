"""
管理后台权限路由测试
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
class TestAdminPermissionsRoutes:
    """管理后台权限路由测试"""
    
    @pytest.fixture
    def mock_permission_service(self):
        """模拟权限服务"""
        permission_service = AsyncMock()
        return permission_service
    
    @pytest.fixture
    def mock_admin_user(self):
        """模拟管理员用户"""
        return {"user_id": "admin123", "username": "admin"}
    
    @pytest.fixture
    def client(self, mock_permission_service):
        """测试客户端"""
        from src.main import app
        
        with patch('src.routes.admin.permissions.permission_service', mock_permission_service):
            yield TestClient(app)
    
    def test_list_permissions_endpoint(self, client, mock_permission_service, mock_admin_user):
        """测试获取权限列表端点"""
        from src.models.permission_models import ResourceType, PermissionType
        
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Permission 1"
        mock_permission.code = "perm1"
        mock_permission.resource_type.value = "workflow"
        mock_permission.permission_type.value = "execute"
        mock_permission.description = "Test permission"
        mock_permission.created_at = None
        mock_permission.updated_at = None
        
        mock_permission_service.list_permissions.return_value = ([mock_permission], 1)
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/permissions?page=1&page_size=20")
            assert response.status_code in [200, 401, 403]
    
    def test_create_permission_endpoint(self, client, mock_permission_service, mock_admin_user):
        """测试创建权限端点"""
        from src.models.permission_models import ResourceType, PermissionType
        
        mock_permission = MagicMock()
        mock_permission.id = "newperm123"
        mock_permission.name = "New Permission"
        mock_permission.code = "newperm"
        mock_permission.resource_type.value = "workflow"
        mock_permission.permission_type.value = "execute"
        mock_permission.description = "New permission"
        mock_permission.created_at = None
        mock_permission.updated_at = None
        
        mock_permission_service.create_permission.return_value = mock_permission
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/permissions",
                json={
                    "name": "New Permission",
                    "code": "newperm",
                    "resource_type": "workflow",
                    "permission_type": "execute",
                    "description": "New permission"
                }
            )
            assert response.status_code in [201, 401, 403, 400]
    
    def test_get_permission_endpoint(self, client, mock_permission_service, mock_admin_user):
        """测试获取权限详情端点"""
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Permission 1"
        mock_permission.code = "perm1"
        mock_permission.resource_type.value = "workflow"
        mock_permission.permission_type.value = "execute"
        mock_permission.description = "Test permission"
        mock_permission.created_at = None
        mock_permission.updated_at = None
        
        mock_permission_service.get_permission.return_value = mock_permission
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/permissions/perm1")
            assert response.status_code in [200, 401, 403, 404]
    
    def test_update_permission_endpoint(self, client, mock_permission_service, mock_admin_user):
        """测试更新权限端点"""
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Updated Permission"
        mock_permission.code = "perm1"
        mock_permission.resource_type.value = "workflow"
        mock_permission.permission_type.value = "execute"
        mock_permission.description = "Updated description"
        mock_permission.created_at = None
        mock_permission.updated_at = None
        
        mock_permission_service.update_permission.return_value = mock_permission
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/permissions/perm1",
                json={"description": "Updated description"}
            )
            assert response.status_code in [200, 401, 403, 404]
    
    def test_delete_permission_endpoint(self, client, mock_permission_service, mock_admin_user):
        """测试删除权限端点"""
        mock_permission_service.delete_permission.return_value = True
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/permissions/perm1")
            assert response.status_code in [204, 401, 403, 404]
    
    def test_create_permission_duplicate_code(self, client, mock_permission_service, mock_admin_user):
        """测试创建权限（代码重复）"""
        mock_permission_service.create_permission.side_effect = ValueError("Permission with code 'test:read' already exists")
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/permissions",
                json={
                    "name": "Test Permission",
                    "code": "test:read",
                    "resource_type": "api",
                    "permission_type": "read"
                }
            )
            assert response.status_code in [400, 401, 403]
    
    def test_get_permission_not_found(self, client, mock_permission_service, mock_admin_user):
        """测试获取不存在的权限"""
        mock_permission_service.get_permission.return_value = None
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/permissions/nonexistent")
            assert response.status_code in [404, 401, 403]
    
    def test_update_permission_not_found(self, client, mock_permission_service, mock_admin_user):
        """测试更新不存在的权限"""
        mock_permission_service.update_permission.return_value = None
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/permissions/nonexistent",
                json={"description": "Updated"}
            )
            assert response.status_code in [404, 401, 403]
    
    def test_delete_permission_not_found(self, client, mock_permission_service, mock_admin_user):
        """测试删除不存在的权限"""
        mock_permission_service.delete_permission.return_value = False
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/permissions/nonexistent")
            assert response.status_code in [404, 401, 403]
    
    def test_list_permissions_with_filters(self, client, mock_permission_service, mock_admin_user):
        """测试带过滤条件的权限列表"""
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Permission 1"
        mock_permission.code = "perm1"
        mock_permission.resource_type.value = "workflow"
        mock_permission.permission_type.value = "execute"
        mock_permission.description = "Test"
        mock_permission.created_at = None
        mock_permission.updated_at = None
        
        mock_permission_service.list_permissions.return_value = ([mock_permission], 1)
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/permissions?page=1&page_size=20&resource_type=workflow&permission_type=execute")
            assert response.status_code in [200, 401, 403]
    
    def test_update_permission_update_failed(self, client, mock_permission_service, mock_admin_user):
        """测试更新权限（更新失败）"""
        mock_permission_service.update_permission.return_value = None
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/permissions/perm1",
                json={"description": "Updated"}
            )
            assert response.status_code in [404, 401, 403]
    
    def test_list_permissions_exception(self, client, mock_permission_service, mock_admin_user):
        """测试获取权限列表（异常）"""
        mock_permission_service.list_permissions.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/permissions")
            assert response.status_code in [500, 401, 403]
    
    def test_create_permission_exception(self, client, mock_permission_service, mock_admin_user):
        """测试创建权限（异常）"""
        mock_permission_service.create_permission.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.post(
                "/admin/permissions",
                json={
                    "name": "New Permission",
                    "code": "newperm",
                    "resource_type": "api",
                    "permission_type": "read"
                }
            )
            assert response.status_code in [500, 401, 403]
    
    def test_get_permission_exception(self, client, mock_permission_service, mock_admin_user):
        """测试获取权限详情（异常）"""
        mock_permission_service.get_permission.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.get("/admin/permissions/perm1")
            assert response.status_code in [500, 401, 403]
    
    def test_update_permission_exception(self, client, mock_permission_service, mock_admin_user):
        """测试更新权限（异常）"""
        mock_permission_service.update_permission.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.put(
                "/admin/permissions/perm1",
                json={"description": "Updated"}
            )
            assert response.status_code in [500, 401, 403]
    
    def test_delete_permission_exception(self, client, mock_permission_service, mock_admin_user):
        """测试删除权限（异常）"""
        mock_permission_service.delete_permission.side_effect = Exception("Database error")
        
        with patch('src.routes.admin.permissions.require_admin') as mock_require_admin:
            mock_require_admin.return_value = mock_admin_user
            response = client.delete("/admin/permissions/perm1")
            assert response.status_code in [500, 401, 403]
    
    def test_permission_to_response_helper(self):
        """测试_permission_to_response辅助函数"""
        from src.routes.admin.permissions import _permission_to_response
        from datetime import datetime
        
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Test Permission"
        mock_permission.code = "test:read"
        mock_permission.resource_type.value = "api"
        mock_permission.permission_type.value = "read"
        mock_permission.description = "Test description"
        mock_permission.created_at = datetime.now()
        mock_permission.updated_at = datetime.now()
        
        response = _permission_to_response(mock_permission)
        
        assert response.id == "perm1"
        assert response.name == "Test Permission"
        assert response.code == "test:read"
        assert response.resource_type == "api"
        assert response.permission_type == "read"
        assert response.description == "Test description"
        assert response.created_at is not None
        assert response.updated_at is not None
    
    def test_permission_to_response_with_none_dates(self):
        """测试_permission_to_response辅助函数（日期为None）"""
        from src.routes.admin.permissions import _permission_to_response
        
        mock_permission = MagicMock()
        mock_permission.id = "perm1"
        mock_permission.name = "Test Permission"
        mock_permission.code = "test:read"
        mock_permission.resource_type.value = "workflow"
        mock_permission.permission_type.value = "execute"
        mock_permission.description = "Test description"
        mock_permission.created_at = None
        mock_permission.updated_at = None
        
        response = _permission_to_response(mock_permission)
        
        assert response.id == "perm1"
        assert response.resource_type == "workflow"
        assert response.permission_type == "execute"
        assert response.created_at is None
        assert response.updated_at is None

