"""RAG 查询缓存 — 基于 Redis 的精确匹配缓存。

Key 格式：rag:cache:{sha256_hash前16位}
Value：JSON {"answer": str, "sources": list}
TTL：24 小时（可通过配置调整）
"""

import hashlib
import json
import logging

import redis.asyncio as redis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class RAGQueryCache:
    """RAG 查询缓存 — 精确匹配，命中直接返回（0 token）。"""

    def __init__(self):
        settings = get_settings()
        self.redis = redis.from_url(settings.rag_redis_url)
        self.ttl = settings.rag_cache_ttl
        self.prefix = "rag:cache:v2:"

    def _make_key(self, query: str) -> str:
        """生成缓存 key — 基于 query 的归一化哈希。"""
        normalized = query.strip().lower()
        normalized = " ".join(normalized.split())  # 合并多余空格
        hash_val = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"{self.prefix}{hash_val}"

    async def get(self, query: str) -> dict | None:
        """精确匹配查询缓存。返回 {"answer": str, "sources": list} 或 None。"""
        key = self._make_key(query)
        data = await self.redis.get(key)
        if data:
            logger.debug("缓存命中 | key=%s", key)
            return json.loads(data)
        return None

    async def set(self, query: str, answer: str, sources: list):
        """写入缓存。"""
        key = self._make_key(query)
        value = json.dumps(
            {"answer": answer, "sources": sources},
            ensure_ascii=False,
        )
        await self.redis.setex(key, self.ttl, value)
        logger.debug("缓存写入 | key=%s ttl=%d", key, self.ttl)

    async def invalidate(self, query: str):
        """手动失效某条缓存。"""
        key = self._make_key(query)
        await self.redis.delete(key)

    async def invalidate_all(self):
        """清空所有 RAG 缓存（文档更新时调用）。"""
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=f"{self.prefix}*", count=100,
            )
            if keys:
                await self.redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        logger.info("RAG 缓存已清空 | deleted=%d", deleted)
