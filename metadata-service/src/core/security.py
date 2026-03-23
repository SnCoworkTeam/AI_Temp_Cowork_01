"""
安全模块
提供认证和授权功能
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from luminaos_common.common.logger import setup_logger

logger = setup_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """
    获取当前用户信息（从JWT令牌）
    
    Args:
        credentials: HTTP Bearer令牌
        
    Returns:
        用户信息字典，如果令牌无效则返回None
    """
    token = credentials.credentials
    
    try:
        # 这里应该验证JWT令牌
        # 为了简化，暂时返回一个示例用户
        # 实际应该从auth-service验证令牌
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "roles": payload.get("roles", [])
        }
    except Exception as e:
        logger.warning(f"Failed to decode token: {str(e)}")
        return None


async def require_auth(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    要求认证的依赖
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 如果未认证
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

