"""Qwen text-embedding-v4 — 通过阿里云百炼 API 获取 Embedding。

无需下载本地模型，无需 GPU，通过 HTTP 调用即可。
API 文档：https://help.aliyun.com/zh/model-studio/text-embedding-v4
"""

import logging

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class QwenEmbedder:
    """Qwen text-embedding-v4 API Embedding（单例）。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            cls._instance.api_key = settings.embedding_api_key
            cls._instance.base_url = settings.embedding_base_url
            cls._instance.model = settings.embedding_model
            cls._instance.dimension = settings.milvus_dimension
            cls._instance._client = httpx.AsyncClient(timeout=30)
            logger.info(
                "QwenEmbedder 初始化 | model=%s dimension=%d",
                cls._instance.model, cls._instance.dimension,
            )
        return cls._instance

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """批量 embedding，用于文档入库。Qwen API 单次最多 25 条，自动分批。"""
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        batch_size = 10

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = await self._client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "input": batch,
                    "dimensions": self.dimension,
                },
            )
            if resp.status_code != 200:
                logger.error(
                    "Embedding API 响应异常 | status=%d body=%s",
                    resp.status_code, resp.text[:500],
                )
            resp.raise_for_status()
            data = resp.json()
            # 按 index 排序，保证顺序与输入一致
            sorted_items = sorted(data["data"], key=lambda x: x["index"])
            for item in sorted_items:
                all_embeddings.append(item["embedding"])

        logger.debug("Embedding 完成 | count=%d", len(all_embeddings))
        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """单条 query embedding，用于检索。"""
        results = await self.embed([query])
        return results[0]
