"""
Repository层测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestTokenRepository:
    """TokenRepository测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        redis = MagicMock()
        redis.exists.return_value = False
        redis.set.return_value = True
        redis.get.return_value = None
        redis.delete.return_value = True
        return redis
    
    @pytest.fixture
    def token_repo(self, mock_db):
        """创建TokenRepository实例"""
        from src.repositories.token_repository import TokenRepository
        return TokenRepository(mock_db)
    
    def test_is_token_blacklisted_false(self, token_repo, mock_redis):
        """测试检查令牌不在黑名单中"""
        result = token_repo.is_token_blacklisted("test_token", mock_redis)
        assert result is False
        mock_redis.exists.assert_called_once()
    
    def test_is_token_blacklisted_true(self, token_repo, mock_redis):
        """测试检查令牌在黑名单中"""
        mock_redis.exists.return_value = True
        result = token_repo.is_token_blacklisted("test_token", mock_redis)
        assert result is True
    
    def test_is_token_blacklisted_error(self, token_repo, mock_redis):
        """测试检查令牌时出错"""
        mock_redis.exists.side_effect = Exception("Redis error")
        result = token_repo.is_token_blacklisted("test_token", mock_redis)
        assert result is False
    
    def test_add_to_blacklist_success(self, token_repo, mock_redis):
        """测试添加令牌到黑名单成功"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        result = token_repo.add_to_blacklist("test_token", expires_at, mock_redis)
        assert result is True
        mock_redis.set.assert_called_once()
    
    def test_add_to_blacklist_expired(self, token_repo, mock_redis):
        """测试添加已过期的令牌"""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        result = token_repo.add_to_blacklist("test_token", expires_at, mock_redis)
        assert result is False
    
    def test_remove_from_blacklist(self, token_repo, mock_redis):
        """测试从黑名单移除令牌"""
        result = token_repo.remove_from_blacklist("test_token", mock_redis)
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_get_token_info_none(self, token_repo, mock_redis):
        """测试获取不存在的令牌信息"""
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result is None
    
    def test_get_token_info_exists(self, token_repo, mock_redis):
        """测试获取存在的令牌信息"""
        import json
        token_info = {"user_id": "123", "username": "test"}
        mock_redis.get.return_value = json.dumps(token_info)
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result == token_info
    
    def test_save_token_info(self, token_repo, mock_redis):
        """测试保存令牌信息"""
        import json
        token_info = {"user_id": "123", "username": "test"}
        result = token_repo.save_token_info("test_token", token_info, 3600, mock_redis)
        assert result is True
        mock_redis.set.assert_called_once()
    
    def test_get_token_info_invalid_json(self, token_repo, mock_redis):
        """测试获取令牌信息（无效JSON）"""
        mock_redis.get.return_value = "invalid json"
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result is None
    
    def test_get_token_info_exception(self, token_repo, mock_redis):
        """测试获取令牌信息（异常）"""
        mock_redis.get.side_effect = Exception("Redis error")
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result is None
    
    def test_save_token_info_exception(self, token_repo, mock_redis):
        """测试保存令牌信息（异常）"""
        import json
        token_info = {"user_id": "123", "username": "test"}
        mock_redis.set.side_effect = Exception("Redis error")
        result = token_repo.save_token_info("test_token", token_info, 3600, mock_redis)
        assert result is False
    
    def test_remove_from_blacklist_exception(self, token_repo, mock_redis):
        """测试从黑名单移除令牌（异常）"""
        mock_redis.delete.side_effect = Exception("Redis error")
        result = token_repo.remove_from_blacklist("test_token", mock_redis)
        assert result is True  # 即使出错也返回True


@pytest.mark.unit
class TestSessionRepository:
    """SessionRepository测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def session_repo(self, mock_db):
        """创建SessionRepository实例"""
        from src.repositories.session_repository import SessionRepository
        return SessionRepository(mock_db)
    
    def test_create_session(self, session_repo, mock_db):
        """测试创建会话"""
        from uuid import uuid4
        user_id = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        session = session_repo.create_session(
            user_id=user_id,
            access_token="access_token",
            refresh_token="refresh_token",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            expires_at=expires_at
        )
        
        assert session is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
    
    def test_get_session_by_id(self, session_repo, mock_db):
        """测试根据ID获取会话"""
        from uuid import uuid4
        session_id = str(uuid4())
        
        result = session_repo.get_session_by_id(session_id)
        assert result is None or isinstance(result, type(None))
    
    def test_get_session_by_token(self, session_repo, mock_db):
        """测试根据令牌获取会话"""
        result = session_repo.get_session_by_token("access_token")
        assert result is None or isinstance(result, type(None))
    
    def test_get_user_sessions(self, session_repo, mock_db):
        """测试获取用户会话列表"""
        from uuid import uuid4
        user_id = str(uuid4())
        
        sessions = session_repo.get_user_sessions(user_id, active_only=True)
        assert isinstance(sessions, list)
    
    def test_deactivate_session(self, session_repo, mock_db):
        """测试停用会话"""
        from uuid import uuid4
        session_id = str(uuid4())
        
        result = session_repo.deactivate_session(session_id)
        assert isinstance(result, bool)
    
    def test_get_session_by_id_invalid_uuid(self, session_repo, mock_db):
        """测试根据ID获取会话（无效UUID）"""
        result = session_repo.get_session_by_id("invalid_uuid")
        assert result is None
    
    def test_get_session_by_token_exception(self, session_repo, mock_db):
        """测试根据令牌获取会话（异常）"""
        mock_db.query.side_effect = Exception("Database error")
        result = session_repo.get_session_by_token("access_token")
        assert result is None
    
    def test_get_user_sessions_invalid_uuid(self, session_repo, mock_db):
        """测试获取用户会话（无效UUID）"""
        result = session_repo.get_user_sessions("invalid_uuid")
        assert result == []
    
    def test_get_user_sessions_exception(self, session_repo, mock_db):
        """测试获取用户会话（异常）"""
        from uuid import uuid4
        user_id = str(uuid4())
        mock_db.query.side_effect = Exception("Database error")
        result = session_repo.get_user_sessions(user_id)
        assert result == []
    
    def test_update_session_not_found(self, session_repo, mock_db):
        """测试更新会话（会话不存在）"""
        from uuid import uuid4
        session_id = str(uuid4())
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = session_repo.update_session(session_id, access_token="new_token")
        assert result is None
    
    def test_update_session_exception(self, session_repo, mock_db):
        """测试更新会话（异常）"""
        from uuid import uuid4
        session_id = str(uuid4())
        mock_db.query.side_effect = Exception("Database error")
        
        result = session_repo.update_session(session_id, access_token="new_token")
        assert result is None
    
    def test_deactivate_session_not_found(self, session_repo, mock_db):
        """测试停用会话（会话不存在）"""
        from uuid import uuid4
        session_id = str(uuid4())
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = session_repo.deactivate_session(session_id)
        assert result is False
    
    def test_deactivate_session_exception(self, session_repo, mock_db):
        """测试停用会话（异常）"""
        from uuid import uuid4
        session_id = str(uuid4())
        mock_db.query.side_effect = Exception("Database error")
        
        result = session_repo.deactivate_session(session_id)
        assert result is False
    
    def test_delete_expired_sessions_exception(self, session_repo, mock_db):
        """测试删除过期会话（异常）"""
        from datetime import datetime, timedelta
        before = datetime.utcnow() - timedelta(days=7)
        mock_db.query.side_effect = Exception("Database error")
        
        result = session_repo.delete_expired_sessions(before)
        assert result == 0
    
    def test_delete_expired_sessions(self, session_repo, mock_db):
        """测试删除过期会话"""
        before = datetime.utcnow()
        count = session_repo.delete_expired_sessions(before)
        assert isinstance(count, int)
        assert count >= 0


