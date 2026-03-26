"""
认证路由
处理登录、登出、回调等认证相关操作
"""
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import secrets
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..sso.sso_client import sso_client
from ..sso.jwt_manager import jwt_manager
from ..sso.cache_manager import cache_manager
from ..middleware.auth_middleware import get_current_user
from ..dependencies.database import get_db
from ..config import settings
from ..services.auth_service import AuthService
from ..sso.id_token_verifier import verify_id_token_rs256, extract_login_identity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


def _cookie_secure(request: Request) -> bool:
    """
    是否对本次响应设置 Secure Cookie：仅当本请求视为 HTTPS 时为 True。
    IDP 将来走 https 访问回调时自动生效；仍为 http 时不影响现有运行。
    TLS 终结在反代时，请由反代传入 X-Forwarded-Proto: https。
    """
    forwarded = request.headers.get("x-forwarded-proto") or request.headers.get("X-Forwarded-Proto") or ""
    if forwarded.strip():
        first = forwarded.split(",")[0].strip().lower()
        return first == "https"
    return request.url.scheme == "https"


def _get_post_login_base(request: Request) -> str:
    """推导登录成功/失败后的 WebUI 重定向基地址。"""
    base = settings.SSO_POST_LOGIN_REDIRECT_BASE.rstrip("/")
    if "localhost" in base:
        host = (
            request.headers.get("x-forwarded-host")
            or request.headers.get("X-Forwarded-Host")
            or request.headers.get("host")
            or ""
        )
        ip = host.split(":")[0].strip()
        if ip:
            scheme = "https" if _cookie_secure(request) else "http"
            base = f"{scheme}://{ip}:3000"
            logger.info("SSO redirect base fallback: %s", base)
    return base


def _resolve_post_login_url(request: Request, target_url: Optional[str]) -> str:
    """解析 IDP 传入的 target_url，防止开放重定向。"""
    base = _get_post_login_base(request)
    path = settings.SSO_TOKEN_LOGIN_DEFAULT_PATH
    if not path.startswith("/"):
        path = "/" + path
    default = f"{base}{path}"
    if not target_url or not str(target_url).strip():
        return default
    t = str(target_url).strip()
    if t.startswith("/") and not t.startswith("//"):
        return f"{base}{t}"
    from urllib.parse import urlparse

    p = urlparse(t)
    b = urlparse(base)
    if p.scheme in ("http", "https") and p.netloc and p.netloc == b.netloc:
        return t
    logger.warning("忽略不安全的 target_url: %s", t[:120])
    return default


def _sso_token_login_error_redirect(request: Request, code: str = "token_invalid") -> RedirectResponse:
    base = _get_post_login_base(request)
    return RedirectResponse(url=f"{base}/login?sso_error={code}", status_code=302)


# 请求/响应模型
class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str


# SSO状态管理函数（使用Redis）
async def store_sso_state(state: str, redirect_uri: Optional[str] = None) -> None:
    """存储SSO状态到Redis"""
    try:
        state_data = {
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow().isoformat()
        }
        await cache_manager.set(
            f"sso_state:{state}",
            state_data,
            ttl=600  # 10分钟过期
        )
        logger.debug(f"SSO state stored: {state}")
    except Exception as e:
        logger.error(f"Failed to store SSO state: {str(e)}")
        raise

async def get_sso_state(state: str) -> Optional[Dict[str, Any]]:
    """从Redis获取SSO状态"""
    try:
        state_data = await cache_manager.get(f"sso_state:{state}")
        return state_data
    except Exception as e:
        logger.error(f"Failed to get SSO state: {str(e)}")
        return None

async def delete_sso_state(state: str) -> None:
    """删除SSO状态"""
    try:
        await cache_manager.delete(f"sso_state:{state}")
        logger.debug(f"SSO state deleted: {state}")
    except Exception as e:
        logger.error(f"Failed to delete SSO state: {str(e)}")


@router.get("/sso/login")
async def sso_login(
    request: Request,
    redirect_uri: Optional[str] = None
):
    """
    发起SSO登录
    
    重定向到SSO提供者的授权页面
    """
    try:
        # 生成状态参数（用于防止CSRF攻击）
        state = secrets.token_urlsafe(32)
        
        # 存储状态到Redis（10分钟过期）
        await store_sso_state(state, redirect_uri)
        
        # 生成授权URL
        auth_url = sso_client.get_authorization_url(state)
        response = RedirectResponse(url=auth_url)
        
        # 设置状态Cookie（安全配置）
        response.set_cookie(
            key="sso_state",
            value=state,
            max_age=600,  # 10分钟
            httponly=True,
            secure=_cookie_secure(request),
            samesite="lax"
        )
        
        logger.info(f"SSO login initiated with state: {state}")
        return response
    
    except Exception as e:
        logger.error(f"SSO login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate SSO login: {str(e)}"
        )


