"""会话记忆管理 — Redis 持久化会话历史。

Redis Key 设计（方案 D：分层 key + latest 指针）：

    session:{username}:{uuid}   → 会话消息历史（JSON，滑动 TTL）
    session:latest:{username}   → 该用户最近活跃的 session_id（TTL 跟随 session）

匿名用户（未登录）：
    session:{uuid}              → 匿名会话（无 latest 指针）

示例：
    session:test:a1b2c3d4       → 用户 test 的会话数据
    session:latest:test         → "a1b2c3d4"（test 最近的 session）
    session:x9y8z7w6            → 匿名用户的会话
"""

import json
import logging
from datetime import datetime

import redis.asyncio as redis
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.config.constants import SessionDefaults
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# 匿名用户的特殊标识
_ANONYMOUS = "anonymous"


class RedisSessionStore:
    """基于 Redis 的会话存储，支持多实例部署。"""

    # ── 序列化标识 ──
    _ROLE_HUMAN = "human"
    _ROLE_AI = "ai"

    def __init__(self) -> None:
        settings = get_settings()
        self.redis = redis.from_url(settings.session_redis_url)
        self.ttl = settings.session_ttl
        self.max_turns = settings.session_max_turns
        self._prefix = SessionDefaults.SESSION_KEY_PREFIX

    # ── Key 生成 ──────────────────────────────────────

    def _session_key(self, username: str, session_id: str) -> str:
        """生成 session 数据的 Redis key。"""
        if username == _ANONYMOUS:
            return f"{self._prefix}{session_id}"
        return f"{self._prefix}{username}:{session_id}"

    def _latest_key(self, username: str) -> str:
        """生成 latest 指针的 Redis key。"""
        return f"{self._prefix}latest:{username}"

    # ── 序列化 ────────────────────────────────────────

    @staticmethod
    def _to_dict(msg: BaseMessage, timestamp: str | None = None, tool_results: list | None = None, pending_actions: list | None = None) -> dict:
        """单条 Message → 存储用 dict。"""
        role = "human" if isinstance(msg, HumanMessage) else "ai"
        d = {
            "role": role,
            "content": msg.content,
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        if tool_results:
            d["tool_results"] = tool_results
        if pending_actions:
            d["pending_actions"] = pending_actions
        return d

    @staticmethod
    def _from_dict(item: dict) -> BaseMessage:
        """存储用 dict → LangChain Message。"""
        if item.get("role") == "human":
            return HumanMessage(content=item.get("content", ""))
        return AIMessage(content=item.get("content", ""))

    # ── Latest 指针 ───────────────────────────────────

    async def get_latest_session_id(self, username: str) -> str | None:
        """获取用户最近活跃的 session_id，不存在返回 None。"""
        if username == _ANONYMOUS:
            return None
        key = self._latest_key(username)
        try:
            session_id = await self.redis.get(key)
            if session_id:
                return session_id.decode() if isinstance(session_id, bytes) else session_id
        except Exception:
            logger.warning("读取 latest 指针失败 | username=%s", username, exc_info=True)
        return None

    async def _update_latest_pointer(self, username: str, session_id: str) -> None:
        """更新 latest 指针（与 session 同 TTL）。"""
        if username == _ANONYMOUS:
            return
        key = self._latest_key(username)
        try:
            await self.redis.setex(key, self.ttl, session_id)
        except Exception:
            logger.warning("更新 latest 指针失败 | username=%s", username, exc_info=True)

    # ── 公开接口 ──────────────────────────────────────

    async def get_history(self, username: str, session_id: str) -> list[BaseMessage]:
        """获取指定会话的对话历史（LangChain Message 格式）。"""
        key = self._session_key(username, session_id)
        try:
            data = await self.redis.get(key)
            if data:
                raw = json.loads(data)
                return [self._from_dict(item) for item in raw]
        except Exception:
            logger.warning("Redis 会话读取失败 | session=%s", session_id, exc_info=True)
        return []

    async def add_message(
        self,
        username: str,
        session_id: str,
        message: BaseMessage,
        tool_results: list | None = None,
        pending_actions: list | None = None,
    ) -> None:
        """向指定会话追加一条消息，重置滑动过期时间，更新 latest 指针。"""
        key = self._session_key(username, session_id)
        try:
            existing_raw = await self._load_raw(username, session_id)
            existing_raw.append(self._to_dict(message, tool_results=tool_results, pending_actions=pending_actions))

            # 限制历史长度
            max_messages = self.max_turns * SessionDefaults.MESSAGES_PER_TURN
            if len(existing_raw) > max_messages:
                existing_raw = existing_raw[-max_messages:]

            serialized = json.dumps(existing_raw, ensure_ascii=False)
            await self.redis.setex(key, self.ttl, serialized)

            # 更新 latest 指针
            await self._update_latest_pointer(username, session_id)

            logger.debug(
                "会话已保存 | user=%s session=%s messages=%d",
                username, session_id, len(existing_raw),
            )
        except Exception:
            logger.warning("Redis 会话写入失败 | session=%s", session_id, exc_info=True)

    async def clear(self, username: str, session_id: str) -> None:
        """清空指定会话的历史，并清除 latest 指针（如果指向该 session）。"""
        key = self._session_key(username, session_id)
        try:
            await self.redis.delete(key)
            # 如果 latest 指向被清空的 session，也一并清除
            if username != _ANONYMOUS:
                latest = await self.get_latest_session_id(username)
                if latest == session_id:
                    await self.redis.delete(self._latest_key(username))
        except Exception:
            logger.warning("Redis 会话删除失败 | session=%s", session_id, exc_info=True)

    async def get_raw_history_dicts(self, username: str, session_id: str) -> list[dict]:
        """获取对话历史（dict 格式，含时间戳和 tool_results）。"""
        raw = await self._load_raw(username, session_id)
        result = []
        for item in raw:
            role = item.get("role", "")
            d = {
                "role": "user" if role == self._ROLE_HUMAN else "assistant",
                "content": item.get("content", ""),
                "timestamp": item.get("timestamp"),
            }
            if item.get("tool_results"):
                d["tool_results"] = item["tool_results"]
            if item.get("pending_actions"):
                d["pending_actions"] = item["pending_actions"]
            result.append(d)
        return result

    async def update_pending_action_status(
        self,
        username: str,
        session_id: str,
        action_id: str,
        status: str,
        result_message: str,
    ) -> bool:
        """更新指定消息中某个 pending_action 的确认状态。"""
        key = self._session_key(username, session_id)
        try:
            raw = await self._load_raw(username, session_id)
            # 从后往前找，找到最近一条包含该 action_id 的 assistant 消息
            for msg in reversed(raw):
                if msg.get("role") != self._ROLE_AI:
                    continue
                for pa in msg.get("pending_actions", []):
                    if pa.get("action_id") == action_id:
                        pa["_status"] = status
                        pa["_result"] = result_message
                        serialized = json.dumps(raw, ensure_ascii=False)
                        await self.redis.setex(key, self.ttl, serialized)
                        return True
            return False
        except Exception:
            logger.warning("更新 pending_action 状态失败 | session=%s action_id=%s", session_id, action_id, exc_info=True)
            return False

    # ── 内部方法 ──────────────────────────────────────

    async def _load_raw(self, username: str, session_id: str) -> list[dict]:
        """从 Redis 加载原始 dict 列表。"""
        key = self._session_key(username, session_id)
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            logger.warning("Redis 会话读取失败 | session=%s", session_id, exc_info=True)
        return []


# 全局单例
session_store = RedisSessionStore()
