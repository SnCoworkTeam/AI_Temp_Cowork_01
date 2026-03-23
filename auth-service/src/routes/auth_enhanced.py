"""
增强的认证路由
集成数据库的用户注册、登录、密码管理等功能
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from ..dependencies.database import get_db
from ..services.auth_service import AuthService
from ..services.user_service import UserService
from ..middleware.auth_middleware import get_current_user
from ..sso.jwt_manager import jwt_manager
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


# 请求/响应模型
class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class RegisterResponse(BaseModel):
    """用户注册响应"""
    user_id: str
    username: str
    email: str
    message: str


class LoginRequest(BaseModel):
    """登录请求"""
    username: str  # 支持用户名或邮箱
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    session_id: str


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    """修改密码响应"""
    message: str


class LogoutResponse(BaseModel):
    """登出响应"""
    message: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    创建新用户账户
    """
    try:
        logger.info(f"Register request received - username: {getattr(request, 'username', 'NOT_SET')}, email: {getattr(request, 'email', 'NOT_SET')}")
        
        # 验证必填字段
        if not hasattr(request, 'username') or not request.username:
            logger.error("Register request missing username field")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="用户名不能为空"
            )
        
        if not hasattr(request, 'email') or not request.email:
            logger.error("Register request missing email field")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="邮箱不能为空"
            )
        
        if not hasattr(request, 'password') or not request.password:
            logger.error("Register request missing password field")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="密码不能为空"
            )
        
        auth_service = AuthService(db)
        
        client_ip = request_obj.client.host if request_obj.client else None
        
        logger.info(f"Attempting to register user: {request.username} with email: {request.email}")
        
        user_data, error = await auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            ip_address=client_ip
        )
        
        if error:
            logger.warning(f"Registration failed: {error} for username: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        logger.info(f"Registration successful for user: {user_data.get('username', 'unknown')}")
        return RegisterResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            message="用户注册成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    支持用户名或邮箱登录
    """
    try:
        logger.info(f"Login request received for username: {request.username}")
        auth_service = AuthService(db)
        
        client_ip = request_obj.client.host if request_obj.client else None
        user_agent = request_obj.headers.get("user-agent")
        
        result, error = await auth_service.authenticate_user(
            username=request.username,
            password=request.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if error:
            logger.warning(f"Login failed: {error} for username: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error
            )
        
        logger.info(f"Login successful for user: {result.get('user', {}).get('username', 'unknown')}")
        return LoginResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌（包含黑名单检查）
    """
    try:
        # 先检查刷新令牌是否在黑名单中
        from ..repositories.token_blacklist_repository import TokenBlacklistRepository
        blacklist_repo = TokenBlacklistRepository(db)
        
        if await blacklist_repo.is_blacklisted(request.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        auth_service = AuthService(db)
        
        client_ip = request_obj.client.host if request_obj.client else None
        
        result, error = await auth_service.refresh_token(
            refresh_token=request.refresh_token,
            ip_address=client_ip
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error
            )
        
        # 撤销旧的刷新令牌（添加到黑名单）
        try:
            await jwt_manager.revoke_token(
                request.refresh_token,
                token_type="refresh",
                db_session=db,
                reason="token_refreshed"
            )
        except Exception as e:
            logger.warning(f"Failed to revoke old refresh token: {e}")
            # 继续执行，不影响新令牌的返回
        
        return RefreshTokenResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新令牌失败: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    session_id: Optional[str] = None
):
    """
    用户登出
    
    撤销当前会话和令牌（使用黑名单机制）
    """
    try:
        # 获取当前用户（包含黑名单检查）
        current_user = await get_current_user(request, db_session=db)
        
        auth_service = AuthService(db)
        user_id = current_user.get("user_id")
        access_token = current_user.get("token")
        
        success = await auth_service.logout(
            user_id=user_id,
            session_id=session_id,
            access_token=access_token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登出失败"
            )
        
        return LogoutResponse(message="登出成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    修改密码
    
    需要提供旧密码进行验证
    """
    try:
        auth_service = AuthService(db)
        user_id = current_user.get("user_id")
        
        success, error = await auth_service.change_password(
            user_id=user_id,
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return ChangePasswordResponse(message="密码修改成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改密码失败: {str(e)}"
        )


@router.get("/sessions")
async def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的所有活跃会话
    """
    try:
        from ..repositories.session_repository import SessionRepository
        
        session_repo = SessionRepository(db)
        user_id = current_user.get("user_id")
        
        sessions = session_repo.get_user_sessions(
            user_id=user_id,
            active_only=True
        )
        
        return {
            "sessions": [
                {
                    "session_id": str(s.id),
                    "ip_address": s.ip_address,
                    "user_agent": s.user_agent,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                }
                for s in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话列表失败: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    撤销指定会话
    
    用于登出特定设备
    """
    try:
        from ..repositories.session_repository import SessionRepository
        
        session_repo = SessionRepository(db)
        user_id = current_user.get("user_id")
        
        # 验证会话属于当前用户
        session = session_repo.get_session_by_id(session_id)
        if not session or str(session.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 停用会话
        success = session_repo.deactivate_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="撤销会话失败"
            )
        
        db.commit()
        
        return {"message": "会话已撤销"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销会话失败: {str(e)}"
        )