@router.get("/sso/callback")
async def sso_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    code: str = None,
    state: str = None,
    error: str = None
):
    """
    SSO回调处理
    
    接收SSO提供者的回调，交换令牌，创建会话
    """
    try:
        # 检查错误
        if error:
            logger.error(f"SSO callback error: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSO authentication failed: {error}"
            )
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not provided"
            )
        
        # 验证状态参数
        cookie_state = request.cookies.get("sso_state")
        if not state or state != cookie_state:
            logger.warning(f"State mismatch: {state} != {cookie_state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # 从Redis获取状态
        state_data = await get_sso_state(state)
        if not state_data:
            logger.warning(f"State not found in Redis or expired: {state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state"
            )
        
        # 获取重定向URI（如果存储了）
        redirect_uri = state_data.get("redirect_uri")
        
        # 删除已使用的状态
        await delete_sso_state(state)
        
        # 使用授权码交换令牌
        token_response = await sso_client.exchange_code_for_tokens(code)
        
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to obtain access token"
            )
        
        # 获取用户信息（用于兼容部分 IDP 字段；但在“映射 admin”模式下将统一使用本地 admin 生成 JWT）
        _user_info = await sso_client.get_user_info(access_token)

        # 统一映射：SSO 登录结果不再使用外部用户身份，而是模拟本地 admin 登录
        auth_service = AuthService(db)
        admin_user = auth_service.user_repo.get_by_username(settings.SSO_ID_TOKEN_ADMIN_USERNAME)
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSO admin 映射失败，未找到用户: {settings.SSO_ID_TOKEN_ADMIN_USERNAME}",
            )

        user_id = str(admin_user.id)
        username = admin_user.username
        email = admin_user.email
        roles = [str(r.id) for r in admin_user.roles]
        
        # 生成内部JWT令牌
        jwt_access_token = jwt_manager.create_access_token(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles
        )
        
        jwt_refresh_token = jwt_manager.create_refresh_token(user_id=user_id)
        
        # 缓存令牌（异步操作）
        access_token_data = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "roles": roles,
        }
        await cache_manager.set_access_token(
            jwt_access_token,
            access_token_data,
            settings.CACHE_ACCESS_TOKEN_TTL
        )
        await cache_manager.add_user_token(user_id, "access", jwt_access_token)
        
        refresh_token_data = {
            "user_id": user_id,
        }
        await cache_manager.set_refresh_token(
            jwt_refresh_token,
            refresh_token_data,
            settings.CACHE_REFRESH_TOKEN_TTL
        )
        await cache_manager.add_user_token(user_id, "refresh", jwt_refresh_token)
        
        # 创建会话
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "roles": roles,
            "sso_access_token": access_token,  # 可选：存储SSO令牌
            "created_at": None,
        }
        
        await cache_manager.set_user_session(session_id, session_data)
        
        # 设置Cookie
        # 使用存储的重定向URI，如果没有则使用默认URI
        final_redirect_uri = redirect_uri or settings.SSO_REDIRECT_URI.replace("/auth/sso/callback", "/")
        redirect_response = RedirectResponse(url=final_redirect_uri)
        
        # 设置访问令牌Cookie
        redirect_response.set_cookie(
            key="access_token",
            value=jwt_access_token,
            httponly=True,
            secure=_cookie_secure(request),
            samesite="lax",
            max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        # 设置刷新令牌Cookie
        redirect_response.set_cookie(
            key="refresh_token",
            value=jwt_refresh_token,
            httponly=True,
            secure=_cookie_secure(request),
            samesite="lax",
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        # 设置会话ID Cookie
        redirect_response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=_cookie_secure(request),
            samesite="lax",
            max_age=settings.CACHE_SESSION_TTL
        )
        
        # 清除状态Cookie
        redirect_response.delete_cookie("sso_state")
        
        logger.info(f"SSO callback successful (mapped to admin): {user_id}")
        return redirect_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSO callback failed: {str(e)}"
        )


