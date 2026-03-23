"""
用户模型测试
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
class TestUserModels:
    """用户模型测试"""
    
    def test_user_status_enum(self):
        """测试UserStatus枚举"""
        from src.models.user_models import UserStatus
        
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.SUSPENDED == "suspended"
        assert UserStatus.DELETED == "deleted"
    
    def test_user_model_creation(self):
        """测试User模型创建"""
        from src.models.user_models import User, UserStatus
        
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com"
        )
        
        assert user.user_id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == UserStatus.ACTIVE
        assert user.roles == []
        assert user.permissions == []
        assert user.metadata == {}
    
    def test_user_model_with_all_fields(self):
        """测试User模型（所有字段）"""
        from src.models.user_models import User, UserStatus
        
        now = datetime.now()
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            roles=["role1", "role2"],
            permissions=["perm1"],
            status=UserStatus.ACTIVE,
            metadata={"key": "value"},
            last_login_at=now,
            created_at=now,
            updated_at=now
        )
        
        assert user.display_name == "Test User"
        assert len(user.roles) == 2
        assert len(user.permissions) == 1
        assert user.metadata == {"key": "value"}
        assert user.last_login_at == now
    
    def test_user_create_model(self):
        """测试UserCreate模型"""
        from src.models.user_models import UserCreate, UserStatus
        
        user_create = UserCreate(
            username="newuser",
            email="newuser@example.com",
            display_name="New User"
        )
        
        assert user_create.username == "newuser"
        assert user_create.email == "newuser@example.com"
        assert user_create.display_name == "New User"
        assert user_create.status == UserStatus.ACTIVE
        assert user_create.roles == []
    
    def test_user_update_model(self):
        """测试UserUpdate模型"""
        from src.models.user_models import UserUpdate, UserStatus
        
        user_update = UserUpdate(
            display_name="Updated Name",
            status=UserStatus.INACTIVE
        )
        
        assert user_update.display_name == "Updated Name"
        assert user_update.status == UserStatus.INACTIVE
        assert user_update.username is None
        assert user_update.email is None
    
    def test_user_response_model(self):
        """测试UserResponse模型"""
        from src.models.user_models import UserResponse
        
        user_response = UserResponse(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["role1"],
            permissions=["perm1"],
            status="active"
        )
        
        assert user_response.user_id == "user123"
        assert user_response.username == "testuser"
        assert user_response.status == "active"
    
    def test_user_detail_response_model(self):
        """测试UserDetailResponse模型"""
        from src.models.user_models import UserDetailResponse
        
        user_detail = UserDetailResponse(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            roles=["role1"],
            permissions=["perm1"],
            status="active",
            metadata={"key": "value"},
            role_details=[{"id": "role1", "name": "Role 1"}],
            permission_details=[{"id": "perm1", "name": "Permission 1"}]
        )
        
        assert user_detail.metadata == {"key": "value"}
        assert len(user_detail.role_details) == 1
        assert len(user_detail.permission_details) == 1
    
    def test_user_list_response_model(self):
        """测试UserListResponse模型"""
        from src.models.user_models import UserListResponse, UserResponse
        
        users = [
            UserResponse(
                user_id="user1",
                username="user1",
                email="user1@example.com",
                roles=[],
                permissions=[],
                status="active"
            ),
            UserResponse(
                user_id="user2",
                username="user2",
                email="user2@example.com",
                roles=[],
                permissions=[],
                status="active"
            )
        ]
        
        user_list = UserListResponse(
            users=users,
            total=2,
            page=1,
            page_size=20
        )
        
        assert len(user_list.users) == 2
        assert user_list.total == 2
        assert user_list.page == 1
        assert user_list.page_size == 20
    
    def test_user_search_params_model(self):
        """测试UserSearchParams模型"""
        from src.models.user_models import UserSearchParams, UserStatus
        
        search_params = UserSearchParams(
            page=2,
            page_size=50,
            search="test",
            status=UserStatus.ACTIVE,
            role="admin"
        )
        
        assert search_params.page == 2
        assert search_params.page_size == 50
        assert search_params.search == "test"
        assert search_params.status == UserStatus.ACTIVE
        assert search_params.role == "admin"
    
    def test_user_search_params_defaults(self):
        """测试UserSearchParams默认值"""
        from src.models.user_models import UserSearchParams
        
        search_params = UserSearchParams()
        
        assert search_params.page == 1
        assert search_params.page_size == 20
        assert search_params.search is None
        assert search_params.status is None
        assert search_params.role is None
