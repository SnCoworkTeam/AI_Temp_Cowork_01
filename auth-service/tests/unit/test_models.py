"""
Auth Service 模型单元测试
"""
import pytest
from datetime import datetime
from uuid import uuid4


@pytest.mark.unit
class TestUserModels:
    """用户模型测试"""
    
    def test_user_creation(self):
        """测试用户创建"""
        from database.src.models.user_models import User
        
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            created_at=datetime.utcnow()
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_user_password_hashing(self):
        """测试密码哈希"""
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "test_password"
        hashed = pwd_context.hash(password)
        
        # 验证密码
        assert pwd_context.verify(password, hashed)
        assert not pwd_context.verify("wrong_password", hashed)


@pytest.mark.unit
class TestRoleModels:
    """角色模型测试"""
    
    def test_role_creation(self):
        """测试角色创建"""
        try:
            from database.src.models.role_models import Role
            
            role = Role(
                id=uuid4(),
                name="admin",
                description="Administrator role",
                created_at=datetime.utcnow()
            )
            
            assert role.name == "admin"
            assert role.description == "Administrator role"
        except ImportError:
            pytest.skip("Role model not available")







