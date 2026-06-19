"""路由处理器的共享 FastAPI 依赖项。"""

import base64
import logging
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError, jwt

from app.config.settings import get_settings
from app.core.exceptions import AuthenticationException

logger = logging.getLogger(__name__)


@dataclass
class CurrentUser:
    """从 JWT 中解析出的当前用户信息。

    Java 后端 JWT 的 sub 字段存储的是 username（非数字 ID）。
    is_admin 标识是否为 mall-admin 管理员（通过 admin_jwt_secret 验签成功）。
    """

    username: str
    token: str
    is_admin: bool = False


def _try_decode_token(token: str, secrets: list[str], algorithm: str) -> dict | None:
    """尝试用多个 secret 解码 JWT，返回第一个成功的 payload。

    Java JJWT 0.9.1 的 TextCodec.BASE64.decode 比 Python base64 更宽松，
    因此对每个 secret 同时尝试 base64 解码和原始字符串两种方式。
    """
    logger.info("JWT 验签开始 | token=%s...%s | algorithm=%s | secrets=%s",
                token[:20], token[-10:], algorithm, [s[:10]+"..." for s in secrets])

    for secret in secrets:
        # 构造候选 key 列表：base64 解码 + 原始字符串（去重）
        candidate_keys: list[tuple[str, bytes]] = []
        try:
            decoded = base64.b64decode(secret)
            candidate_keys.append(("base64", decoded))
        except Exception:
            pass
        candidate_keys.append(("raw", secret.encode("utf-8")))

        for key_type, key in candidate_keys:
            try:
                payload = jwt.decode(token, key, algorithms=[algorithm])
                logger.info("JWT 验签成功 | secret='%s' key_type=%s", secret, key_type)
                return payload
            except JWTError as e:
                logger.info("JWT 验签失败 | secret='%s' key_type=%s error=%s", secret, key_type, str(e)[:100])
                continue

    logger.warning("JWT 验签失败（已尝试 %d 个 secret，共 %d 种 key）",
                   len(secrets), sum(2 for _ in secrets))
    return None


async def get_optional_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser | None:
    """从 JWT token 中提取当前用户信息（如果存在且有效）。

    依次尝试 mall-portal 和 mall-admin 的 JWT secret 验签。
    未提供 token 或 token 无效时返回 None，允许公开端点在无认证下访问。
    """
    if not authorization:
        return None

    token = _extract_bearer_token(authorization)
    if token is None:
        return None

    settings = get_settings()

    # 收集可用的 secret（portal 必有，admin 可选）
    secrets = [settings.jwt_secret]
    if settings.admin_jwt_secret and settings.admin_jwt_secret != settings.jwt_secret:
        secrets.append(settings.admin_jwt_secret)

    payload = _try_decode_token(token, secrets, settings.jwt_algorithm)
    if payload is None:
        return None

    username = payload.get("sub")
    if not username:
        return None

    # 判断是否为 admin token（用 admin secret 验签成功）
    is_admin = False
    if settings.admin_jwt_secret:
        try:
            admin_key = base64.b64decode(settings.admin_jwt_secret)
        except Exception:
            admin_key = settings.admin_jwt_secret
        try:
            jwt.decode(token, admin_key, algorithms=[settings.jwt_algorithm])
            is_admin = True
        except JWTError:
            pass

    return CurrentUser(username=username, token=token, is_admin=is_admin)


async def require_user(
    user: CurrentUser | None = Depends(get_optional_user),
) -> CurrentUser:
    """与 get_optional_user 类似，但无有效 token 时抛出 401。"""
    if user is None:
        raise AuthenticationException()
    return user


async def require_admin(
    user: CurrentUser | None = Depends(get_optional_user),
) -> CurrentUser:
    """要求管理员身份。非管理员返回 403。"""
    if user is None:
        raise AuthenticationException()
    if not user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")
    return user


def _extract_bearer_token(authorization_header: str) -> str | None:
    """去除 Authorization 请求头中的 'Bearer ' 前缀。"""
    prefix = "Bearer "
    if authorization_header.startswith(prefix):
        return authorization_header[len(prefix):]
    return None
