"""
数据库集成测试
"""
import pytest
from database.src.core.database import DatabaseManager
from database.src.models.user_models import User


@pytest.mark.integration
class TestDatabaseIntegration:
    """数据库集成测试"""
    
    def test_database_operations(self, db_session):
        """测试数据库基本操作"""
        # 创建
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed"
        )
        db_session.add(user)
        db_session.commit()
        
        # 读取
        found_user = db_session.query(User).filter_by(username="testuser").first()
        assert found_user is not None
        assert found_user.email == "test@example.com"
        
        # 更新
        found_user.email = "updated@example.com"
        db_session.commit()
        
        updated_user = db_session.query(User).filter_by(username="testuser").first()
        assert updated_user.email == "updated@example.com"
        
        # 删除
        db_session.delete(updated_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter_by(username="testuser").first()
        assert deleted_user is None

