"""用户画像 — 从对话历史中提取购物偏好，存储在 Redis。

技术栈：
- 存储：Redis db3（与 session 共用，key 前缀隔离）
- 提取：DeepSeek Chat LLM（轻量 prompt，每轮 ~200 token）
- 策略：每轮对话后异步提取，merge 到已有画像（增量更新）

画像标识：username（JWT sub 字段），跨 session 累积。
"""

import json
import logging
from datetime import datetime
from typing import Optional

import redis.asyncio as redis

from app.config.constants import ProfileDefaults
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

PROFILE_EXTRACTION_PROMPT = """\
你是一个用户偏好分析助手。请从以下最近的对话中提取用户的购物偏好信息。

只提取用户**明确表达**或**强烈暗示**的偏好，不要猜测。
如果对话中没有包含任何偏好信息，输出空 JSON {{}}。

输出 JSON 格式：
{{
    "preferred_categories": ["品类1", "品类2"],
    "price_range": {{"min": 数字, "max": 数字}},
    "brand_preferences": ["品牌1"],
    "style_preferences": ["风格1"],
    "disliked": ["不喜欢的东西"],
    "use_cases": ["使用场景"],
    "last_order_interest": "最近关注的商品类型"
}}

字段说明：
- preferred_categories: 商品品类偏好（如"手机"、"耳机"）
- price_range: 价格区间（仅在用户明确提到预算时提取）
- brand_preferences: 品牌偏好
- style_preferences: 风格偏好（如"简约"、"商务"）
- disliked: 用户明确表示不喜欢的东西
- use_cases: 使用场景（如"办公"、"通勤"）
- last_order_interest: 最近关注的商品类型（字符串，覆盖更新）

最近对话：
{history}

输出 JSON："""


# ---------------------------------------------------------------------------
# 核心类
# ---------------------------------------------------------------------------


