"""重排序模块 — 使用阿里云百炼 gte-rerank-v2 API。

仅在低相似度（score < 0.85）场景触发，提升检索精度。
API 文档：https://help.aliyun.com/zh/model-studio/reranking-api
"""

import logging

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class Reranker:
    """百炼 gte-rerank-v2 API 重排序（单例）。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            cls._instance.api_key = settings.reranker_api_key or settings.embedding_api_key
            cls._instance.base_url = settings.reranker_base_url
            cls._instance.model = settings.reranker_model
            cls._instance._client = httpx.AsyncClient(timeout=30)
            logger.info("Reranker 初始化 | model=%s", cls._instance.model)
        return cls._instance

    async def rerank(
        self, query: str, documents: list[dict], top_k: int = 5,
    ) -> list[dict]:
        """对检索结果重排序。

        Args:
            query: 用户问题
            documents: [{"content": str, "score": float, ...}, ...]
            top_k: 返回前 k 个结果

        Returns:
            重排后的结果列表，新增 rerank_score 字段。
            如果 rerank API 调用失败，降级返回原始结果。
        """
        if not documents:
            return []

        try:
            body = {
                "model": self.model,
                "input": {"query": query, "documents": [doc["content"] for doc in documents]},
                "parameters": {"top_n": min(top_k, len(documents)), "return_documents": False},
            }
            resp = await self._client.post(
                f"{self.base_url}/services/rerank/text-rerank/text-rerank",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
            )
            if resp.status_code != 200:
                logger.error("Rerank API 响应异常 | status=%d body=%s", resp.status_code, resp.text)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Rerank API 调用失败，降级使用原始排序 | error=%s", e)
            return documents[:top_k]

        data = resp.json()

        # DashScope API 返回 {"output": {"results": [{"index": 0, "relevance_score": 0.95}, ...]}}
        results = data.get("output", {}).get("results", [])
        if not results:
            logger.warning("Rerank 返回结果为空，降级使用原始排序")
            return documents[:top_k]

        for item in results:
            idx = item["index"]
            documents[idx]["rerank_score"] = item["relevance_score"]

        # 按 rerank_score 降序排列
        reranked = sorted(
            [documents[item["index"]] for item in results],
            key=lambda x: x["rerank_score"],
            reverse=True,
        )

        logger.debug(
            "重排序完成 | query=%s candidates=%d result=%d",
            query[:30], len(documents), len(reranked),
        )
        return reranked[:top_k]
