"""用户画像 API — 查看和管理 AI 学习到的用户偏好。

接口：
- GET  /api/v1/user/profile  — 获取当前用户的 AI 画像
- DELETE /api/v1/user/profile — 删除画像（重置 AI 记忆）

身份识别：通过 JWT token 的 sub 字段获取 username。
"""

from fastapi import APIRouter, Depends

from app.api.v1.deps import CurrentUser, get_optional_user
from app.core.exceptions import AgentException, agent_exception_to_http
from app.memory.user_profile import user_profile_store

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile")
async def get_user_profile(
    user: CurrentUser | None = Depends(get_optional_user),
):
    """获取当前用户的 AI 画像。"""
    if not user:
        raise agent_exception_to_http(
            AgentException(code=401, message="请先登录"),
        )

    profile = await user_profile_store.get_profile(user.username)
    return {
        "code": 200,
        "data": profile,
        "message": "ok" if profile else "暂无画像数据",
    }


@router.delete("/profile")
async def delete_user_profile(
    user: CurrentUser | None = Depends(get_optional_user),
):
    """删除当前用户的 AI 画像（重置记忆）。"""
    if not user:
        raise agent_exception_to_http(
            AgentException(code=401, message="请先登录"),
        )

    deleted = await user_profile_store.delete_profile(user.username)
    return {
        "code": 200,
        "message": "画像已删除" if deleted else "暂无画像数据",
    }
