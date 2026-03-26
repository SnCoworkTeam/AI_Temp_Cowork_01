"""
令牌Repository测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestTokenRepository:
    """令牌Repository测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        redis = MagicMock()
        redis.exists = MagicMock(return_value=False)
        redis.set = MagicMock(return_value=True)
        redis.get = MagicMock(return_value=None)
        redis.delete = MagicMock(return_value=True)
        return redis
    
    @pytest.fixture
    def token_repo(self, mock_db):
        """创建TokenRepository实例"""
        from src.repositories.token_repository import TokenRepository
        return TokenRepository(mock_db)
    
    def test_token_repository_initialization(self, token_repo, mock_db):
        """测试TokenRepository初始化"""
        assert token_repo is not None
        assert token_repo.session == mock_db
    
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
    
    def test_add_to_blacklist_error(self, token_repo, mock_redis):
        """测试添加令牌到黑名单时出错"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_redis.set.side_effect = Exception("Redis error")
        result = token_repo.add_to_blacklist("test_token", expires_at, mock_redis)
        assert result is False
    
    def test_remove_from_blacklist_success(self, token_repo, mock_redis):
        """测试从黑名单移除令牌成功"""
        result = token_repo.remove_from_blacklist("test_token", mock_redis)
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_remove_from_blacklist_error(self, token_repo, mock_redis):
        """测试从黑名单移除令牌时出错"""
        mock_redis.delete.side_effect = Exception("Redis error")
        result = token_repo.remove_from_blacklist("test_token", mock_redis)
        assert result is False
    
    def test_get_token_info_none(self, token_repo, mock_redis):
        """测试获取不存在的令牌信息"""
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result is None
    
    def test_get_token_info_exists(self, token_repo, mock_redis):
        """测试获取存在的令牌信息"""
        token_info = {"user_id": "123", "username": "test"}
        mock_redis.get.return_value = json.dumps(token_info)
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result == token_info
    
    def test_get_token_info_invalid_json(self, token_repo, mock_redis):
        """测试获取无效JSON的令牌信息"""
        mock_redis.get.return_value = "invalid json{"
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result is None
    
    def test_get_token_info_error(self, token_repo, mock_redis):
        """测试获取令牌信息时出错"""
        mock_redis.get.side_effect = Exception("Redis error")
        result = token_repo.get_token_info("test_token", mock_redis)
        assert result is None
    
    def test_save_token_info_success(self, token_repo, mock_redis):
        """测试保存令牌信息成功"""
        token_info = {"user_id": "123", "username": "test"}
        result = token_repo.save_token_info("test_token", token_info, 3600, mock_redis)
        assert result is True
        mock_redis.set.assert_called_once()
    
    def test_save_token_info_error(self, token_repo, mock_redis):
        """测试保存令牌信息时出错"""
        token_info = {"user_id": "123", "username": "test"}
        mock_redis.set.side_effect = Exception("Redis error")
        result = token_repo.save_token_info("test_token", token_info, 3600, mock_redis)
        assert result is False
