"""
SSO客户端
集成OAuth 2.0/OpenID Connect协议
"""
from typing import Dict, Any, Optional
import logging
import httpx
from urllib.parse import urlencode, parse_qs, urlparse

from ..config import settings

logger = logging.getLogger(__name__)


class SSOClient:
    """SSO客户端 - OAuth 2.0/OpenID Connect"""
    
    def __init__(self):
        self.client_id = settings.SSO_CLIENT_ID
        self.client_secret = settings.SSO_CLIENT_SECRET
        self.authorization_url = settings.SSO_AUTHORIZATION_URL
        self.token_url = settings.SSO_TOKEN_URL
        self.userinfo_url = settings.SSO_USERINFO_URL
        self.redirect_uri = settings.SSO_REDIRECT_URI
        self.scopes = settings.SSO_SCOPES
    
    def get_authorization_url(self, state: str) -> str:
        """
        获取授权URL
        
        Args:
            state: 状态参数（用于防止CSRF攻击）
        
        Returns:
            授权URL
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }
        
        url = f"{self.authorization_url}?{urlencode(params)}"
        logger.info(f"Generated authorization URL with state: {state}")
        return url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        使用授权码交换访问令牌
        
        Args:
            code: 授权码
        
        Returns:
            令牌响应（包含access_token, refresh_token等）
        """
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
                
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0
                )
                response.raise_for_status()
                
                token_data = response.json()
                logger.info("Successfully exchanged code for tokens")
                return token_data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error exchanging code: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            raise
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            access_token: 访问令牌
        
        Returns:
            用户信息
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }
                
                response = await client.get(
                    self.userinfo_url,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                user_info = response.json()
                logger.info(f"Successfully retrieved user info for user: {user_info.get('sub')}")
                return user_info
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user info: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            新的令牌响应
        """
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
                
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30.0
                )
                response.raise_for_status()
                
                token_data = response.json()
                logger.info("Successfully refreshed access token")
                return token_data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error refreshing token: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            raise
    
    async def revoke_token(self, token: str, token_type_hint: Optional[str] = None):
        """
        撤销令牌
        
        Args:
            token: 要撤销的令牌
            token_type_hint: 令牌类型提示（access_token或refresh_token）
        """
        # 注意：不是所有OAuth提供者都支持令牌撤销
        # 这里提供一个基本实现，实际使用时需要根据提供者的文档调整
        logger.info(f"Token revocation requested (type: {token_type_hint})")
        # 实际实现取决于SSO提供者的API


# 全局SSO客户端实例
sso_client = SSOClient()









