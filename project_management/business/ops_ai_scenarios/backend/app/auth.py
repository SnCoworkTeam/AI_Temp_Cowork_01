from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from .config import settings


security = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    if not settings.AUTH_ENABLED:
        return {"user_id": "anonymous", "username": "anonymous", "roles": []}

    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token") if request else None

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(token)
    return {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
        "token": token,
    }

