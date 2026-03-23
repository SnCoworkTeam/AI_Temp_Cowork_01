"""
权限模型测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestPermissionModels:
    """权限模型测试"""
    
    def test_permission_type_enum(self):
        """测试PermissionType枚举"""
        from src.models.permission_models import PermissionType
        
        assert PermissionType.READ == "read"
        assert PermissionType.WRITE == "write"
        assert PermissionType.DELETE == "delete"
        assert PermissionType.EXECUTE == "execute"
        assert PermissionType.ADMIN == "admin"
    
    def test_resource_type_enum(self):
        """测试ResourceType枚举"""
        from src.models.permission_models import ResourceType
        
        assert ResourceType.USER == "user"
        assert ResourceType.WORKFLOW == "workflow"
        assert ResourceType.TOOL == "tool"
        assert ResourceType.ADMIN == "admin"
        assert ResourceType.SYSTEM == "system"
    
    def test_permission_model_creation(self):
        """测试Permission模型创建"""
        from src.models.permission_models import Permission, ResourceType, PermissionType
        
        permission = Permission(
            id="perm123",
            name="Test Permission",
            code="test:read",
            resource_type=ResourceType.USER,
            permission_type=PermissionType.READ
        )
        
        assert permission.id == "perm123"
        assert permission.name == "Test Permission"
        assert permission.code == "test:read"
        assert permission.resource_type == ResourceType.USER
        assert permission.permission_type == PermissionType.READ
        assert permission.description == ""
    
    def test_permission_model_with_all_fields(self):
        """测试Permission模型（所有字段）"""
        from src.models.permission_models import Permission, ResourceType, PermissionType
        
        now = datetime.now()
        permission = Permission(
            id="perm123",
            name="Test Permission",
            code="test:read",
            resource_type=ResourceType.WORKFLOW,
            permission_type=PermissionType.EXECUTE,
            description="Test description",
            created_at=now,
            updated_at=now
        )
        
        assert permission.description == "Test description"
        assert permission.resource_type == ResourceType.WORKFLOW
        assert permission.permission_type == PermissionType.EXECUTE
        assert permission.created_at == now
    
    def test_permission_create_model(self):
        """测试PermissionCreate模型"""
        from src.models.permission_models import PermissionCreate, ResourceType, PermissionType
        
        permission_create = PermissionCreate(
            name="New Permission",
            code="new:write",
            resource_type=ResourceType.TOOL,
            permission_type=PermissionType.WRITE,
            description="New permission description"
        )
        
        assert permission_create.name == "New Permission"
        assert permission_create.code == "new:write"
        assert permission_create.resource_type == ResourceType.TOOL
        assert permission_create.permission_type == PermissionType.WRITE
    
    def test_permission_update_model(self):
        """测试PermissionUpdate模型"""
        from src.models.permission_models import PermissionUpdate
        
        permission_update = PermissionUpdate(
            name="Updated Name",
            description="Updated description"
        )
        
        assert permission_update.name == "Updated Name"
        assert permission_update.description == "Updated description"
    
    def test_permission_response_model(self):
        """测试PermissionResponse模型"""
        from src.models.permission_models import PermissionResponse
        
        permission_response = PermissionResponse(
            id="perm123",
            name="Test Permission",
            code="test:read",
            resource_type="user",
            permission_type="read",
            description="Test"
        )
        
        assert permission_response.id == "perm123"
        assert permission_response.name == "Test Permission"
        assert permission_response.code == "test:read"
    
    def test_permission_list_response_model(self):
        """测试PermissionListResponse模型"""
        from src.models.permission_models import PermissionListResponse, PermissionResponse
        
        permissions = [
            PermissionResponse(
                id="perm1",
                name="Permission 1",
                code="test:read",
                resource_type="user",
                permission_type="read",
                description="Permission 1"
            ),
            PermissionResponse(
                id="perm2",
                name="Permission 2",
                code="test:write",
                resource_type="user",
                permission_type="write",
                description="Permission 2"
            )
        ]
        
        permission_list = PermissionListResponse(
            permissions=permissions,
            total=2,
            page=1,
            page_size=20
        )
        
        assert len(permission_list.permissions) == 2
        assert permission_list.total == 2
        assert permission_list.page == 1
        assert permission_list.page_size == 20
