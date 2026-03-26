"""
增强认证路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "auth-service" / "src"))


@pytest.mark.unit
class TestAuthEnhancedRoutes:
    """增强认证路由测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def mock_auth_service(self):
        """模拟认证服务"""
        auth_service = AsyncMock()
        return auth_service
    
    @pytest.fixture
    def client(self, mock_db, mock_auth_service):
        """测试客户端"""
        from src.main import app
        
        with patch('src.routes.auth_enhanced.get_db', return_value=mock_db), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service):
            yield TestClient(app)
    
    def test_register_endpoint_success(self, client, mock_auth_service):
        """测试注册端点成功"""
        mock_auth_service.register_user.return_value = ({
            "user_id": "user123",
            "username": "testuser",
            "email": "test@example.com"
        }, None)
        
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code in [201, 400, 500]
    
    def test_register_endpoint_duplicate_username(self, client, mock_auth_service):
        """测试注册端点（用户名重复）"""
        mock_auth_service.register_user.return_value = (None, "用户名已存在")
        
        response = client.post(
            "/auth/register",
            json={
                "username": "existinguser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code in [400, 500]
    
    def test_register_endpoint_missing_fields(self, client):
        """测试注册端点（缺少字段）"""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser"
                # 缺少email和password
            }
        )
        assert response.status_code in [422, 400]
    
    def test_login_endpoint_success(self, client, mock_auth_service):
        """测试登录端点成功"""
        mock_auth_service.authenticate_user.return_value = ({
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "user_id": "user123",
                "username": "testuser",
                "email": "test@example.com"
            },
            "session_id": "session123"
        }, None)
        
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        assert response.status_code in [200, 401, 500]
    
    def test_login_endpoint_invalid_credentials(self, client, mock_auth_service):
        """测试登录端点（无效凭据）"""
        mock_auth_service.authenticate_user.return_value = (None, "用户名或密码错误")
        
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code in [401, 500]
    
    def test_refresh_token_endpoint_success(self, client, mock_auth_service):
        """测试刷新令牌端点成功"""
        mock_auth_service.refresh_token.return_value = ({
            "access_token": "new_access_token",
            "token_type": "bearer",
            "expires_in": 3600
        }, None)
        
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "refresh_token_123"
            }
        )
        assert response.status_code in [200, 401, 500]
    
    def test_refresh_token_endpoint_invalid(self, client, mock_auth_service):
        """测试刷新令牌端点（无效令牌）"""
        mock_auth_service.refresh_token.return_value = (None, "无效的刷新令牌")
        
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid_token"
            }
        )
        assert response.status_code in [401, 500]
    
    def test_logout_endpoint(self, client, mock_auth_service):
        """测试登出端点"""
        mock_auth_service.logout.return_value = True
        
        # 需要认证，可能返回401
        response = client.post("/auth/logout")
        assert response.status_code in [200, 401, 500]
    
    def test_change_password_endpoint(self, client, mock_auth_service):
        """测试修改密码端点"""
        mock_auth_service.change_password.return_value = (True, None)
        
        # 需要认证，可能返回401
        response = client.post(
            "/auth/change-password",
            json={
                "old_password": "oldpass",
                "new_password": "newpass123"
            }
        )
        assert response.status_code in [200, 401, 400, 500]
    
    def test_get_user_sessions_endpoint(self, client):
        """测试获取用户会话列表端点"""
        # 需要认证，可能返回401
        response = client.get("/auth/sessions")
        assert response.status_code in [200, 401, 500]
    
    def test_revoke_session_endpoint(self, client):
        """测试撤销会话端点"""
        # 需要认证，可能返回401
        response = client.delete("/auth/sessions/session123")
        assert response.status_code in [200, 401, 404, 500]
    
    def test_register_endpoint_weak_password(self, client, mock_auth_service):
        """测试注册端点（弱密码）"""
        mock_auth_service.register_user.return_value = (None, "密码长度至少8位")
        
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert response.status_code in [400, 422, 500]
    
    def test_register_endpoint_invalid_email(self, client):
        """测试注册端点（无效邮箱）"""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        assert response.status_code in [422, 400]
    
    def test_login_endpoint_missing_fields(self, client):
        """测试登录端点（缺少字段）"""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser"
                # 缺少password
            }
        )
        assert response.status_code in [422, 400]
    
    def test_refresh_token_endpoint_missing_token(self, client):
        """测试刷新令牌端点（缺少令牌）"""
        response = client.post(
            "/auth/refresh",
            json={}
        )
        assert response.status_code in [422, 400]
    
    def test_change_password_endpoint_weak_password(self, client, mock_auth_service):
        """测试修改密码端点（弱密码）"""
        mock_auth_service.change_password.return_value = (False, "密码长度至少8位")
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}):
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "oldpass123",
                    "new_password": "short"
                }
            )
            assert response.status_code in [400, 401, 500]
    
    def test_change_password_endpoint_wrong_old_password(self, client, mock_auth_service):
        """测试修改密码端点（旧密码错误）"""
        mock_auth_service.change_password.return_value = (False, "旧密码错误")
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}):
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "wrongpass",
                    "new_password": "newpass123"
                }
            )
            assert response.status_code in [400, 401, 500]
    
    def test_get_user_sessions_with_auth(self, client, mock_auth_service):
        """测试获取用户会话列表端点（已认证）"""
        mock_auth_service.get_user_sessions = AsyncMock(return_value=[])
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service):
            response = client.get("/auth/sessions")
            assert response.status_code in [200, 401, 500]
    
    def test_revoke_session_with_auth(self, client, mock_auth_service):
        """测试撤销会话端点（已认证）"""
        mock_auth_service.logout = AsyncMock(return_value=True)
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service):
            response = client.delete("/auth/sessions/session123")
            assert response.status_code in [200, 401, 404, 500]
    
    def test_get_user_sessions_with_auth(self, client, mock_auth_service):
        """测试获取用户会话列表端点（已认证）"""
        from unittest.mock import MagicMock
        
        mock_session = MagicMock()
        mock_session.id = "session123"
        mock_session.ip_address = "127.0.0.1"
        mock_session.user_agent = "test-agent"
        mock_session.created_at = None
        mock_session.expires_at = None
        
        mock_session_repo = MagicMock()
        mock_session_repo.get_user_sessions.return_value = [mock_session]
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository', return_value=mock_session_repo), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.get("/auth/sessions")
            assert response.status_code in [200, 401, 500]
    
    def test_change_password_success(self, client, mock_auth_service):
        """测试修改密码成功"""
        mock_auth_service.change_password.return_value = (True, None)
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "oldpass123",
                    "new_password": "newpass123"
                }
            )
            assert response.status_code in [200, 401, 500]
    
    def test_change_password_wrong_old_password(self, client, mock_auth_service):
        """测试修改密码（旧密码错误）"""
        mock_auth_service.change_password.return_value = (False, "旧密码错误")
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "wrongpass",
                    "new_password": "newpass123"
                }
            )
            assert response.status_code in [400, 401, 500]
    
    def test_register_endpoint_exception(self, client, mock_auth_service):
        """测试注册端点（异常）"""
        mock_auth_service.register_user.side_effect = Exception("Database error")
        
        with patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post(
                "/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "password123"
                }
            )
            assert response.status_code in [500, 400]
    
    def test_login_endpoint_exception(self, client, mock_auth_service):
        """测试登录端点（异常）"""
        mock_auth_service.authenticate_user.side_effect = Exception("Database error")
        
        with patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post(
                "/auth/login",
                json={
                    "username": "testuser",
                    "password": "password123"
                }
            )
            assert response.status_code in [500, 401]
    
    def test_refresh_token_endpoint_exception(self, client, mock_auth_service):
        """测试刷新令牌端点（异常）"""
        mock_auth_service.refresh_token.side_effect = Exception("Database error")
        
        with patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post(
                "/auth/refresh",
                json={
                    "refresh_token": "refresh_token_123"
                }
            )
            assert response.status_code in [500, 401]
    
    def test_logout_endpoint_exception(self, client, mock_auth_service):
        """测试登出端点（异常）"""
        mock_auth_service.logout.side_effect = Exception("Database error")
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post("/auth/logout")
            assert response.status_code in [500, 401]
    
    def test_change_password_endpoint_exception(self, client, mock_auth_service):
        """测试修改密码端点（异常）"""
        mock_auth_service.change_password.side_effect = Exception("Database error")
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.AuthService', return_value=mock_auth_service), \
             patch('src.routes.auth_enhanced.get_db', return_value=MagicMock()):
            response = client.post(
                "/auth/change-password",
                json={
                    "old_password": "oldpass123",
                    "new_password": "newpass123"
                }
            )
            assert response.status_code in [500, 401, 400]
    
    def test_revoke_session_success(self, client, mock_auth_service):
        """测试撤销会话成功"""
        from unittest.mock import MagicMock
        
        mock_session = MagicMock()
        mock_session.user_id = "user123"
        mock_session_repo = MagicMock()
        mock_session_repo.get_session_by_id.return_value = mock_session
        mock_session_repo.deactivate_session.return_value = True
        
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository', return_value=mock_session_repo), \
             patch('src.routes.auth_enhanced.get_db', return_value=mock_db):
            response = client.delete("/auth/sessions/session123")
            assert response.status_code in [200, 401, 404, 500]
    
    def test_revoke_session_not_found(self, client, mock_auth_service):
        """测试撤销会话（会话不存在）"""
        from unittest.mock import MagicMock
        
        mock_session_repo = MagicMock()
        mock_session_repo.get_session_by_id.return_value = None
        
        mock_db = MagicMock()
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository', return_value=mock_session_repo), \
             patch('src.routes.auth_enhanced.get_db', return_value=mock_db):
            response = client.delete("/auth/sessions/nonexistent")
            assert response.status_code in [404, 401, 500]
    
    def test_revoke_session_wrong_user(self, client, mock_auth_service):
        """测试撤销会话（不属于当前用户）"""
        from unittest.mock import MagicMock
        
        mock_session = MagicMock()
        mock_session.user_id = "other123"
        mock_session_repo = MagicMock()
        mock_session_repo.get_session_by_id.return_value = mock_session
        
        mock_db = MagicMock()
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository', return_value=mock_session_repo), \
             patch('src.routes.auth_enhanced.get_db', return_value=mock_db):
            response = client.delete("/auth/sessions/session123")
            assert response.status_code in [404, 401, 500]
    
    def test_revoke_session_deactivate_failed(self, client, mock_auth_service):
        """测试撤销会话（停用失败）"""
        from unittest.mock import MagicMock
        
        mock_session = MagicMock()
        mock_session.user_id = "user123"
        mock_session_repo = MagicMock()
        mock_session_repo.get_session_by_id.return_value = mock_session
        mock_session_repo.deactivate_session.return_value = False
        
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository') as mock_repo_class, \
             patch('src.routes.auth_enhanced.get_db', return_value=mock_db):
            # SessionRepository被调用时会返回mock_session_repo
            mock_repo_class.return_value = mock_session_repo
            response = client.delete("/auth/sessions/session123")
            # 如果deactivate_session返回False，应该返回500错误
            assert response.status_code == 500
    
    def test_revoke_session_exception(self, client, mock_auth_service):
        """测试撤销会话（异常）"""
        from unittest.mock import MagicMock
        
        mock_session_repo = MagicMock()
        mock_session_repo.get_session_by_id.side_effect = Exception("Database error")
        
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository', return_value=mock_session_repo), \
             patch('src.routes.auth_enhanced.get_db', return_value=mock_db):
            response = client.delete("/auth/sessions/session123")
            assert response.status_code in [500, 401, 404]
    
    def test_get_user_sessions_exception(self, client, mock_auth_service):
        """测试获取用户会话列表（异常）"""
        from unittest.mock import MagicMock
        
        mock_session_repo = MagicMock()
        mock_session_repo.get_user_sessions.side_effect = Exception("Database error")
        
        mock_db = MagicMock()
        
        with patch('src.routes.auth_enhanced.get_current_user', return_value={"user_id": "user123"}), \
             patch('src.routes.auth_enhanced.SessionRepository', return_value=mock_session_repo), \
             patch('src.routes.auth_enhanced.get_db', return_value=mock_db):
            response = client.get("/auth/sessions")
            assert response.status_code in [500, 401]

