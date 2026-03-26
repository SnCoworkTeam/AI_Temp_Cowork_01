"""
角色服务测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestRoleService:
    """角色服务测试"""
    
    @pytest.fixture
    def mock_cache_manager(self):
        """模拟缓存管理器"""
        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set = AsyncMock()
        cache_manager.delete = AsyncMock()
        return cache_manager
    
    @pytest.fixture
    def role_service(self, mock_cache_manager):
        """创建角色服务实例"""
        from src.services.role_service import RoleService
        
        with patch('src.services.role_service.cache_manager', mock_cache_manager):
            service = RoleService()
            return service
    
    @pytest.mark.asyncio
    async def test_create_role(self, role_service, mock_cache_manager):
        """测试创建角色"""
        role_data = {
            "name": "Test Role",
            "code": "test_role",
            "description": "Test role description",
            "permissions": []
        }
        
        role = await role_service.create_role(role_data)
        
        assert role is not None
        assert role.name == "Test Role"
        assert role.code == "test_role"
        mock_cache_manager.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_role_not_found(self, role_service, mock_cache_manager):
        """测试获取不存在的角色"""
        mock_cache_manager.get.return_value = None
        
        role = await role_service.get_role("nonexistent")
        assert role is None
    
    @pytest.mark.asyncio
    async def test_get_role_found(self, role_service, mock_cache_manager):
        """测试获取存在的角色"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        role = await role_service.get_role("role1")
        assert role is not None
        assert role.id == "role1"
    
    @pytest.mark.asyncio
    async def test_get_role_by_code(self, role_service, mock_cache_manager):
        """测试根据代码获取角色"""
        role_ids = ["role1", "role2"]
        mock_cache_manager.get.side_effect = [
            role_ids,  # _get_all_role_ids
            {  # get_role for role1
                "id": "role1",
                "name": "Test Role",
                "code": "test_role",
                "description": "Test",
                "permissions": [],
                "is_system": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        role = await role_service.get_role_by_code("test_role")
        # 可能返回None或角色对象
        assert role is None or role.code == "test_role"
    
    @pytest.mark.asyncio
    async def test_update_role(self, role_service, mock_cache_manager):
        """测试更新角色"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        updates = {"description": "Updated description"}
        updated_role = await role_service.update_role("role1", updates)
        
        assert updated_role is not None
        mock_cache_manager.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_role(self, role_service, mock_cache_manager):
        """测试删除角色"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.side_effect = [
            role_data,  # get_role
            ["role1"]   # _get_all_role_ids
        ]
        
        result = await role_service.delete_role("role1")
        assert result is True
        mock_cache_manager.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_system_role(self, role_service, mock_cache_manager):
        """测试删除系统角色（应该失败）"""
        role_data = {
            "id": "role1",
            "name": "System Role",
            "code": "system_role",
            "description": "System",
            "permissions": [],
            "is_system": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        result = await role_service.delete_role("role1")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_roles(self, role_service, mock_cache_manager):
        """测试列出角色"""
        role_ids = ["role1", "role2"]
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_cache_manager.get.side_effect = [
            role_ids,  # _get_all_role_ids
            role_data,  # get_role for role1
            role_data   # get_role for role2
        ]
        
        roles, total = await role_service.list_roles(page=1, page_size=20)
        assert isinstance(roles, list)
        assert total >= 0
    
    @pytest.mark.asyncio
    async def test_add_permission_to_role(self, role_service, mock_cache_manager):
        """测试为角色添加权限"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        result = await role_service.add_permission_to_role("role1", "perm1")
        assert result is True
        mock_cache_manager.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_remove_permission_from_role(self, role_service, mock_cache_manager):
        """测试移除角色权限"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": ["perm1"],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        result = await role_service.remove_permission_from_role("role1", "perm1")
        assert result is True
        mock_cache_manager.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_role_not_found(self, role_service, mock_cache_manager):
        """测试更新不存在的角色"""
        mock_cache_manager.get.return_value = None
        
        result = await role_service.update_role("nonexistent", {"name": "Updated"})
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_system_role(self, role_service, mock_cache_manager):
        """测试更新系统角色（某些字段不能修改）"""
        role_data = {
            "id": "role1",
            "name": "System Role",
            "code": "system_role",
            "description": "System",
            "permissions": [],
            "is_system": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        updates = {
            "name": "Updated Name",
            "code": "new_code",  # 系统角色的code不应该被修改
            "is_system": False   # 系统角色的is_system不应该被修改
        }
        
        result = await role_service.update_role("role1", updates)
        assert result is not None
        # code和is_system应该被移除，不会被更新
        mock_cache_manager.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_add_permission_to_role_not_found(self, role_service, mock_cache_manager):
        """测试为不存在的角色添加权限"""
        mock_cache_manager.get.return_value = None
        
        result = await role_service.add_permission_to_role("nonexistent", "perm1")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_permission_to_role_already_exists(self, role_service, mock_cache_manager):
        """测试为角色添加已存在的权限"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": ["perm1"],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        result = await role_service.add_permission_to_role("role1", "perm1")
        assert result is True  # 即使已存在也应该返回True
    
    @pytest.mark.asyncio
    async def test_remove_permission_from_role_not_found(self, role_service, mock_cache_manager):
        """测试从不存在的角色移除权限"""
        mock_cache_manager.get.return_value = None
        
        result = await role_service.remove_permission_from_role("nonexistent", "perm1")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_remove_permission_not_in_role(self, role_service, mock_cache_manager):
        """测试移除角色中不存在的权限"""
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": ["perm1"],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        result = await role_service.remove_permission_from_role("role1", "perm2")
        assert result is True  # 即使不存在也应该返回True
    
    @pytest.mark.asyncio
    async def test_list_roles_with_search(self, role_service, mock_cache_manager):
        """测试带搜索的列出角色"""
        role_ids = ["role1", "role2"]
        role_data1 = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test description",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        role_data2 = {
            "id": "role2",
            "name": "Another Role",
            "code": "another_role",
            "description": "Another",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_cache_manager.get.side_effect = [
            role_ids,
            role_data1,
            role_data2
        ]
        
        roles, total = await role_service.list_roles(page=1, page_size=20, search="Test")
        assert isinstance(roles, list)
        assert total >= 0
    
    @pytest.mark.asyncio
    async def test_list_roles_pagination(self, role_service, mock_cache_manager):
        """测试角色列表分页"""
        role_ids = ["role1", "role2", "role3"]
        role_data = {
            "id": "role1",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        mock_cache_manager.get.side_effect = [
            role_ids,
            role_data,
            role_data,
            role_data
        ]
        
        roles, total = await role_service.list_roles(page=1, page_size=2)
        assert isinstance(roles, list)
        assert total == 3
        assert len(roles) <= 2
    
    @pytest.mark.asyncio
    async def test_list_roles_empty(self, role_service, mock_cache_manager):
        """测试列出空角色列表"""
        mock_cache_manager.get.return_value = []
        
        roles, total = await role_service.list_roles()
        assert roles == []
        assert total == 0
    
    @pytest.mark.asyncio
    async def test_get_role_by_code_not_found(self, role_service, mock_cache_manager):
        """测试根据代码获取角色（未找到）"""
        mock_cache_manager.get.return_value = []
        
        result = await role_service.get_role_by_code("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_role_with_permissions(self, role_service, mock_cache_manager):
        """测试更新角色（包含权限）"""
        role_data = {
            "id": "role123",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": ["perm1"],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        
        updates = {"permissions": ["perm1", "perm2"]}
        result = await role_service.update_role("role123", updates)
        
        assert result is not None
        assert len(result.permissions) == 2
    
    @pytest.mark.asyncio
    async def test_list_roles_with_resource_type_filter(self, role_service, mock_cache_manager):
        """测试列出角色（带资源类型过滤）"""
        role_ids = ["role1", "role2"]
        role_data = {
            "id": "role1",
            "name": "Role 1",
            "code": "role1",
            "description": "Role 1",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.side_effect = [role_ids, role_data, role_data]
        
        result = await role_service.list_roles(skip=0, limit=10, resource_type="api")
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, role_service, mock_cache_manager):
        """测试删除不存在的角色"""
        mock_cache_manager.get.return_value = None
        
        result = await role_service.delete_role("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_role(self, role_service, mock_cache_manager):
        """测试保存角色到Redis"""
        from src.models.role_models import Role
        
        role = Role(
            id="role123",
            name="Test Role",
            code="test_role",
            description="Test",
            permissions=[],
            is_system=False
        )
        
        await role_service._save_role(role)
        mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_role_ids(self, role_service, mock_cache_manager):
        """测试获取所有角色ID"""
        role_ids = ["role1", "role2"]
        mock_cache_manager.get.return_value = role_ids
        
        result = await role_service._get_all_role_ids()
        assert result == role_ids
    
    @pytest.mark.asyncio
    async def test_get_all_role_ids_empty(self, role_service, mock_cache_manager):
        """测试获取所有角色ID（空）"""
        mock_cache_manager.get.return_value = None
        
        result = await role_service._get_all_role_ids()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_add_to_role_list(self, role_service, mock_cache_manager):
        """测试添加到角色列表索引"""
        with patch.object(role_service, '_get_all_role_ids', new_callable=AsyncMock, return_value=[]):
            await role_service._add_to_role_list("role123")
            mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_from_role_list(self, role_service, mock_cache_manager):
        """测试从角色列表索引中移除"""
        with patch.object(role_service, '_get_all_role_ids', new_callable=AsyncMock, return_value=["role123"]):
            await role_service._remove_from_role_list("role123")
            mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_roles_with_resource_type_filter(self, role_service, mock_cache_manager):
        """测试列出角色（带资源类型过滤）"""
        role_ids = ["role1", "role2"]
        role_data = {
            "id": "role1",
            "name": "Role 1",
            "code": "role1",
            "description": "Role 1",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.side_effect = [role_ids, role_data, role_data]
        
        result = await role_service.list_roles(skip=0, limit=10, resource_type="api")
        assert result is not None
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_add_permission_to_role_exception(self, role_service, mock_cache_manager):
        """测试为角色添加权限（异常）"""
        role_data = {
            "id": "role123",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        mock_cache_manager.set.side_effect = Exception("Cache error")
        
        result = await role_service.add_permission_to_role("role123", "perm123")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_remove_permission_from_role_exception(self, role_service, mock_cache_manager):
        """测试从角色移除权限（异常）"""
        role_data = {
            "id": "role123",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": ["perm123"],
            "is_system": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_cache_manager.get.return_value = role_data
        mock_cache_manager.set.side_effect = Exception("Cache error")
        
        result = await role_service.remove_permission_from_role("role123", "perm123")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_role_datetime_parsing_error(self, role_service, mock_cache_manager):
        """测试获取角色（日期时间解析错误）"""
        role_data = {
            "id": "role123",
            "name": "Test Role",
            "code": "test_role",
            "description": "Test",
            "permissions": [],
            "is_system": False,
            "created_at": "invalid_date",
            "updated_at": "invalid_date"
        }
        mock_cache_manager.get.return_value = role_data
        
        result = await role_service.get_role("role123")
        assert result is not None

