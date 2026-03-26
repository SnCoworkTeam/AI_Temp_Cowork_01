"""
使用 RS256 公钥校验 IDP 下发的 id_token（JWT）。
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import jwt
from jwt.exceptions import InvalidTokenError

from ..config import settings

logger = logging.getLogger(__name__)


def load_public_key_pem() -> str:
    """从配置读取 PEM 公钥（环境变量整段或文件路径）。"""
    if settings.SSO_ID_TOKEN_PUBLIC_KEY and settings.SSO_ID_TOKEN_PUBLIC_KEY.strip():
        return settings.SSO_ID_TOKEN_PUBLIC_KEY.strip()
    # 读取优先级：
    # 1) 显式环境变量路径（容器部署默认指向 /app/keys/...）
    # 2) 项目内相对路径（便于重部署时仅替换项目文件）
    # 3) 历史兼容路径（最后兜底）
    candidate_paths = []
    if settings.SSO_ID_TOKEN_PUBLIC_KEY_PATH:
        candidate_paths.append(settings.SSO_ID_TOKEN_PUBLIC_KEY_PATH)
    candidate_paths.extend(
        [
            # 项目内相对路径（建议通过 compose 挂载到容器内同路径或 /app/keys）
            "sso/idp/jwt_public_key_pkc8.pem",
            "keys/jwt_public_key_pkc8.pem",
            r"C:\IDP_AIOS_Key\jwt_public_key_pkc8.pem",
        ]
    )
    for path_str in candidate_paths:
        path = Path(path_str)
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise ValueError(
        "未配置 id_token 验签公钥：请设置 SSO_ID_TOKEN_PUBLIC_KEY 或 SSO_ID_TOKEN_PUBLIC_KEY_PATH"
    )


def verify_id_token_rs256(id_token: str) -> Dict[str, Any]:
    """
    校验 id_token 签名与可选 iss/aud，返回 payload。
    """
    pem = load_public_key_pem()
    verify_aud = bool(settings.SSO_ID_TOKEN_AUDIENCE)
    verify_iss = bool(settings.SSO_ID_TOKEN_ISSUER)
    try:
        payload = jwt.decode(
            id_token,
            pem,
            algorithms=["RS256"],
            audience=settings.SSO_ID_TOKEN_AUDIENCE if verify_aud else None,
            issuer=settings.SSO_ID_TOKEN_ISSUER if verify_iss else None,
            options={"verify_aud": verify_aud, "verify_iss": verify_iss},
        )
        return payload
    except InvalidTokenError as e:
        logger.warning(f"id_token 校验失败: {e}")
        raise
    except Exception as e:
        logger.error(f"id_token 处理异常: {e}", exc_info=True)
        raise


def extract_login_identity(payload: Dict[str, Any]) -> tuple[str, Optional[str]]:
    """
    从 claims 解析本地登录用用户名与邮箱。
    优先 preferred_username / username / name，否则使用 sub。
    """
    # 兼容某些 IDP 文档中的业务约定：error=0 才视为成功
    if "error" in payload and str(payload.get("error")) not in {"0", ""}:
        raise ValueError(f"IDP 返回 error={payload.get('error')}")

    username = (
        payload.get("preferred_username")
        or payload.get("username")
        or payload.get("name")
        or payload.get("sub")
    )
    if not username or not str(username).strip():
        raise ValueError("id_token 中缺少可用的用户标识（sub / preferred_username 等）")
    email = payload.get("email")
    if email is not None:
        email = str(email).strip() or None
    return str(username).strip(), email