@router.get("/sso/token-login")
async def sso_token_login(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Query(
        None,
        description="部分 IDaaS 文档使用的 JWT 参数名（与 id_token 二选一）",
    ),
    id_token: Optional[str] = Query(
        None,
        description="OIDC 常见参数名 id_token（与 token 二选一）",
    ),
    target_url: Optional[str] = Query(
        None, description="登录成功后跳转地址（通常为相对路径或同站绝对 URL）"
    ),
):
    """
    IDaaS JWT SSO：浏览器 GET 回调，query 中携带 JWT（`token` 或 `id_token` 其一）及可选 `target_url`。

    对外地址须与 IDP 登记的 redirect_uri 一致（生产建议全站 HTTPS），经网关示例：
    https://<域名>:8080/api/auth/sso/token-login
    """
    jwt_str = (token or id_token or "").strip()
    if not jwt_str:
        return _sso_token_login_error_redirect(request, "missing_token")

    try:
        payload = verify_id_token_rs256(jwt_str)
        username, email = extract_login_identity(payload)
    except Exception as e:
        logger.warning("id_token 校验失败: %s", e)
        return _sso_token_login_error_redirect(request, "token_invalid")

    auth_service = AuthService(db)
    # 按当前约定：IDP 进入的用户统一映射 admin
    admin_user = auth_service.user_repo.get_by_username(
        settings.SSO_ID_TOKEN_ADMIN_USERNAME
    )
    if not admin_user:
        logger.warning(
            "SSO admin 映射失败，未找到用户: %s",
            settings.SSO_ID_TOKEN_ADMIN_USERNAME,
        )
        return _sso_token_login_error_redirect(request, "admin_not_found")

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    result, err = await auth_service.login_with_sso_identity(
        admin_user,
        ip_address=client_ip,
        user_agent=user_agent,
        permission_source_user=admin_user,
    )
    if err or not result:
        logger.warning("SSO token-login 签发失败: %s", err)
        return _sso_token_login_error_redirect(request, "login_failed")

    dest = _resolve_post_login_url(request, target_url)
    redirect_response = RedirectResponse(url=dest, status_code=302)

    redirect_response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=_cookie_secure(request),
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    redirect_response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=_cookie_secure(request),
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    redirect_response.set_cookie(
        key="session_id",
        value=result["session_id"],
        httponly=True,
        secure=_cookie_secure(request),
        samesite="lax",
        max_age=settings.CACHE_SESSION_TTL,
    )
    logger.info("SSO token-login 成功: user_id=%s", result.get("user", {}).get("user_id"))
    return redirect_response


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌（包含黑名单检查）
    
    使用刷新令牌获取新的访问令牌
    """
    try:
        refresh_token = request.refresh_token
        
        # 验证刷新令牌（包含黑名单检查）
        payload = await jwt_manager.verify_token_async(
            refresh_token, 
            token_type="refresh",
            db_session=db
        )
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked refresh token"
            )
        
        user_id = payload.get("sub")
        
        # 检查刷新令牌是否在缓存中
        cached_refresh = await cache_manager.get_refresh_token(refresh_token)
        if not cached_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or revoked"
            )
        
        # 获取用户信息（从缓存或数据库）
        # 这里简化处理，实际应该从数据库获取
        user_session = await cache_manager.get_user_session(
            f"user_session:{user_id}"
        )
        
        if not user_session:
            # 如果会话不存在，尝试从SSO获取用户信息
            # 这里简化处理，实际应该从数据库获取
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User session not found"
            )
        
        # 生成新的访问令牌
        new_access_token = jwt_manager.create_access_token(
            user_id=user_id,
            username=user_session.get("username", ""),
            email=user_session.get("email", ""),
            roles=user_session.get("roles", [])
        )
        
        # 缓存新的访问令牌
        access_token_data = {
            "user_id": user_id,
            "username": user_session.get("username", ""),
            "email": user_session.get("email", ""),
            "roles": user_session.get("roles", []),
        }
        await cache_manager.set_access_token(
            new_access_token,
            access_token_data,
            settings.CACHE_ACCESS_TOKEN_TTL
        )
        await cache_manager.add_user_token(user_id, "access", new_access_token)
        
        # 可选：生成新的刷新令牌（滚动刷新）
        new_refresh_token = jwt_manager.create_refresh_token(user_id=user_id)
        
        # 缓存新的刷新令牌
        refresh_token_data = {
            "user_id": user_id,
        }
        await cache_manager.set_refresh_token(
            new_refresh_token,
            refresh_token_data,
            settings.CACHE_REFRESH_TOKEN_TTL
        )
        await cache_manager.add_user_token(user_id, "refresh", new_refresh_token)
        
        # 删除旧的刷新令牌（添加到黑名单）
        await jwt_manager.revoke_token(
            refresh_token, 
            token_type="refresh", 
            db_session=db,
            reason="token_refreshed"
        )
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    登出并清理缓存（使用黑名单机制）
    
    撤销所有令牌并清除会话
    """
    try:
        # 获取当前用户（包含黑名单检查）
        from ..middleware.auth_middleware import get_current_user
        current_user = await get_current_user(request, db_session=db)
        
        user_id = current_user.get("user_id")
        access_token = current_user.get("token")
        session_id = request.cookies.get("session_id")
        
        # 使用认证服务的logout方法（包含完整的黑名单处理）
        from ..services.auth_service import AuthService
        auth_service = AuthService(db)
        
        success = await auth_service.logout(
            user_id=user_id,
            session_id=session_id,
            access_token=access_token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
        
        # 清除Cookie
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("session_id")
        
        logger.info(f"User logged out: {user_id}")
        
        return LogoutResponse(message="Logged out successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

