"""
权限服务单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestPermissionService:
    """权限服务测试"""
    
    @pytest.fixture
    def permission_service(self):
        """创建PermissionService实例"""
        from src.services.permission_service import PermissionService
        service = PermissionService()
        return service
    
    @pytest.fixture
    def mock_permission(self):
        """模拟权限对象"""
        from src.models.permission_models import Permission, ResourceType, PermissionType
        
        permission = Permission(
            id="perm123",
            name="Test Permission",
            code="test:read",
            resource_type=ResourceType.API,
            permission_type=PermissionType.READ,
            description="Test permission",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return permission
    
    def test_permission_service_initialization(self, permission_service):
        """测试权限服务初始化"""
        assert permission_service is not None
        assert hasattr(permission_service, '_permissions_cache_key')
        assert hasattr(permission_service, '_permission_key_prefix')
    
    @pytest.mark.asyncio
    async def test_create_permission_success(self, permission_service, mock_permission):
        """测试创建权限成功"""
        permission_data = {
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": "api",
            "permission_type": "read",
            "description": "Test permission"
        }
        
        with patch.object(permission_service, 'get_permission_by_code', new_callable=AsyncMock, return_value=None), \
             patch.object(permission_service, '_save_permission', new_callable=AsyncMock), \
             patch.object(permission_service, '_add_to_permission_list', new_callable=AsyncMock), \
             patch.object(permission_service, '_add_to_code_index', new_callable=AsyncMock), \
             patch('src.services.permission_service.Permission') as mock_perm_class:
            mock_perm_class.return_value = mock_permission
            
            result = await permission_service.create_permission(permission_data)
            
            assert result is not None
            assert result.id == "perm123"
    
    @pytest.mark.asyncio
    async def test_create_permission_duplicate_code(self, permission_service, mock_permission):
        """测试创建权限时代码已存在"""
        permission_data = {
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": "api",
            "permission_type": "read"
        }
        
        with patch.object(permission_service, 'get_permission_by_code', new_callable=AsyncMock, return_value=mock_permission):
            with pytest.raises(ValueError, match="already exists"):
                await permission_service.create_permission(permission_data)
    
    @pytest.mark.asyncio
    async def test_get_permission_success(self, permission_service, mock_permission):
        """测试获取权限成功"""
        permission_data = {
            "id": "perm123",
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": "api",
            "permission_type": "read",
            "description": "Test",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=permission_data)
            
            result = await permission_service.get_permission("perm123")
            
            assert result is not None
            assert result.id == "perm123"
    
    @pytest.mark.asyncio
    async def test_get_permission_not_found(self, permission_service):
        """测试获取不存在的权限"""
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            
            result = await permission_service.get_permission("nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_permission_by_code_success(self, permission_service, mock_permission):
        """测试根据代码获取权限成功"""
        code_index = {"test:read": "perm123"}
        permission_data = {
            "id": "perm123",
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": "api",
            "permission_type": "read",
            "description": "Test",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(side_effect=[code_index, permission_data])
            
            result = await permission_service.get_permission_by_code("test:read")
            
            assert result is not None
            assert result.code == "test:read"
    
    @pytest.mark.asyncio
    async def test_update_permission_success(self, permission_service, mock_permission):
        """测试更新权限成功"""
        updates = {
            "name": "Updated Permission",
            "description": "Updated description"
        }
        
        with patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission), \
             patch.object(permission_service, '_save_permission', new_callable=AsyncMock):
            result = await permission_service.update_permission("perm123", updates)
            
            assert result is not None
            assert result.name == "Updated Permission"
    
    @pytest.mark.asyncio
    async def test_update_permission_not_found(self, permission_service):
        """测试更新不存在的权限"""
        with patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=None):
            result = await permission_service.update_permission("nonexistent", {"name": "Updated"})
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_permission_success(self, permission_service, mock_permission):
        """测试删除权限成功"""
        with patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission), \
             patch.object(permission_service, '_remove_from_permission_list', new_callable=AsyncMock), \
             patch.object(permission_service, '_remove_from_code_index', new_callable=AsyncMock), \
             patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.delete = AsyncMock()
            
            result = await permission_service.delete_permission("perm123")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_permission_not_found(self, permission_service):
        """测试删除不存在的权限"""
        with patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=None):
            result = await permission_service.delete_permission("nonexistent")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_list_permissions_success(self, permission_service, mock_permission):
        """测试列出权限成功"""
        permission_ids = ["perm123", "perm456"]
        permission_data = {
            "id": "perm123",
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": "api",
            "permission_type": "read",
            "description": "Test",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission):
            result = await permission_service.list_permissions(skip=0, limit=10)
            
            assert result is not None
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_check_permission(self, permission_service):
        """测试检查权限"""
        # 这个方法需要根据实际实现来测试
        # 由于check_permission可能依赖其他服务，这里先跳过具体实现
        pass
    
    @pytest.mark.asyncio
    async def test_get_permission_by_code_not_found(self, permission_service):
        """测试根据代码获取不存在的权限"""
        code_index = {}
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=code_index)
            
            result = await permission_service.get_permission_by_code("nonexistent:read")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_permission_code_change(self, permission_service, mock_permission):
        """测试更新权限代码（需要更新索引）"""
        old_code = "test:read"
        new_code = "test:write"
        mock_permission.code = old_code
        
        updates = {
            "code": new_code
        }
        
        with patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission), \
             patch.object(permission_service, '_save_permission', new_callable=AsyncMock), \
             patch.object(permission_service, '_remove_from_code_index', new_callable=AsyncMock), \
             patch.object(permission_service, '_add_to_code_index', new_callable=AsyncMock):
            result = await permission_service.update_permission("perm123", updates)
            
            assert result is not None
            permission_service._remove_from_code_index.assert_called_once_with(old_code)
            permission_service._add_to_code_index.assert_called_once_with(new_code, "perm123")
    
    @pytest.mark.asyncio
    async def test_list_permissions_with_search(self, permission_service, mock_permission):
        """测试带搜索的列出权限"""
        permission_ids = ["perm123", "perm456"]
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission):
            result = await permission_service.list_permissions(skip=0, limit=10, search="Test")
            
            assert result is not None
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_list_permissions_with_resource_type_filter(self, permission_service, mock_permission):
        """测试带资源类型过滤的列出权限"""
        permission_ids = ["perm123", "perm456"]
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission):
            result = await permission_service.list_permissions(skip=0, limit=10, resource_type="api")
            
            assert result is not None
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_list_permissions_empty(self, permission_service):
        """测试列出空权限列表"""
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=[]):
            result = await permission_service.list_permissions(skip=0, limit=10)
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_list_permissions_pagination(self, permission_service, mock_permission):
        """测试权限列表分页"""
        permission_ids = ["perm1", "perm2", "perm3", "perm4", "perm5"]
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission):
            result = await permission_service.list_permissions(skip=2, limit=2)
            
            assert result is not None
            assert isinstance(result, list)
            assert len(result) <= 2
    
    @pytest.mark.asyncio
    async def test_update_permission_with_none_values(self, permission_service, mock_permission):
        """测试更新权限（包含None值）"""
        updates = {
            "name": "Updated Name",
            "description": None  # None值应该被忽略
        }
        
        with patch.object(permission_service, 'get_permission', new_callable=AsyncMock, return_value=mock_permission), \
             patch.object(permission_service, '_save_permission', new_callable=AsyncMock):
            result = await permission_service.update_permission("perm123", updates)
            
            assert result is not None
            assert result.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_save_permission(self, permission_service, mock_permission):
        """测试保存权限到Redis"""
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.set = AsyncMock()
            await permission_service._save_permission(mock_permission)
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_permission_ids(self, permission_service):
        """测试获取所有权限ID"""
        permission_ids = ["perm1", "perm2"]
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=permission_ids)
            result = await permission_service._get_all_permission_ids()
            assert result == permission_ids
    
    @pytest.mark.asyncio
    async def test_get_all_permission_ids_empty(self, permission_service):
        """测试获取所有权限ID（空）"""
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            result = await permission_service._get_all_permission_ids()
            assert result == []
    
    @pytest.mark.asyncio
    async def test_add_to_permission_list(self, permission_service):
        """测试添加到权限列表索引"""
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=[]), \
             patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.set = AsyncMock()
            await permission_service._add_to_permission_list("perm123")
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_to_permission_list_already_exists(self, permission_service):
        """测试添加到权限列表索引（已存在）"""
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=["perm123"]), \
             patch('src.services.permission_service.cache_manager') as mock_cache:
            await permission_service._add_to_permission_list("perm123")
            mock_cache.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_from_permission_list(self, permission_service):
        """测试从权限列表索引中移除"""
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=["perm123"]), \
             patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.set = AsyncMock()
            await permission_service._remove_from_permission_list("perm123")
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_from_permission_list_not_exists(self, permission_service):
        """测试从权限列表索引中移除（不存在）"""
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=[]), \
             patch('src.services.permission_service.cache_manager') as mock_cache:
            await permission_service._remove_from_permission_list("perm123")
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_to_code_index(self, permission_service):
        """测试添加到代码索引"""
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value={})
            mock_cache.set = AsyncMock()
            await permission_service._add_to_code_index("test:read", "perm123")
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_from_code_index(self, permission_service):
        """测试从代码索引中移除"""
        code_index = {"test:read": "perm123"}
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=code_index)
            mock_cache.set = AsyncMock()
            await permission_service._remove_from_code_index("test:read", "perm123")
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_from_code_index_wrong_id(self, permission_service):
        """测试从代码索引中移除（ID不匹配）"""
        code_index = {"test:read": "perm456"}
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=code_index)
            await permission_service._remove_from_code_index("test:read", "perm123")
            mock_cache.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_permission_datetime_parsing_error(self, permission_service):
        """测试获取权限（日期时间解析错误）"""
        from src.models.permission_models import Permission, ResourceType, PermissionType
        
        permission_data = {
            "id": "perm123",
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": ResourceType.USER.value,
            "permission_type": PermissionType.READ.value,
            "description": "Test",
            "created_at": "invalid_date",
            "updated_at": "invalid_date"
        }
        
        with patch('src.services.permission_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=permission_data)
            result = await permission_service.get_permission("perm123")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_list_permissions_with_permission_type_filter(self, permission_service):
        """测试列出权限（带权限类型过滤）"""
        from src.models.permission_models import ResourceType, PermissionType
        
        permission_ids = ["perm1", "perm2"]
        permission_data = {
            "id": "perm1",
            "name": "Permission 1",
            "code": "test:read",
            "resource_type": ResourceType.USER.value,
            "permission_type": PermissionType.READ.value,
            "description": "Permission 1",
            "created_at": None,
            "updated_at": None
        }
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock) as mock_get:
            from src.models.permission_models import Permission
            mock_permission = Permission(**permission_data)
            mock_get.return_value = mock_permission
            
            result = await permission_service.list_permissions(
                page=1,
                page_size=10,
                permission_type=PermissionType.READ
            )
            
            assert result is not None
            assert isinstance(result, tuple)
    
    @pytest.mark.asyncio
    async def test_list_permissions_with_search(self, permission_service):
        """测试列出权限（带搜索）"""
        from src.models.permission_models import ResourceType, PermissionType
        
        permission_ids = ["perm1"]
        permission_data = {
            "id": "perm1",
            "name": "Test Permission",
            "code": "test:read",
            "resource_type": ResourceType.USER.value,
            "permission_type": PermissionType.READ.value,
            "description": "Test description",
            "created_at": None,
            "updated_at": None
        }
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock) as mock_get:
            from src.models.permission_models import Permission
            mock_permission = Permission(**permission_data)
            mock_get.return_value = mock_permission
            
            result = await permission_service.list_permissions(
                page=1,
                page_size=10,
                search="test"
            )
            
            assert result is not None
            assert isinstance(result, tuple)
    
    @pytest.mark.asyncio
    async def test_list_permissions_no_match(self, permission_service):
        """测试列出权限（无匹配）"""
        permission_ids = ["perm1"]
        permission_data = {
            "id": "perm1",
            "name": "Other Permission",
            "code": "other:read",
            "resource_type": "user",
            "permission_type": "read",
            "description": "Other",
            "created_at": None,
            "updated_at": None
        }
        
        with patch.object(permission_service, '_get_all_permission_ids', new_callable=AsyncMock, return_value=permission_ids), \
             patch.object(permission_service, 'get_permission', new_callable=AsyncMock) as mock_get:
            from src.models.permission_models import Permission, ResourceType, PermissionType
            mock_permission = Permission(**permission_data)
            mock_get.return_value = mock_permission
            
            result = await permission_service.list_permissions(
                page=1,
                page_size=10,
                search="nonexistent"
            )
            
            assert result is not None
            permissions, total = result
            assert len(permissions) == 0