class UserProfileStore:
    """用户画像存储 — Redis 实现，支持提取、merge、查询。"""

    def __init__(self) -> None:
        settings = get_settings()
        self.redis = redis.from_url(settings.session_redis_url)
        self._prefix = ProfileDefaults.PROFILE_KEY_PREFIX

    def _make_key(self, username: str) -> str:
        """生成 Redis key。"""
        return f"{self._prefix}{username}"

    # ── CRUD ──────────────────────────────────────────

    async def get_profile(self, username: str) -> Optional[dict]:
        """获取用户画像，不存在返回 None。"""
        key = self._make_key(username)
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            logger.warning("读取用户画像失败 | username=%s", username, exc_info=True)
        return None

    async def save_profile(self, username: str, profile: dict) -> None:
        """保存用户画像（覆盖写入，无 TTL，永久保留）。"""
        key = self._make_key(username)
        try:
            profile[ProfileDefaults.FIELD_UPDATED_AT] = datetime.now().isoformat()
            await self.redis.set(
                key,
                json.dumps(profile, ensure_ascii=False),
            )
        except Exception:
            logger.warning("写入用户画像失败 | username=%s", username, exc_info=True)

    async def delete_profile(self, username: str) -> bool:
        """删除用户画像。"""
        key = self._make_key(username)
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception:
            logger.warning("删除用户画像失败 | username=%s", username, exc_info=True)
            return False

    # ── 提取 & 合并 ──────────────────────────────────

    async def extract_and_merge(
        self,
        username: str,
        chat_history: list[dict],
    ) -> Optional[dict]:
        """从对话历史中提取偏好并与已有画像 merge。

        流程：取最近 N 轮对话 → LLM 提取偏好 JSON → merge 到已有画像 → 保存。

        Args:
            username: 用户名（JWT sub 字段）
            chat_history: [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            更新后的画像 dict，失败返回 None
        """
        if not chat_history:
            return None

        # 只取最近 N 条消息
        recent = chat_history[-ProfileDefaults.EXTRACTION_WINDOW_SIZE:]
        history_text = "\n".join(
            f"{'用户' if m.get('role') == 'user' else '助手'}：{m.get('content', '')[:ProfileDefaults.EXTRACTION_CONTENT_LIMIT]}"
            for m in recent
        )

        prompt = PROFILE_EXTRACTION_PROMPT.format(history=history_text)

        try:
            from app.agent.llm import create_llm

            llm = create_llm()
            response = await llm.ainvoke(prompt)
            extracted = self._parse_json(response.content)

            if not extracted:
                logger.debug("未从对话中提取到有效偏好 | username=%s", username)
                return None

            # merge 到已有画像
            existing = await self.get_profile(username) or {}
            merged = self._merge(existing, extracted)
            merged[ProfileDefaults.FIELD_EXTRACT_COUNT] = (
                existing.get(ProfileDefaults.FIELD_EXTRACT_COUNT, 0) + 1
            )

            await self.save_profile(username, merged)
            logger.info(
                "用户画像已更新 | username=%s fields=%s extract_count=%d",
                username,
                list(extracted.keys()),
                merged[ProfileDefaults.FIELD_EXTRACT_COUNT],
            )
            return merged

        except Exception:
            logger.warning("用户画像提取失败 | username=%s", username, exc_info=True)
            return None

    # ── 格式化 ───────────────────────────────────────

    def format_for_prompt(self, profile: dict) -> str:
        """将画像格式化为可注入 system prompt 的文本片段。

        Returns:
            格式化的文本，无有效内容时返回空字符串。
        """
        if not profile:
            return ""

        parts = ["【用户偏好（自动学习）】"]

        # 列表类字段
        list_fields = [
            (ProfileDefaults.FIELD_CATEGORIES, "偏好品类"),
            (ProfileDefaults.FIELD_BRANDS, "偏好品牌"),
            (ProfileDefaults.FIELD_STYLES, "风格偏好"),
            (ProfileDefaults.FIELD_DISLIKED, "不喜欢"),
            (ProfileDefaults.FIELD_USE_CASES, "使用场景"),
        ]
        for field_key, label in list_fields:
            values = profile.get(field_key, [])
            if values:
                parts.append(f"- {label}：{'、'.join(values)}")

        # 价格区间
        price = profile.get(ProfileDefaults.FIELD_PRICE_RANGE)
        if price and price.get("max"):
            min_p = price.get("min", 0)
            max_p = price["max"]
            parts.append(f"- 预算范围：¥{min_p} ~ ¥{max_p}")

        # 最近关注
        interest = profile.get(ProfileDefaults.FIELD_INTEREST)
        if interest:
            parts.append(f"- 最近关注：{interest}")

        # 没有实际内容
        if len(parts) == 1:
            return ""

        return "\n".join(parts)

    # ── 内部方法 ──────────────────────────────────────

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """解析 LLM 返回的 JSON，兼容 markdown 代码块包裹。"""
        try:
            text = raw.strip()
            # 清理 markdown 代码块
            if text.startswith("```"):
                first_newline = text.find("\n")
                if first_newline != -1:
                    text = text[first_newline + 1:]
                text = text.rstrip("`").strip()
            return json.loads(text)
        except (json.JSONDecodeError, AttributeError):
            return {}

    @staticmethod
    def _merge(existing: dict, new_data: dict) -> dict:
        """智能 merge 两份画像数据。

        规则：
        - 列表字段：取并集，去重，保留顺序，最多 MAX_LIST_SIZE 个
        - price_range：取交集（收紧范围）
        - 字符串字段：新值覆盖旧值
        """
        merged = dict(existing)
        max_list = ProfileDefaults.MAX_LIST_SIZE

        for key, value in new_data.items():
            if not value:
                continue

            # 列表字段：合并去重
            if key in ProfileDefaults.LIST_FIELDS:
                existing_list = merged.get(key, [])
                if isinstance(value, list):
                    # 保序去重（dict.fromkeys 保持插入顺序）
                    combined = list(dict.fromkeys(existing_list + value))
                    merged[key] = combined[:max_list]
                elif isinstance(value, str) and value not in existing_list:
                    merged[key] = (existing_list + [value])[:max_list]

            # 价格范围：取交集
            elif key == ProfileDefaults.FIELD_PRICE_RANGE and isinstance(value, dict):
                old_range = merged.get(ProfileDefaults.FIELD_PRICE_RANGE, {})
                new_min = max(old_range.get("min", 0), value.get("min", 0))
                old_max = old_range.get("max", float("inf"))
                new_max = min(old_max, value.get("max", float("inf")))
                if new_min <= new_max:
                    merged[ProfileDefaults.FIELD_PRICE_RANGE] = {
                        "min": new_min,
                        "max": new_max,
                    }

            # 字符串字段：直接覆盖
            elif key == ProfileDefaults.FIELD_INTEREST:
                merged[key] = value

        return merged


# 全局单例
user_profile_store = UserProfileStore()
