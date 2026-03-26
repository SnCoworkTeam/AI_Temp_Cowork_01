"""
认证中间件
验证JWT令牌并注入用户信息到请求
"""
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from ..sso.jwt_manager import jwt_manager
from ..sso.cache_manager import cache_manager

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
    db_session = None
) -> dict:
    """
    获取当前用户（依赖注入函数）
    
    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭证（可选）
        db_session: 数据库会话（可选，用于黑名单检查）
    
    Returns:
        用户信息字典
    
    Raises:
        HTTPException: 如果认证失败
    """
    # 从Authorization头获取令牌
    if not credentials:
        credentials = await security(request)
    
    if not credentials:
        # 尝试从Cookie获取令牌
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        token = credentials.credentials
    
    # 验证令牌（包含黑名单检查）
    if db_session:
        # 使用异步版本（包含黑名单检查）
        payload = await jwt_manager.verify_token_async(token, token_type="access", db_session=db_session)
    else:
        # 使用同步版本（不包含黑名单检查，向后兼容）
        payload = jwt_manager.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查缓存（可选，用于额外的验证）
    cached_token = await cache_manager.get_access_token(token)
    if not cached_token:
        logger.warning(f"Token not found in cache: {token[:20]}...")
        # 注意：JWT令牌即使不在缓存中也可能有效，这取决于安全策略
    
    # 构建用户信息
    user_info = {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
        "token": token,
    }
    
    # 将用户信息添加到请求状态
    request.state.user = user_info
    
    return user_info


async def require_roles(*required_roles: str):
    """
    角色要求装饰器（依赖注入函数）
    
    Args:
        *required_roles: 需要的角色列表
    
    Returns:
        依赖函数
    """
    async def role_checker(user: dict = None) -> dict:
        if not user:
            user = await get_current_user(None)
        
        user_roles = user.get("roles", [])
        
        # 检查是否有任一需要的角色
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}",
            )
        
        return user
    
    return role_checker


async def optional_auth(request: Request) -> Optional[dict]:
    """
    可选认证（不会抛出异常）
    
    Args:
        request: FastAPI请求对象
    
    Returns:
        用户信息（如果已认证），否则返回None
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None









