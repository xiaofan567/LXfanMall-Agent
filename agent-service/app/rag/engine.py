"""RAG 查询引擎 — 基于 RetrievalEngine 的编排层。

职责：
1. 调用 RetrievalEngine 执行混合检索
2. 多轮对话上下文改写
3. 构建 RAG 提示词并调用 LLM 生成回答
4. 引用插入与置信度计算
5. 流式 / 非流式两种输出模式

架构：
┌─────────────────────────────────────────────────────────┐
│  用户提问 + 可选 chat_history                             │
│      │                                                   │
│      ▼                                                   │
│  ┌─ Redis 缓存命中？ ─┐                                  │
│  │   YES              │  NO                              │
│  │   → 直接返回        │  │                               │
│  └────────────────────┘  ▼                               │
│              chat_history → LLM 改写查询                   │
│                          │                               │
│                          ▼                               │
│              RetrievalEngine.retrieve()                   │
│              (向量 + 关键词混合检索 + 可选重排)              │
│                          │                               │
│                          ▼                               │
│              _build_rag_prompt() → LLM 生成回答           │
│                          │                               │
│                          ▼                               │
│              retrieve_with_citation() → 插入引用           │
│                          │                               │
│                          ▼                               │
│              计算置信度 → RAGResponse                      │
└─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import AsyncGenerator

from app.config.settings import get_settings
from app.rag.query_cache import RAGQueryCache
from app.rag.retrieval import RetrievalEngine, RetrievalResult, Citation
from app.rag.reranker import Reranker
from app.rag.vector_store import MilvusVectorStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class RAGResponse:
    """RAG 查询统一返回结构。"""

    answer: str = ""
    sources: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    search_method: str = ""
    from_cache: bool = False
    citations: list[dict] = field(default_factory=list)

    def __getitem__(self, key: str):
        """支持 dict 风格访问，保持与旧版 dict 返回值的向后兼容。"""
        return getattr(self, key)

    def get(self, key: str, default=None):
        """支持 dict 风格 .get() 访问。"""
        return getattr(self, key, default)


# ---------------------------------------------------------------------------
# RAG Prompt 模板（中文电商客服场景）
# ---------------------------------------------------------------------------
RAG_PROMPT_TEMPLATE = """\
你是 LXfanMall 商城的智能客服助手。请严格根据下方【参考资料】回答用户问题。

## 回答规范
1. 直接给出详细、完整的回答，不要提及"根据资料""参考文档"等字眼
2. 以自然、友好的客服口吻组织语言，像在和用户聊天一样
3. 不要暴露任何内部标记（如 Q1、Q28、问题编号、文档标题等）
4. 如果资料中有具体数据（金额、比例、条件等），准确引用
5. 如果资料不足以完整回答问题，基于已有信息合理补充，但标注"具体以页面显示为准"
6. 适当使用分点列表，让回答清晰易读
7. 如果用户问题与之前的对话相关，请结合上下文理解并回答

## 参考资料
{context}

## 用户问题
{question}
"""

QUERY_REWRITE_PROMPT = """\
你是一个查询改写助手。请根据对话历史，将用户的最新问题改写为一个独立、完整的搜索查询。
要求：
1. 消除代词歧义（如"它""这个"指代什么）
2. 补充必要的上下文信息
3. 保留用户原始意图
4. 只输出改写后的查询，不要解释

对话历史：
{history}

用户最新问题：{question}