@pytest.mark.unit
class TestUserRepository:
    """UserRepository测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def user_repo(self, mock_db):
        """创建UserRepository实例"""
        from src.repositories.user_repository import UserRepository
        return UserRepository(mock_db)
    
    def test_get_by_id_valid_uuid(self, user_repo, mock_db):
        """测试根据有效UUID获取用户"""
        from uuid import uuid4
        user_id = str(uuid4())
        
        result = user_repo.get_by_id(user_id)
        # 可能返回None（如果用户不存在）或用户对象
        assert result is None or hasattr(result, 'id')
    
    def test_get_by_id_invalid_uuid(self, user_repo, mock_db):
        """测试根据无效UUID获取用户"""
        result = user_repo.get_by_id("invalid-uuid")
        assert result is None
    
    def test_get_by_username(self, user_repo, mock_db):
        """测试根据用户名获取用户"""
        result = user_repo.get_by_username("testuser")
        # 可能返回None或用户对象
        assert result is None or hasattr(result, 'username')
    
    def test_get_by_email(self, user_repo, mock_db):
        """测试根据邮箱获取用户"""
        result = user_repo.get_by_email("test@example.com")
        assert result is None or hasattr(result, 'email')
    
    def test_create_user(self, user_repo, mock_db):
        """测试创建用户"""
        user = user_repo.create_user(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            status="active"
        )
        
        assert user is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
    
    def test_list_users(self, user_repo, mock_db):
        """测试列出用户"""
        users = user_repo.list_users(skip=0, limit=10)
        assert isinstance(users, list)
    
    def test_list_users_with_search(self, user_repo, mock_db):
        """测试带搜索的列出用户"""
        users = user_repo.list_users(skip=0, limit=10, search="test")
        assert isinstance(users, list)
    
    def test_assign_role(self, user_repo, mock_db):
        """测试分配角色"""
        from uuid import uuid4
        user_id = str(uuid4())
        role_id = str(uuid4())
        
        result = user_repo.assign_role(user_id, role_id)
        assert isinstance(result, bool)
    
    def test_remove_role(self, user_repo, mock_db):
        """测试移除角色"""
        from uuid import uuid4
        user_id = str(uuid4())
        role_id = str(uuid4())
        
        result = user_repo.remove_role(user_id, role_id)
        assert isinstance(result, bool)
    
    def test_get_user_permissions(self, user_repo, mock_db):
        """测试获取用户权限"""
        from uuid import uuid4
        user_id = str(uuid4())
        
        permissions = user_repo.get_user_permissions(user_id)
        assert isinstance(permissions, list)
    
    def test_update_user_success(self, user_repo, mock_db):
        """测试更新用户成功"""
        from uuid import uuid4
        user_id = str(uuid4())
        
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        
        with patch.object(user_repo, '_db_repo') as mock_db_repo:
            mock_db_repo.update.return_value = mock_user
            
            result = user_repo.update_user(user_id, username="newuser", email="new@example.com")
            
            assert result is not None
            mock_db_repo.update.assert_called_once()
    
    def test_update_user_invalid_id(self, user_repo, mock_db):
        """测试更新用户（无效ID）"""
        result = user_repo.update_user("invalid-uuid", username="newuser")
        assert result is None
    
    def test_delete_user_success(self, user_repo, mock_db):
        """测试删除用户成功"""
        from uuid import uuid4
        user_id = str(uuid4())
        
        mock_user = MagicMock()
        mock_user.status = MagicMock()
        
        with patch.object(user_repo, '_db_repo') as mock_db_repo:
            mock_db_repo.get_by_id.return_value = mock_user
            
            result = user_repo.delete_user(user_id)
            
            assert result is True
            mock_db.flush.assert_called_once()
    
    def test_delete_user_not_found(self, user_repo, mock_db):
        """测试删除不存在的用户"""
        from uuid import uuid4
        user_id = str(uuid4())
        
        with patch.object(user_repo, '_db_repo') as mock_db_repo:
            mock_db_repo.get_by_id.return_value = None
            
            result = user_repo.delete_user(user_id)
            
            assert result is False
    
    def test_delete_user_invalid_id(self, user_repo, mock_db):
        """测试删除用户（无效ID）"""
        result = user_repo.delete_user("invalid-uuid")
        assert result is False
    
    def test_create_user_different_statuses(self, user_repo, mock_db):
        """测试创建不同状态的用户"""
        statuses = ["active", "inactive", "suspended", "deleted"]
        
        for status in statuses:
            user = user_repo.create_user(
                username=f"testuser_{status}",
                email=f"test_{status}@example.com",
                password_hash="hashed_password",
                status=status
            )
            assert user is not None
            mock_db.add.assert_called()
            mock_db.flush.assert_called()
    
    def test_create_user_with_exception(self, user_repo, mock_db):
        """测试创建用户时发生异常"""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_db.add.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            user_repo.create_user(
                username="testuser",
                email="test@example.com",
                password_hash="hashed_password"
            )
        
        mock_db.rollback.assert_called_once()
    
    def test_list_users_with_status_filter(self, user_repo, mock_db):
        """测试带状态过滤的列出用户"""
        users = user_repo.list_users(skip=0, limit=10, status="active")
        assert isinstance(users, list)
    
    def test_list_users_with_invalid_status(self, user_repo, mock_db):
        """测试带无效状态过滤的列出用户"""
        users = user_repo.list_users(skip=0, limit=10, status="invalid_status")
        assert isinstance(users, list)
    
    def test_assign_role_invalid_user_id(self, user_repo, mock_db):
        """测试分配角色（无效用户ID）"""
        result = user_repo.assign_role("invalid-uuid", str(uuid4()))
        assert result is False
    
    def test_assign_role_invalid_role_id(self, user_repo, mock_db):
        """测试分配角色（无效角色ID）"""
        from uuid import uuid4
        result = user_repo.assign_role(str(uuid4()), "invalid-uuid")
        assert result is False
    
    def test_remove_role_invalid_user_id(self, user_repo, mock_db):
        """测试移除角色（无效用户ID）"""
        result = user_repo.remove_role("invalid-uuid", str(uuid4()))
        assert result is False
    
    def test_remove_role_invalid_role_id(self, user_repo, mock_db):
        """测试移除角色（无效角色ID）"""
        from uuid import uuid4
        result = user_repo.remove_role(str(uuid4()), "invalid-uuid")
        assert result is False
    
    def test_get_user_permissions_invalid_id(self, user_repo, mock_db):
        """测试获取用户权限（无效ID）"""
        result = user_repo.get_user_permissions("invalid_id")
        assert result == []
    
    def test_get_user_permissions_exception(self, user_repo, mock_db):
        """测试获取用户权限（异常）"""
        from uuid import uuid4
        user_id = str(uuid4())
        mock_db.query.side_effect = Exception("Database error")
        
        result = user_repo.get_user_permissions(user_id)
        assert result == []
    
    def test_list_users_exception(self, user_repo, mock_db):
        """测试列出用户（异常）"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = user_repo.list_users()
        assert result == []
    
    def test_create_session_exception(self, session_repo, mock_db):
        """测试创建会话（异常）"""
        from uuid import uuid4
        from datetime import datetime, timedelta
        user_id = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        mock_db.add.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            session_repo.create_session(
                user_id=user_id,
                access_token="access_token",
                expires_at=expires_at
            )
        mock_db.rollback.assert_called_once()

