"""
认证和权限依赖
"""

import logging
import os

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> dict:
    """
    获取当前用户（简化版，从token中解析）

    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭证

    Returns:
        用户信息字典

    Raises:
        HTTPException: 如果认证失败
    """
    # 尝试从Authorization头获取令牌
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # 尝试从Cookie获取令牌
        token = request.cookies.get("access_token")
        # 尝试从请求头获取
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]

    if not token:
        # 允许匿名访问（开发环境），生产环境应该要求认证
        if os.getenv("DEBUG", "false").lower() == "true":
            return {"user_id": "anonymous", "username": "anonymous", "email": None, "roles": [], "token": None}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证token（可以调用auth-service验证，这里简化处理）
    # 在实际环境中，应该调用auth-service验证token
    try:
        # 尝试通过auth-service验证token
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8003")
        # 如果配置了API网关URL，使用API网关
        api_gateway_url = os.getenv("API_GATEWAY_URL", "http://api-gateway:8080")

        # 优先尝试通过API网关验证
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_gateway_url}/api/users/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0
                )
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "user_id": user_data.get("id") or user_data.get("user_id"),
                        "username": user_data.get("username"),
                        "email": user_data.get("email"),
                        "roles": user_data.get("roles", []),
                        "token": token,
                    }
        except (ValueError, AttributeError):
            # 如果API网关验证失败，尝试直接连接auth-service
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{auth_service_url}/api/users/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0
                    )
                    if response.status_code == 200:
                        user_data = response.json()
                        return {
                            "user_id": user_data.get("id") or user_data.get("user_id"),
                            "username": user_data.get("username"),
                            "email": user_data.get("email"),
                            "roles": user_data.get("roles", []),
                            "token": token,
                        }
            except (ValueError, AttributeError):
                pass

        # 如果验证服务不可用，但token存在，在开发环境允许通过
        # 或者尝试解析JWT token获取基本信息
        if os.getenv("DEBUG", "false").lower() == "true" or os.getenv("ALLOW_TOKEN_BYPASS", "false").lower() == "true":
            logger.warning("Token验证服务不可用，但允许token通过（开发模式）")
            # 尝试从token中解析用户信息（如果token是JWT）
            try:
                import jwt

                # 不验证签名，只解析payload（开发环境）
                decoded = jwt.decode(token, options={"verify_signature": False})
                return {
                    "user_id": decoded.get("sub") or decoded.get("user_id") or "unknown",
                    "username": decoded.get("username") or decoded.get("preferred_username") or "user",
                    "email": decoded.get("email"),
                    "roles": decoded.get("roles", []),
                    "token": token,
                }
            except (ValueError, AttributeError):
                # 如果无法解析，返回默认用户信息
                return {"user_id": "authenticated_user", "username": "user", "email": None, "roles": [], "token": token}
    except Exception as e:
        logger.warning(f"Token验证失败: {e!s}")

    # 如果验证失败，在开发环境允许匿名访问
    if os.getenv("DEBUG", "false").lower() == "true":
        return {"user_id": "anonymous", "username": "anonymous", "email": None, "roles": [], "token": token}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_auth(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求认证（依赖注入函数）

    Args:
        current_user: 当前用户

    Returns:
        用户信息
    """
    if not current_user or current_user.get("user_id") == "anonymous":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求管理员权限

    Args:
        current_user: 当前用户

    Returns:
        用户信息
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    username = current_user.get("username", "").lower()
    roles = current_user.get("roles", [])

    # 检查是否是管理员（admin账号或roles中包含admin）
    is_admin = (
        username == "admin" or
        "admin" in [r.lower() for r in roles] if isinstance(roles, list) else False or
        "administrator" in [r.lower() for r in roles] if isinstance(roles, list) else False
    )

    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return current_user