改写后的查询："""


# ---------------------------------------------------------------------------
# RAGEngine
# ---------------------------------------------------------------------------
class RAGEngine:
    """RAG 查询引擎 — 基于 RetrievalEngine 的编排层。"""

    def __init__(self):
        self.settings = get_settings()
        # Lazy-initialized dependencies
        self._retrieval_engine: RetrievalEngine | None = None
        self._embedder = None
        self._vector_store = None
        self._cache: RAGQueryCache | None = None
        self._reranker: Reranker | None = None

    # ------------------------------------------------------------------
    # Lazy property accessors
    # ------------------------------------------------------------------
    @property
    def vector_store(self) -> MilvusVectorStore:
        if self._vector_store is None:
            self._vector_store = MilvusVectorStore()
        return self._vector_store

    @property
    def embedder(self):
        if self._embedder is None:
            from app.rag.embedder import QwenEmbedder
            self._embedder = QwenEmbedder()
        return self._embedder

    @property
    def cache(self) -> RAGQueryCache:
        if self._cache is None:
            self._cache = RAGQueryCache()
        return self._cache

    @property
    def reranker(self) -> Reranker:
        if self._reranker is None:
            self._reranker = Reranker()
        return self._reranker

    @property
    def retrieval_engine(self) -> RetrievalEngine:
        if self._retrieval_engine is None:
            self._retrieval_engine = RetrievalEngine(
                vector_store=self.vector_store,
                embedder=self.embedder,
                reranker=self.reranker,
                cache=self.cache,
            )
        return self._retrieval_engine

    # ------------------------------------------------------------------
    # 公开接口 — 非流式查询
    # ------------------------------------------------------------------
    async def query(
        self,
        question: str,
        top_k: int = 5,
        doc_type: str | None = None,
        file_filter: str | None = None,
        chat_history: list[dict] | None = None,
    ) -> RAGResponse:
        """执行 RAG 查询并返回完整回答。

        Args:
            question:    用户问题
            top_k:       返回的参考文档数量
            doc_type:    文档类型过滤
            file_filter: 文件名过滤
            chat_history: 对话历史 [{role: str, content: str}, ...]

        Returns:
            RAGResponse 包含 answer, sources, confidence, citations 等
        """
        # ── 第 1 步：Redis 精确缓存（仅对无历史的简单查询）──
        if not chat_history:
            try:
                cached = await self.cache.get(question)
            except Exception:
                cached = None
                logger.warning("Redis 缓存读取失败，跳过缓存", exc_info=True)

            if cached:
                logger.info("RAG 缓存命中 | query=%s", question[:50])
                return RAGResponse(
                    answer=cached.get("answer", ""),
                    sources=cached.get("sources", []),
                    confidence=0.95,
                    search_method="cache_hit",
                    from_cache=True,
                    citations=[],
                )

        # ── 第 2 步：多轮对话 — 改写查询 ──
        effective_query = question
        if chat_history:
            effective_query = await self._rewrite_query_with_history(
                question, chat_history,
            )
            logger.info(
                "查询改写 | 原始=%s → 改写=%s",
                question[:40], effective_query[:40],
            )

        # ── 第 3 步：RetrievalEngine 混合检索 ──
        retrieval_result: RetrievalResult = await self.retrieval_engine.retrieve(
            query=effective_query,
            top_k=top_k,
            doc_type=doc_type,
            file_filter=file_filter,
        )

        if not retrieval_result.chunks:
            return RAGResponse(
                answer="抱歉，暂未找到与您问题相关的知识信息。",
                sources=[],
                confidence=0.0,
                search_method=retrieval_result.search_method,
                from_cache=retrieval_result.from_cache,
                citations=[],
            )

        logger.info(
            "RAG 检索完成 | query=%s method=%s chunks=%d top_score=%.4f",
            effective_query[:30],
            retrieval_result.search_method,
            len(retrieval_result.chunks),
            retrieval_result.scores[0] if retrieval_result.scores else 0.0,
        )

        # ── 第 4 步：构建提示词并调用 LLM ──
        prompt = self._build_rag_prompt(question, retrieval_result.chunks, chat_history)
        answer = await self._generate_answer(prompt)

        # ── 第 5 步：引用插入 ──
        citations = await self._generate_citations(question, answer)

        # ── 第 6 步：格式化 sources & 计算置信度 ──
        sources = [self._format_source(chunk) for chunk in retrieval_result.chunks]
        confidence = self._calculate_confidence(retrieval_result.scores)

        # ── 第 7 步：写入缓存（仅无历史的简单查询）──
        if not chat_history:
            try:
                await self.cache.set(question, answer, sources)
            except Exception:
                logger.warning("Redis 缓存写入失败", exc_info=True)

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            search_method=retrieval_result.search_method,
            from_cache=retrieval_result.from_cache,
            citations=[self._format_citation(c) for c in citations],
        )

    # ------------------------------------------------------------------
    # 公开接口 — 流式查询
    # ------------------------------------------------------------------
    async def query_stream(
        self,
        question: str,
        top_k: int = 5,
        doc_type: str | None = None,
        file_filter: str | None = None,
        chat_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """执行 RAG 查询并以流式方式逐 token 返回回答。

        与 query() 流程相同，但 LLM 调用改为流式输出。

        Yields:
            str: 单个 token / 片段
        """
        # ── 缓存命中 → 一次性返回 ──
        if not chat_history:
            try:
                cached = await self.cache.get(question)
            except Exception:
                cached = None

            if cached:
                yield cached.get("answer", "")
                return

        # ── 查询改写 ──
        effective_query = question
        if chat_history:
            effective_query = await self._rewrite_query_with_history(
                question, chat_history,
            )

        # ── 混合检索 ──
        retrieval_result: RetrievalResult = await self.retrieval_engine.retrieve(
            query=effective_query,
            top_k=top_k,
            doc_type=doc_type,
            file_filter=file_filter,
        )

        if not retrieval_result.chunks:
            yield "抱歉，暂未找到与您问题相关的知识信息。"
            return

        # ── 构建提示词 ──
        prompt = self._build_rag_prompt(question, retrieval_result.chunks, chat_history)

        # ── LLM 流式生成 ──
        full_answer_parts: list[str] = []
        async for token in self._generate_answer_stream(prompt):
            full_answer_parts.append(token)
            yield token

        # ── 后处理：引用 + 缓存（在后台完成，不阻塞流式输出）──
        full_answer = "".join(full_answer_parts)
        try:
            citations = await self._generate_citations(question, full_answer)
            sources = [self._format_source(chunk) for chunk in retrieval_result.chunks]
            if not chat_history and full_answer:
                try:
                    await self.cache.set(question, full_answer, sources)
                except Exception:
                    pass
        except Exception:
            logger.warning("流式查询后处理失败", exc_info=True)

    # ------------------------------------------------------------------
    # 内部方法 — 构建 RAG 提示词
    # ------------------------------------------------------------------
    def _build_rag_prompt(
        self,
        question: str,
        contexts: list[dict],
        chat_history: list[dict] | None = None,
    ) -> str:
        """构建 RAG 提示词，将检索到的上下文片段拼入模板。"""
        context_parts: list[str] = []
        for i, ctx in enumerate(contexts, 1):
            content = ctx.get("content", "")
            file_name = ctx.get("file_name", "")
            header = f"【文档 {i}】"
            if file_name:
                header += f" 来源: {file_name}"
            context_parts.append(f"{header}\n{content}")

        context_text = "\n\n".join(context_parts)

        # 如果有对话历史，将其追加到用户问题前
        question_with_history = question
        if chat_history:
            history_lines: list[str] = []
            for msg in chat_history[-6:]:  # 最多取最近 6 轮
                role = "用户" if msg.get("role") == "user" else "助手"
                history_lines.append(f"{role}：{msg.get('content', '')}")
            history_text = "\n".join(history_lines)
            question_with_history = f"对话历史：\n{history_text}\n\n当前问题：{question}"

        return RAG_PROMPT_TEMPLATE.format(
            context=context_text,
            question=question_with_history,
        )

    # ------------------------------------------------------------------
    # 内部方法 — 计算置信度
    # ------------------------------------------------------------------
    @staticmethod
    def _calculate_confidence(scores: list[float]) -> float:
        """根据检索分数聚合置信度。

        策略：加权平均，Top1 权重最高，随排名递减。
        """
        if not scores:
            return 0.0

        # 加权：Top1 权重 0.5，后续递减
        total_weight = 0.0
        weighted_sum = 0.0
        for i, score in enumerate(scores):
            weight = 1.0 / (i + 2)  # i=0 → 0.5, i=1 → 0.33, i=2 → 0.25 ...
            weighted_sum += score * weight
            total_weight += weight

        raw_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        # 将 [0, 1] 分数映射到更合理的置信度区间 [0, 0.98]
        # 避免置信度为 1.0（过于绝对）
        return min(round(raw_confidence * 0.98, 4), 0.98)

    # ------------------------------------------------------------------
    # 内部方法 — 多轮对话查询改写
    # ------------------------------------------------------------------
    async def _rewrite_query_with_history(
        self,
        question: str,
        chat_history: list[dict],
    ) -> str:
        """利用 LLM 根据对话历史改写用户查询，消除指代歧义。

        如果改写失败，返回原始问题。
        """
        # 组装历史摘要（最近 6 轮）
        history_lines: list[str] = []
        for msg in chat_history[-6:]:
            role = "用户" if msg.get("role") == "user" else "助手"
            content = msg.get("content", "")
            if content:
                history_lines.append(f"{role}：{content[:200]}")

        if not history_lines:
            return question

        history_text = "\n".join(history_lines)

        prompt = QUERY_REWRITE_PROMPT.format(
            history=history_text,
            question=question,
        )

        try:
            from app.agent.llm import create_llm
            llm = create_llm()
            response = await llm.ainvoke(prompt)
            rewritten = response.content.strip()

            # 基本校验：改写结果不能为空或过长
            if rewritten and 2 < len(rewritten) < 500:
                return rewritten
        except Exception:
            logger.warning("查询改写失败，使用原始查询", exc_info=True)

        return question

    # ------------------------------------------------------------------
    # 内部方法 — LLM 生成
    # ------------------------------------------------------------------
    async def _generate_answer(self, prompt: str) -> str:
        """调用 LLM 生成回答（非流式）。"""
        from app.agent.llm import create_llm
        llm = create_llm()
        try:
            response = await llm.ainvoke(prompt)
            return response.content
        except Exception:
            logger.error("LLM 生成回答失败", exc_info=True)
            return "抱歉，系统暂时无法生成回答，请稍后再试。"

    async def _generate_answer_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """调用 LLM 生成回答（流式）。"""
        from app.agent.llm import create_llm
        llm = create_llm()
        try:
            async for chunk in llm.astream(prompt):
                if chunk.content:
                    yield chunk.content
        except Exception:
            logger.error("LLM 流式生成失败", exc_info=True)
            yield "抱歉，系统暂时无法生成回答，请稍后再试。"

    # ------------------------------------------------------------------
    # 内部方法 — 引用生成
    # ------------------------------------------------------------------
    async def _generate_citations(
        self,
        question: str,
        answer: str,
    ) -> list[Citation]:
        """为回答生成引用标注。"""
        try:
            return await self.retrieval_engine.retrieve_with_citation(
                query=question,
                answer=answer,
                top_k=5,
            )
        except Exception:
            logger.warning("引用生成失败", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # 格式化工具
    # ------------------------------------------------------------------
    @staticmethod
    def _format_source(doc: dict) -> dict:
        """格式化单条参考来源。"""
        return {
            "file_name": doc.get("file_name", ""),
            "content": doc.get("content", "")[:500],
            "score": round(doc.get("score", 0.0), 4),
            "metadata": doc.get("metadata", {}),
        }

    @staticmethod
    def _format_citation(citation: Citation) -> dict:
        """格式化单条引用。"""
        return {
            "sentence": citation.sentence,
            "source_file": citation.source_file,
            "score": round(citation.score, 4),
        }
