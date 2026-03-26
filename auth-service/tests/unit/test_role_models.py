"""
角色模型测试
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
class TestRoleModels:
    """角色模型测试"""
    
    def test_role_model_creation(self):
        """测试Role模型创建"""
        from src.models.role_models import Role
        
        role = Role(
            id="role123",
            name="Test Role",
            code="test_role"
        )
        
        assert role.id == "role123"
        assert role.name == "Test Role"
        assert role.code == "test_role"
        assert role.description == ""
        assert role.permissions == []
        assert role.is_system is False
    
    def test_role_model_with_all_fields(self):
        """测试Role模型（所有字段）"""
        from src.models.role_models import Role
        
        now = datetime.now()
        role = Role(
            id="role123",
            name="Test Role",
            code="test_role",
            description="Test description",
            permissions=["perm1", "perm2"],
            is_system=True,
            created_at=now,
            updated_at=now
        )
        
        assert role.description == "Test description"
        assert len(role.permissions) == 2
        assert role.is_system is True
        assert role.created_at == now
    
    def test_role_create_model(self):
        """测试RoleCreate模型"""
        from src.models.role_models import RoleCreate
        
        role_create = RoleCreate(
            name="New Role",
            code="new_role",
            description="New role description"
        )
        
        assert role_create.name == "New Role"
        assert role_create.code == "new_role"
        assert role_create.description == "New role description"
        assert role_create.permissions == []
    
    def test_role_update_model(self):
        """测试RoleUpdate模型"""
        from src.models.role_models import RoleUpdate
        
        role_update = RoleUpdate(
            name="Updated Name",
            description="Updated description"
        )
        
        assert role_update.name == "Updated Name"
        assert role_update.description == "Updated description"
        assert role_update.permissions is None
    
    def test_role_response_model(self):
        """测试RoleResponse模型"""
        from src.models.role_models import RoleResponse
        
        role_response = RoleResponse(
            id="role123",
            name="Test Role",
            code="test_role",
            description="Test",
            permissions=["perm1"],
            is_system=False
        )
        
        assert role_response.id == "role123"
        assert role_response.name == "Test Role"
        assert role_response.is_system is False
    
    def test_role_list_response_model(self):
        """测试RoleListResponse模型"""
        from src.models.role_models import RoleListResponse, RoleResponse
        
        roles = [
            RoleResponse(
                id="role1",
                name="Role 1",
                code="role1",
                description="Role 1",
                permissions=[],
                is_system=False
            ),
            RoleResponse(
                id="role2",
                name="Role 2",
                code="role2",
                description="Role 2",
                permissions=[],
                is_system=False
            )
        ]
        
        role_list = RoleListResponse(
            roles=roles,
            total=2,
            page=1,
            page_size=20
        )
        
        assert len(role_list.roles) == 2
        assert role_list.total == 2
        assert role_list.page == 1
        assert role_list.page_size == 20
