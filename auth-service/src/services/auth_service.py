"""
认证服务
处理用户认证、登录、登出等业务逻辑
"""
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import hashlib

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..repositories.user_repository import UserRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.token_repository import TokenRepository
from ..sso.jwt_manager import JWTManager
from ..sso.cache_manager import cache_manager

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.token_repo = TokenRepository(db)
        self.jwt_manager = JWTManager()
    
    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            full_name: 全名
            ip_address: IP地址
        
        Returns:
            (用户信息字典, 错误消息)
        """
        try:
            logger.info(f"Starting user registration for username: {username}, email: {email}")
            
            # 刷新数据库会话
            self.db.expire_all()
            
            # 验证用户名和邮箱是否已存在
            existing_user = self.user_repo.get_by_username(username)
            if existing_user:
                logger.warning(f"Registration failed: Username {username} already exists")
                return None, "用户名已存在"
            
            existing_email = self.user_repo.get_by_email(email)
            if existing_email:
                logger.warning(f"Registration failed: Email {email} already registered")
                return None, "邮箱已被注册"
            
            # 验证密码强度
            password_error = self._validate_password(password)
            if password_error:
                logger.warning(f"Registration failed: Password validation error - {password_error}")
                return None, password_error
            
            # 加密密码
            logger.debug(f"Hashing password for user {username}")
            password_hash = pwd_context.hash(password)
            logger.debug(f"Password hashed successfully")
            
            # 创建用户
            logger.debug(f"Creating user in database: {username}")
            from database.src.models.user_models import User
            db_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                status="active"  # 直接使用字符串值，匹配数据库枚举类型
            )
            self.db.add(db_user)
            self.db.flush()
            
            logger.debug(f"User created, committing to database")
            self.db.commit()
            # 刷新会话，确保用户对象状态是最新的
            self.db.refresh(db_user)
            logger.debug(f"User object refreshed, id: {db_user.id}")
            
            # 缓存用户信息
            await self._cache_user_info(db_user)
            
            logger.info(f"User registered successfully: {username} (id: {db_user.id})")
            
            return {
                "user_id": str(db_user.id),
                "username": db_user.username,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "status": db_user.status.value
            }, None
            
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}", exc_info=True)
            self.db.rollback()
            return None, f"注册失败: {str(e)}"
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        用户认证（登录）
        
        Args:
            username: 用户名或邮箱
            password: 密码
            ip_address: IP地址
            user_agent: 用户代理
        
        Returns:
            (认证结果（包含tokens和用户信息）, 错误消息)
        """
        try:
            # 刷新数据库会话，确保能查询到刚注册的用户
            self.db.expire_all()
            
            logger.info(f"Attempting login for username/email: {username}")
            
            # 查找用户（支持用户名或邮箱登录）
            user = self.user_repo.get_by_username(username)
            if not user:
                logger.debug(f"User not found by username, trying email: {username}")
                user = self.user_repo.get_by_email(username)
            
            if not user:
                logger.warning(f"Login failed: User not found for {username}")
                return None, "用户名或密码错误"
            
            logger.info(f"User found: {user.username} (id: {user.id}, status: {user.status.value})")
            
            # 检查用户状态
            if user.status.value != "active":
                logger.warning(f"Login failed: User {user.username} status is {user.status.value}")
                return None, f"用户账户状态为{user.status.value}，无法登录"
            
            # 验证密码
            logger.debug(f"Verifying password for user {user.username}")
            password_valid = pwd_context.verify(password, user.password_hash)
            if not password_valid:
                logger.warning(f"Login failed: Invalid password for user {user.username}")
                # 记录失败登录尝试
                await self._record_failed_login(user.id, ip_address)
                return None, "用户名或密码错误"
            
            logger.info(f"Password verified successfully for user {user.username}")
            
            # 更新最后登录信息
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            self.db.commit()
            
            # 生成JWT令牌
            access_token = self.jwt_manager.create_access_token(
                user_id=str(user.id),
                username=user.username,
                email=user.email
            )
            
            refresh_token = self.jwt_manager.create_refresh_token(
                user_id=str(user.id)
            )
            
            # 创建会话
            expires_at = datetime.utcnow() + timedelta(hours=1)
            db_session = self.session_repo.create_session(
                user_id=str(user.id),
                access_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            
            self.db.commit()
            
            # 缓存会话和令牌
            await self._cache_session(db_session, access_token, refresh_token)
            
            # 获取用户权限
            permissions = self.user_repo.get_user_permissions(str(user.id))
            permission_codes = [p.code for p in permissions] if permissions else []
            
            logger.info(f"User authenticated: {username} ({user.id})")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": [str(r.id) for r in user.roles],
                    "permissions": permission_codes
                },
                "session_id": str(db_session.id)
            }, None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}", exc_info=True)
            self.db.rollback()
            return None, f"认证失败: {str(e)}"
    
    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            ip_address: IP地址
        
        Returns:
            (新的tokens, 错误消息)
        """
        try:
            # 验证刷新令牌
            payload = self.jwt_manager.verify_token(refresh_token)
            if not payload:
                return None, "无效的刷新令牌"
            
            user_id = payload.get("sub")
            if not user_id:
                return None, "无效的令牌负载"
            
            # 检查令牌是否在黑名单中
            if cache_manager._redis:
                is_blacklisted = await self.token_repo.is_token_blacklisted(refresh_token, cache_manager._redis)
                if is_blacklisted:
                    return None, "令牌已被撤销"
            
            # 获取用户
            user = self.user_repo.get_by_id(user_id)
            if not user or user.status.value != "active":
                return None, "用户不存在或已禁用"
            
            # 生成新的访问令牌
            access_token = self.jwt_manager.create_access_token(
                user_id=str(user.id),
                username=user.username,
                email=user.email
            )
            
            # 更新会话
            sessions = self.session_repo.get_user_sessions(
                str(user.id),
                active_only=True
            )
            if sessions:
                # 更新第一个活跃会话
                session = sessions[0]
                session.access_token = access_token
                session.last_login_ip = ip_address
                self.db.commit()
                
                # 更新缓存
                await self._cache_session(session, access_token, None)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 3600
            }, None
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
            return None, f"刷新令牌失败: {str(e)}"
    
    async def logout(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> bool:
        """
        用户登出（使用新的黑名单机制）
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            access_token: 访问令牌（可选）
            refresh_token: 刷新令牌（可选）
        
        Returns:
            是否成功
        """
        try:
            from ..repositories.token_blacklist_repository import TokenBlacklistRepository
            blacklist_repo = TokenBlacklistRepository(self.db)
            
            if session_id:
                # 停用指定会话
                self.session_repo.deactivate_session(session_id)
                
                # 获取会话以获取令牌
                session = self.session_repo.get_session_by_id(session_id)
                if session:
                    # 撤销访问令牌
                    if session.access_token:
                        try:
                            # 解码令牌获取过期时间
                            payload = self.jwt_manager.verify_token(session.access_token, token_type="access")
                            if payload:
                                expires_at = datetime.fromtimestamp(payload.get("exp", 0))
                                await blacklist_repo.add_to_blacklist(
                                    token=session.access_token,
                                    token_type="access",
                                    user_id=user_id,
                                    expires_at=expires_at,
                                    reason="logout"
                                )
                                await self.jwt_manager.revoke_token(
                                    session.access_token,
                                    token_type="access",
                                    db_session=self.db,
                                    reason="logout"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to revoke access token: {e}")
                    
                    # 撤销刷新令牌
                    if session.refresh_token:
                        try:
                            payload = self.jwt_manager.verify_token(session.refresh_token, token_type="refresh")
                            if payload:
                                expires_at = datetime.fromtimestamp(payload.get("exp", 0))
                                await blacklist_repo.add_to_blacklist(
                                    token=session.refresh_token,
                                    token_type="refresh",
                                    user_id=user_id,
                                    expires_at=expires_at,
                                    reason="logout"
                                )
                                await self.jwt_manager.revoke_token(
                                    session.refresh_token,
                                    token_type="refresh",
                                    db_session=self.db,
                                    reason="logout"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to revoke refresh token: {e}")
                    
                    self.db.commit()
                    
            elif access_token:
                # 根据令牌停用会话
                session = self.session_repo.get_session_by_token(access_token)
                if session:
                    session.is_active = False
                    self.db.commit()
                    
                    # 撤销访问令牌
                    try:
                        payload = self.jwt_manager.verify_token(access_token, token_type="access")
                        if payload:
                            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
                            await blacklist_repo.add_to_blacklist(
                                token=access_token,
                                token_type="access",
                                user_id=user_id,
                                expires_at=expires_at,
                                reason="logout"
                            )
                            await self.jwt_manager.revoke_token(
                                access_token,
                                token_type="access",
                                db_session=self.db,
                                reason="logout"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to revoke access token: {e}")
                    
                    # 撤销刷新令牌（如果存在）
                    if session.refresh_token:
                        try:
                            payload = self.jwt_manager.verify_token(session.refresh_token, token_type="refresh")
                            if payload:
                                expires_at = datetime.fromtimestamp(payload.get("exp", 0))
                                await blacklist_repo.add_to_blacklist(
                                    token=session.refresh_token,
                                    token_type="refresh",
                                    user_id=user_id,
                                    expires_at=expires_at,
                                    reason="logout"
                                )
                                await self.jwt_manager.revoke_token(
                                    session.refresh_token,
                                    token_type="refresh",
                                    db_session=self.db,
                                    reason="logout"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to revoke refresh token: {e}")
            else:
                # 停用用户所有会话并撤销所有令牌
                sessions = self.session_repo.get_user_sessions(str(user_id), active_only=True)
                for session in sessions:
                    session.is_active = False
                    if session.access_token:
                        try:
                            payload = self.jwt_manager.verify_token(session.access_token, token_type="access")
                            if payload:
                                expires_at = datetime.fromtimestamp(payload.get("exp", 0))
                                await blacklist_repo.add_to_blacklist(
                                    token=session.access_token,
                                    token_type="access",
                                    user_id=user_id,
                                    expires_at=expires_at,
                                    reason="logout_all"
                                )
                        except Exception:
                            pass  # 忽略无效令牌
                
                self.db.commit()
                
                # 撤销用户的所有令牌（从缓存）
                await self.jwt_manager.revoke_user_tokens(
                    user_id,
                    db_session=self.db,
                    reason="logout_all"
                )
            
            logger.info(f"User logged out: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging out: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        修改密码（密码更改后撤销所有令牌）
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            (是否成功, 错误消息)
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return False, "用户不存在"
            
            # 验证旧密码
            if not pwd_context.verify(old_password, user.password_hash):
                return False, "旧密码错误"
            
            # 验证新密码强度
            password_error = self._validate_password(new_password)
            if password_error:
                return False, password_error
            
            # 加密新密码
            new_password_hash = pwd_context.hash(new_password)
            
            # 更新密码
            user.password_hash = new_password_hash
            self.db.commit()
            
            # 密码更改成功后，撤销用户的所有令牌（安全措施）
            try:
                await self.jwt_manager.revoke_user_tokens(
                    user_id,
                    db_session=self.db,
                    reason="password_changed"
                )
                logger.info(f"All tokens revoked for user {user_id} after password change")
            except Exception as e:
                logger.warning(f"Failed to revoke tokens after password change: {e}")
                # 令牌撤销失败不影响密码更改
            
            logger.info(f"Password changed for user: {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}", exc_info=True)
            self.db.rollback()
            return False, f"修改密码失败: {str(e)}"
    
    async def reset_password(
        self,
        user_id: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        重置密码（管理员操作）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
        
        Returns:
            (是否成功, 错误消息)
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return False, "用户不存在"
            
            # 验证密码强度
            password_error = self._validate_password(new_password)
            if password_error:
                return False, password_error
            
            # 加密新密码
            new_password_hash = pwd_context.hash(new_password)
            
            # 更新密码
            user.password_hash = new_password_hash
            self.db.commit()
            
            logger.info(f"Password reset for user: {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}", exc_info=True)
            self.db.rollback()
            return False, f"重置密码失败: {str(e)}"
    
    def _validate_password(self, password: str) -> Optional[str]:
        """
        验证密码强度
        
        Args:
            password: 密码
        
        Returns:
            错误消息，如果密码有效则返回None
        """
        if len(password) < 8:
            return "密码长度至少8位"
        
        if len(password) > 128:
            return "密码长度不能超过128位"
        
        # 检查是否包含数字
        if not any(c.isdigit() for c in password):
            return "密码必须包含至少一个数字"
        
        # 检查是否包含字母
        if not any(c.isalpha() for c in password):
            return "密码必须包含至少一个字母"
        
        return None
    
    async def _cache_user_info(self, user):
        """缓存用户信息到Redis"""
        try:
            if cache_manager._redis:
                user_key = f"user:info:{user.id}"
                user_data = {
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "status": user.status.value if hasattr(user.status, 'value') else str(user.status),
                    "roles": [str(r.id) for r in user.roles]
                }
                await cache_manager.set(user_key, user_data, ttl=3600)  # 1小时
        except Exception as e:
            logger.warning(f"Failed to cache user info: {str(e)}")
    
    async def _cache_session(self, session, access_token: str, refresh_token: Optional[str]):
        """缓存会话到Redis"""
        try:
            redis_client = await cache_manager.get_client()
            if redis_client:
                # 缓存访问令牌
                if access_token:
                    token_key = f"token:access:{access_token[:20]}"
                    await cache_manager.set(token_key, {
                        "session_id": str(session.id),
                        "user_id": str(session.user_id)
                    }, ttl=3600)
                
                # 缓存刷新令牌
                if refresh_token:
                    refresh_key = f"token:refresh:{refresh_token[:20]}"
                    await cache_manager.set(refresh_key, {
                        "session_id": str(session.id),
                        "user_id": str(session.user_id)
                    }, ttl=604800)  # 7天
        except Exception as e:
            logger.warning(f"Failed to cache session: {str(e)}")
    
    async def _record_failed_login(self, user_id: UUID, ip_address: Optional[str]):
        """记录失败登录尝试"""
        try:
            redis_client = await cache_manager.get_client()
            if redis_client:
                key = f"login:failed:{user_id}:{ip_address or 'unknown'}"
                count = await cache_manager.get(key) or 0
                await cache_manager.set(key, count + 1, ttl=3600)  # 1小时
        except Exception as e:
            logger.warning(f"Failed to record failed login: {str(e)}")

