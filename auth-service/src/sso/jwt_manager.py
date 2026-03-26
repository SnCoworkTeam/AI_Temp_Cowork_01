"""
JWT令牌管理器
生成、验证和管理JWT令牌
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from ..config import settings
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)


class JWTManager:
    """JWT令牌管理器"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        email: str,
        roles: list = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱
            roles: 用户角色列表
            additional_claims: 额外的声明
        
        Returns:
            JWT访问令牌
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,  # subject (用户ID)
            "username": username,
            "email": email,
            "roles": roles or [],
            "type": "access",
            "iat": now,  # issued at
            "exp": expire,  # expiration
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # 注意：缓存操作应该在异步上下文中调用
        # 这里只返回令牌，缓存由调用者负责
        logger.debug(f"Created access token for user: {user_id}")
        
        return token
    
    def create_refresh_token(
        self,
        user_id: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建刷新令牌
        
        Args:
            user_id: 用户ID
            additional_claims: 额外的声明
        
        Returns:
            JWT刷新令牌
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": expire,
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # 注意：缓存操作应该在异步上下文中调用
        # 这里只返回令牌，缓存由调用者负责
        logger.debug(f"Created refresh token for user: {user_id}")
        
        return token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        验证令牌（同步版本，不包含黑名单检查）
        
        注意：黑名单检查需要在异步上下文中进行，使用 verify_token_async()
        
        Args:
            token: JWT令牌
            token_type: 令牌类型（access或refresh）
        
        Returns:
            解码后的载荷，如果无效则返回None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 验证令牌类型
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
    
    async def verify_token_async(
        self, 
        token: str, 
        token_type: str = "access",
        db_session = None
    ) -> Optional[Dict[str, Any]]:
        """
        验证令牌（异步版本，包含黑名单检查）
        
        Args:
            token: JWT令牌
            token_type: 令牌类型（access或refresh）
            db_session: 数据库会话（可选，如果提供则进行黑名单检查）
        
        Returns:
            解码后的载荷，如果无效或已撤销则返回None
        """
        try:
            # 先进行基本的JWT验证
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 验证令牌类型
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            
            # 检查黑名单（如果提供了数据库会话）
            if db_session:
                try:
                    from ..repositories.token_blacklist_repository import TokenBlacklistRepository
                    blacklist_repo = TokenBlacklistRepository(db_session)
                    if await blacklist_repo.is_blacklisted(token):
                        logger.warning(f"Token is blacklisted: {token[:20]}...")
                        return None
                except Exception as e:
                    logger.error(f"Failed to check token blacklist: {e}")
                    # 黑名单检查失败时，为了安全，拒绝令牌
                    return None
            
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
    
    async def revoke_token(
        self, 
        token: str, 
        token_type: str = "access",
        db_session = None,
        reason: Optional[str] = None
    ):
        """
        撤销令牌（添加到黑名单 + 从缓存中删除）
        
        Args:
            token: JWT令牌
            token_type: 令牌类型
            db_session: 数据库会话（必需，用于添加到黑名单）
            reason: 撤销原因
        """
        try:
            # 先验证令牌以获取信息（不验证过期）
            try:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                    options={"verify_exp": False}  # 允许撤销已过期的令牌
                )
            except InvalidTokenError:
                logger.warning(f"Attempted to revoke invalid token: {token[:20]}...")
                # 即使令牌无效也继续（防御性编程）
                return
            
            user_id = payload.get("sub")
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
            
            # 添加到数据库黑名单
            if db_session:
                try:
                    from ..repositories.token_blacklist_repository import TokenBlacklistRepository
                    blacklist_repo = TokenBlacklistRepository(db_session)
                    await blacklist_repo.add_to_blacklist(
                        token=token,
                        token_type=token_type,
                        user_id=user_id,
                        expires_at=expires_at,
                        reason=reason or "revoked"
                    )
                    logger.info(f"Token revoked and added to blacklist: {token[:20]}...")
                except Exception as e:
                    logger.error(f"Failed to add token to blacklist: {e}")
                    # 继续执行缓存清理
            
            # 从缓存中删除（现有逻辑）
            if token_type == "access":
                await cache_manager.delete_access_token(token)
            elif token_type == "refresh":
                await cache_manager.delete_refresh_token(token)
            
            # 从用户令牌映射中删除
            if user_id:
                await cache_manager.delete_user_tokens(user_id, token_type)
                
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}", exc_info=True)
    
    async def revoke_user_tokens(
        self, 
        user_id: str,
        db_session = None,
        reason: str = "user_revoked_all"
    ):
        """
        撤销用户的所有令牌
        
        Args:
            user_id: 用户ID
            db_session: 数据库会话（可选，用于清理黑名单记录）
            reason: 撤销原因
        """
        try:
            # 获取用户的所有令牌
            access_tokens = await cache_manager.get_user_tokens(user_id, "access")
            refresh_tokens = await cache_manager.get_user_tokens(user_id, "refresh")
            
            # 删除所有访问令牌（从缓存）
            for token in access_tokens:
                await cache_manager.delete_access_token(token)
            
            # 删除所有刷新令牌（从缓存）
            for token in refresh_tokens:
                await cache_manager.delete_refresh_token(token)
            
            # 删除用户令牌映射
            await cache_manager.delete_user_tokens(user_id, "access")
            await cache_manager.delete_user_tokens(user_id, "refresh")
            
            # 清理过期的黑名单记录（如果提供了数据库会话）
            if db_session:
                try:
                    from ..repositories.token_blacklist_repository import TokenBlacklistRepository
                    blacklist_repo = TokenBlacklistRepository(db_session)
                    await blacklist_repo.revoke_user_tokens(user_id, reason)
                except Exception as e:
                    logger.error(f"Failed to cleanup user blacklist records: {e}")
            
            logger.info(f"All tokens revoked for user: {user_id}")
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {str(e)}", exc_info=True)


# 全局JWT管理器实例
jwt_manager = JWTManager()

