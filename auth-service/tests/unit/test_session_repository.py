"""
会话Repository测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestSessionRepository:
    """会话Repository测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        return db
    
    @pytest.fixture
    def session_repo(self, mock_db):
        """创建SessionRepository实例"""
        from src.repositories.session_repository import SessionRepository
        return SessionRepository(mock_db)
    
    def test_session_repository_initialization(self, session_repo, mock_db):
        """测试SessionRepository初始化"""
        assert session_repo is not None
        assert session_repo.session == mock_db
    
    def test_create_session_success(self, session_repo, mock_db):
        """测试创建会话成功"""
        user_id = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        with patch('src.repositories.session_repository.DBUserSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.id = uuid4()
            mock_session_class.return_value = mock_session
            
            result = session_repo.create_session(
                user_id=user_id,
                access_token="access_token",
                refresh_token="refresh_token",
                ip_address="127.0.0.1",
                user_agent="test-agent",
                expires_at=expires_at
            )
            
            assert result is not None
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()
    
    def test_create_session_invalid_user_id(self, session_repo, mock_db):
        """测试创建会话（无效用户ID）"""
        with pytest.raises((ValueError, TypeError)):
            session_repo.create_session(
                user_id="invalid-uuid",
                access_token="access_token"
            )
    
    def test_create_session_exception(self, session_repo, mock_db):
        """测试创建会话（异常）"""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_db.add.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            session_repo.create_session(
                user_id=str(uuid4()),
                access_token="access_token"
            )
        
        mock_db.rollback.assert_called_once()
    
    def test_get_session_by_id_success(self, session_repo, mock_db):
        """测试根据ID获取会话成功"""
        session_id = str(uuid4())
        mock_session = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = session_repo.get_session_by_id(session_id)
        
        assert result == mock_session
    
    def test_get_session_by_id_invalid(self, session_repo, mock_db):
        """测试根据ID获取会话（无效ID）"""
        result = session_repo.get_session_by_id("invalid-uuid")
        assert result is None
    
    def test_get_session_by_token_success(self, session_repo, mock_db):
        """测试根据令牌获取会话成功"""
        mock_session = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = session_repo.get_session_by_token("access_token")
        
        assert result == mock_session
    
    def test_get_session_by_token_not_found(self, session_repo, mock_db):
        """测试根据令牌获取会话（未找到）"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = session_repo.get_session_by_token("nonexistent_token")
        
        assert result is None
    
    def test_get_session_by_token_exception(self, session_repo, mock_db):
        """测试根据令牌获取会话（异常）"""
        from sqlalchemy.exc import SQLAlchemyError
        
        mock_db.query.return_value.filter.side_effect = SQLAlchemyError("Database error")
        
        result = session_repo.get_session_by_token("access_token")
        
        assert result is None
    
    def test_get_user_sessions_active_only(self, session_repo, mock_db):
        """测试获取用户会话（仅活跃）"""
        user_id = str(uuid4())
        mock_sessions = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_sessions
        
        result = session_repo.get_user_sessions(user_id, active_only=True)
        
        assert len(result) == 2
    
    def test_get_user_sessions_all(self, session_repo, mock_db):
        """测试获取用户会话（所有）"""
        user_id = str(uuid4())
        mock_sessions = [MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_sessions
        
        result = session_repo.get_user_sessions(user_id, active_only=False)
        
        assert len(result) == 1
    
    def test_get_user_sessions_invalid_user_id(self, session_repo, mock_db):
        """测试获取用户会话（无效用户ID）"""
        result = session_repo.get_user_sessions("invalid-uuid")
        assert isinstance(result, list)
    
    def test_deactivate_session_success(self, session_repo, mock_db):
        """测试停用会话成功"""
        session_id = str(uuid4())
        mock_session = MagicMock()
        mock_session.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        result = session_repo.deactivate_session(session_id)
        
        assert result is True
        assert mock_session.is_active is False
        mock_db.commit.assert_called_once()
    
    def test_deactivate_session_not_found(self, session_repo, mock_db):
        """测试停用会话（未找到）"""
        session_id = str(uuid4())
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = session_repo.deactivate_session(session_id)
        
        assert result is False
    
    def test_deactivate_session_invalid_id(self, session_repo, mock_db):
        """测试停用会话（无效ID）"""
        result = session_repo.deactivate_session("invalid-uuid")
        assert result is False
    
    def test_delete_expired_sessions(self, session_repo, mock_db):
        """测试删除过期会话"""
        before = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        count = session_repo.delete_expired_sessions(before)
        
        assert isinstance(count, int)
        assert count >= 0
