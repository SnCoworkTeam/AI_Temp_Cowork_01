"""
用户服务单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from uuid import uuid4

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestUserService:
    """用户服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    @pytest.fixture
    def mock_user_repo(self):
        """模拟用户仓库"""
        repo = MagicMock()
        return repo
    
    @pytest.fixture
    def user_service(self, mock_db, mock_user_repo):
        """创建UserService实例"""
        with patch('src.services.user_service.UserRepository', return_value=mock_user_repo):
            from src.services.user_service import UserService
            service = UserService(mock_db)
            service.user_repo = mock_user_repo
            return service
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户对象"""
        user = MagicMock()
        user.id = uuid4()
        user.username = "testuser"
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.status = MagicMock()
        user.status.value = "active"
        user.created_at = None
        user.updated_at = None
        user.roles = []
        return user
    
    def test_user_service_initialization(self, user_service, mock_db):
        """测试用户服务初始化"""
        assert user_service is not None
        assert user_service.db == mock_db
        assert user_service.user_repo is not None
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试创建用户成功"""
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create_user.return_value = mock_user
        mock_db.commit = MagicMock()
        
        with patch.object(user_service, '_cache_user_info', new_callable=AsyncMock):
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "full_name": "Test User",
                "status": "active"
            }
            
            result, error = await user_service.create_user(user_data)
            
            assert error is None
            assert result is not None
            assert "username" in result
            mock_user_repo.get_by_username.assert_called_once_with("testuser")
            mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service, mock_user_repo, mock_user):
        """测试创建用户时用户名已存在"""
        mock_user_repo.get_by_username.return_value = mock_user
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        
        result, error = await user_service.create_user(user_data)
        
        assert result is None
        assert error == "用户名已存在"
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_user_repo, mock_user):
        """测试创建用户时邮箱已存在"""
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = mock_user
        
        user_data = {
            "username": "newuser",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        
        result, error = await user_service.create_user(user_data)
        
        assert result is None
        assert error == "邮箱已被注册"
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service, mock_user_repo, mock_user):
        """测试获取用户成功"""
        mock_user_repo.get_by_id.return_value = mock_user
        
        with patch.object(user_service, '_get_cached_user', new_callable=AsyncMock, return_value=None), \
             patch.object(user_service, '_cache_user_info', new_callable=AsyncMock):
            
            result = await user_service.get_user(str(mock_user.id))
            
            assert result is not None
            assert result["username"] == "testuser"
            mock_user_repo.get_by_id.assert_called_once_with(str(mock_user.id))
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service, mock_user_repo):
        """测试获取不存在的用户"""
        mock_user_repo.get_by_id.return_value = None
        
        with patch.object(user_service, '_get_cached_user', new_callable=AsyncMock, return_value=None):
            result = await user_service.get_user("nonexistent_id")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_from_cache(self, user_service, mock_user_repo):
        """测试从缓存获取用户"""
        cached_user = {
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com"
        }
        
        with patch.object(user_service, '_get_cached_user', new_callable=AsyncMock, return_value=cached_user):
            result = await user_service.get_user("user123")
            
            assert result == cached_user
            mock_user_repo.get_by_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, user_service, mock_user_repo, mock_user):
        """测试根据用户名获取用户成功"""
        mock_user_repo.get_by_username.return_value = mock_user
        
        with patch.object(user_service, '_cache_user_info', new_callable=AsyncMock):
            result = await user_service.get_user_by_username("testuser")
            
            assert result is not None
            assert result["username"] == "testuser"
            mock_user_repo.get_by_username.assert_called_once_with("testuser")
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_user_repo, mock_user):
        """测试根据邮箱获取用户成功"""
        mock_user_repo.get_by_email.return_value = mock_user
        
        with patch.object(user_service, '_cache_user_info', new_callable=AsyncMock):
            result = await user_service.get_user_by_email("test@example.com")
            
            assert result is not None
            assert result["email"] == "test@example.com"
            mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试更新用户成功"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update_user.return_value = mock_user
        mock_db.commit = MagicMock()
        
        with patch.object(user_service, '_cache_user_info', new_callable=AsyncMock), \
             patch.object(user_service, '_clear_user_cache', new_callable=AsyncMock):
            
            update_data = {
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
            
            result, error = await user_service.update_user(str(mock_user.id), update_data)
            
            assert error is None
            assert result is not None
            mock_user_repo.update_user.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试删除用户成功"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.delete_user.return_value = True
        mock_db.commit = MagicMock()
        
        with patch.object(user_service, '_clear_user_cache', new_callable=AsyncMock):
            result, error = await user_service.delete_user(str(mock_user.id))
            
            assert error is None
            assert result is True
            mock_user_repo.delete_user.assert_called_once_with(str(mock_user.id))
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, user_service, mock_user_repo, mock_user):
        """测试列出用户成功"""
        mock_user_repo.list_users.return_value = [mock_user]
        
        with patch.object(user_service, '_get_cached_user_list', new_callable=AsyncMock, return_value=None), \
             patch.object(user_service, '_cache_user_list', new_callable=AsyncMock):
            
            result = await user_service.list_users(skip=0, limit=10)
            
            assert result is not None
            assert len(result) > 0
            mock_user_repo.list_users.assert_called()
    
    @pytest.mark.asyncio
    async def test_assign_role_success(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试分配角色成功"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.assign_role.return_value = True
        mock_db.commit = MagicMock()
        
        with patch.object(user_service, '_clear_user_cache', new_callable=AsyncMock):
            result, error = await user_service.assign_role(str(mock_user.id), "role123")
            
            assert error is None
            assert result is True
            mock_user_repo.assign_role.assert_called_once_with(str(mock_user.id), "role123")
    
    @pytest.mark.asyncio
    async def test_remove_role_success(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试移除角色成功"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.remove_role.return_value = True
        mock_db.commit = MagicMock()
        
        with patch.object(user_service, '_clear_user_cache', new_callable=AsyncMock):
            result, error = await user_service.remove_role(str(mock_user.id), "role123")
            
            assert error is None
            assert result is True
            mock_user_repo.remove_role.assert_called_once_with(str(mock_user.id), "role123")
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_service, mock_user_repo):
        """测试根据邮箱获取用户（未找到）"""
        mock_user_repo.get_by_email.return_value = None
        
        result = await user_service.get_user_by_email("nonexistent@example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, user_service, mock_user_repo):
        """测试根据用户名获取用户（未找到）"""
        mock_user_repo.get_by_username.return_value = None
        
        result = await user_service.get_user_by_username("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_users_empty(self, user_service, mock_user_repo):
        """测试列出用户（空列表）"""
        mock_user_repo.list_users.return_value = ([], 0)
        
        users, total = await user_service.list_users()
        
        assert users == []
        assert total == 0
    
    @pytest.mark.asyncio
    async def test_assign_role_already_has_role(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试分配角色（用户已有该角色）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.assign_role.return_value = True
        
        with patch.object(user_service, '_clear_user_cache', new_callable=AsyncMock):
            result, error = await user_service.assign_role(str(mock_user.id), "role123")
            
            assert error is None
            assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_role_not_has_role(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试移除角色（用户没有该角色）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.remove_role.return_value = False
        
        result, error = await user_service.remove_role(str(mock_user.id), "role123")
        
        assert result is False
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, user_service, mock_user_repo, mock_user):
        """测试列出用户（分页）"""
        mock_user_repo.list_users.return_value = ([mock_user] * 10, 50)
        
        users, total = await user_service.list_users(page=2, page_size=10)
        
        assert users is not None
        assert total >= 0
    
    @pytest.mark.asyncio
    async def test_list_users_with_role_filter(self, user_service, mock_user_repo, mock_user):
        """测试列出用户（角色过滤）"""
        mock_user_repo.list_users.return_value = ([mock_user], 1)
        
        users, total = await user_service.list_users(role="admin")
        
        assert users is not None
        assert total >= 0
    
    @pytest.mark.asyncio
    async def test_assign_role_role_not_found(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试分配角色（角色不存在）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.assign_role.return_value = False
        
        result, error = await user_service.assign_role(str(mock_user.id), "nonexistent_role")
        
        assert result is False
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_remove_role_role_not_found(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试移除角色（角色不存在）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.remove_role.return_value = False
        
        result, error = await user_service.remove_role(str(mock_user.id), "nonexistent_role")
        
        assert result is False
        assert error is not None
    
    @pytest.mark.asyncio
    async def test_get_user_by_username_exception(self, user_service, mock_user_repo):
        """测试根据用户名获取用户（异常）"""
        mock_user_repo.get_by_username.side_effect = Exception("Database error")
        
        result = await user_service.get_user_by_username("testuser")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_exception(self, user_service, mock_user_repo):
        """测试根据邮箱获取用户（异常）"""
        mock_user_repo.get_by_email.side_effect = Exception("Database error")
        
        result = await user_service.get_user_by_email("test@example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_user_exception_handling(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试更新用户（异常处理）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update_user.side_effect = Exception("Database error")
        
        result, error = await user_service.update_user(str(mock_user.id), {"display_name": "Updated"})
        
        assert result is None
        assert error is not None
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_exception_handling(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试删除用户（异常处理）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update_user.side_effect = Exception("Database error")
        
        result, error = await user_service.delete_user(str(mock_user.id))
        
        assert result is False
        assert error is not None
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_role_exception_handling(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试分配角色（异常处理）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.assign_role.side_effect = Exception("Database error")
        
        result, error = await user_service.assign_role(str(mock_user.id), "role123")
        
        assert result is False
        assert error is not None
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_role_exception_handling(self, user_service, mock_user_repo, mock_user, mock_db):
        """测试移除角色（异常处理）"""
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.remove_role.side_effect = Exception("Database error")
        
        result, error = await user_service.remove_role(str(mock_user.id), "role123")
        
        assert result is False
        assert error is not None
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_user_info_exception(self, user_service, mock_user):
        """测试缓存用户信息（异常）"""
        with patch('src.services.user_service.cache_manager') as mock_cache:
            mock_cache.set = AsyncMock(side_effect=Exception("Cache error"))
            await user_service._cache_user_info(mock_user)
            # 应该不抛出异常，只记录警告
    
    @pytest.mark.asyncio
    async def test_get_cached_user_exception(self, user_service):
        """测试从缓存获取用户（异常）"""
        with patch('src.services.user_service.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
            result = await user_service._get_cached_user("user123")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_clear_user_cache_exception(self, user_service):
        """测试清除用户缓存（异常）"""
        with patch('src.services.user_service.cache_manager') as mock_cache:
            mock_cache.delete = AsyncMock(side_effect=Exception("Cache error"))
            await user_service._clear_user_cache("user123")
            # 应该不抛出异常，只记录警告

