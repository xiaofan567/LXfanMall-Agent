# -*- coding: utf-8 -*-
"""
Hybrid Retrieval Engine for RAG Pipeline.

Orchestrates the full retrieval pipeline inspired by RAGFlow's search.py Dealer class:
query building → synonym expansion → hybrid search → reranking → citation insertion.
Optimized for e-commerce with slightly higher keyword weight for product-specific queries.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.nlp.keyword_extractor import KeywordExtractor
    from app.nlp.query_builder import QueryBuilder
    from app.nlp.tokenizer import Tokenizer
    from app.rag.embedder import QwenEmbedder
    from app.rag.query_cache import RAGQueryCache
    from app.rag.reranker import Reranker
    from app.rag.vector_store import MilvusVectorStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_VECTOR_WEIGHT = 0.7   # e-commerce: balanced toward vector for semantic
DEFAULT_KEYWORD_WEIGHT = 0.3  # slightly higher keyword weight for product names
SIMILARITY_THRESHOLD = 0.4    # minimum score to include a chunk
RERANK_TRIGGER_THRESHOLD = 0.85  # rerank only when top result is below this
CITATION_THRESHOLD = 0.5      # minimum score to attach a citation
DEFAULT_CACHE_TTL = 3600      # 1 hour
SENTENCE_DELIMITERS = (".", "。", "！", "？", "!", "?")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class RetrievalResult:
    """Result of a retrieval pipeline execution."""

    query: str
    chunks: list[dict] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    from_cache: bool = False
    search_method: str = "hybrid"
    total_found: int = 0


@dataclass
class Citation:
    """A citation linking a sentence in an answer to a source chunk."""

    sentence: str
    chunk_id: str
    chunk_content: str
    score: float
    source_file: str = ""


# ---------------------------------------------------------------------------
# Retrieval engine
# ---------------------------------------------------------------------------
class RetrievalEngine:
    """
    Hybrid retrieval engine that orchestrates:
    1. Query building & synonym expansion
    2. Vector embedding
    3. Hybrid search (vector + keyword)
    4. Optional reranking
    5. Score-based filtering
    6. Caching
    7. Citation insertion
    """

    def __init__(
        self,
        vector_store: MilvusVectorStore,
        embedder: QwenEmbedder,
        reranker: Reranker | None = None,
        cache: RAGQueryCache | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder
        self._reranker = reranker
        self._cache = cache

        # Lazy-loaded NLP helpers (set via configure_nlp)
        self._query_builder: QueryBuilder | None = None
        self._keyword_extractor: KeywordExtractor | None = None
        self._tokenizer: Tokenizer | None = None

    # ------------------------------------------------------------------
    # Optional NLP configuration
    # ------------------------------------------------------------------
    def configure_nlp(
        self,
        query_builder: QueryBuilder | None = None,
        keyword_extractor: KeywordExtractor | None = None,
        tokenizer: Tokenizer | None = None,
    ) -> None:
        """Inject NLP dependencies for query processing."""
        self._query_builder = query_builder
        self._keyword_extractor = keyword_extractor
        self._tokenizer = tokenizer

    # ------------------------------------------------------------------
    # Cache helpers (fail-open)
    # ------------------------------------------------------------------
    async def _try_cache_get(self, query: str) -> RetrievalResult | None:
        if self._cache is None:
            return None
        try:
            cached = await self._cache.get(query)
            if cached is None:
                return None
            # cache.get 返回的是 JSON 字符串或 dict
            if isinstance(cached, str):
                cached = json.loads(cached)
            if isinstance(cached, dict) and "chunks" in cached:
                return RetrievalResult(
                    query=cached.get("query", query),
                    chunks=cached.get("chunks", []),
                    scores=cached.get("scores", []),
                    from_cache=True,
                    search_method=cached.get("search_method", "hybrid"),
                    total_found=cached.get("total_found", 0),
                )
            return None
        except Exception:
            logger.warning("Cache GET failed for query=%r", query, exc_info=True)
            return None

    async def _try_cache_set(self, query: str, result: RetrievalResult, ttl: int = DEFAULT_CACHE_TTL) -> None:
        if self._cache is None:
            return
        try:
            # 将 RetrievalResult 序列化为 cache 兼容的格式
            cache_data = {
                "query": result.query,
                "chunks": result.chunks,
                "scores": result.scores,
                "search_method": result.search_method,
                "total_found": result.total_found,
            }
            await self._cache.set(query, json.dumps(cache_data, ensure_ascii=False), [])
        except Exception:
            logger.warning("Cache SET failed for query=%r", query, exc_info=True)

    # ------------------------------------------------------------------
    # Query processing helpers
    # ------------------------------------------------------------------
    def _build_weighted_query(self, query: str) -> dict:
        """Build a weighted query structure using QueryBuilder."""
        if self._query_builder is not None:
            try:
                return self._query_builder.build_weighted_query(
                    query,
                    title_weight=1.2,
                    keyword_weight=1.0,
                    content_weight=0.8,
                )
            except Exception:
                logger.warning("QueryBuilder.build_weighted_query failed", exc_info=True)
        # Fallback: treat the whole query as content
        return {"title": "", "keywords": "", "content": query}

    def _expand_with_synonyms(self, query: str) -> str:
        """Expand the query with synonym substitution."""
        if self._query_builder is not None:
            try:
                return self._query_builder.expand_with_synonyms(query)
            except Exception:
                logger.warning("QueryBuilder.expand_with_synonyms failed", exc_info=True)
        return query

    # ------------------------------------------------------------------
    # Reranking helper (fail-open)
    # ------------------------------------------------------------------
    async def _maybe_rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int,
    ) -> list[dict]:
        """
        Rerank documents when the top result score is below the trigger threshold.
        Falls back to the original ranking on failure.
        """
        if self._reranker is None:
            return documents

        top_score = 0.0
        if documents:
            top_score = documents[0].get("score", 0.0)

        if top_score >= RERANK_TRIGGER_THRESHOLD:
            return documents

        try:
            reranked = await self._reranker.rerank(query, documents, top_k=top_k)
            if reranked:
                logger.info(
                    "Reranker produced %d results (top_score %.4f → %.4f)",
                    len(reranked),
                    top_score,
                    reranked[0].get("score", 0.0),
                )
                return reranked
        except Exception:
            logger.warning("Reranker failed, returning original ranking", exc_info=True)

        return documents

    # ------------------------------------------------------------------
    # Main retrieval pipeline
    # ------------------------------------------------------------------
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        doc_type: str | None = None,
        file_filter: str | None = None,
        use_cache: bool = True,
    ) -> RetrievalResult:
        """
        Execute the full hybrid retrieval pipeline.

        Steps:
        1. Check cache
        2. Build weighted query
        3. Expand with synonyms
        4. Embed the query
        5. Hybrid search (vector + keyword)
        6. Conditional reranking
        7. Filter by similarity threshold
        8. Cache result
        """
        # -- 1. Cache check ------------------------------------------------
        if use_cache:
            cached = await self._try_cache_get(query)
            if cached is not None:
                logger.info("Cache HIT for query=%r", query)
                cached.from_cache = True
                return cached

        # -- 2. Build weighted query ----------------------------------------
        weighted_query = self._build_weighted_query(query)
        # Use the richest available field for search
        search_text = (
            weighted_query.get("content", "")
            or weighted_query.get("title", "")
            or query
        )

        # -- 3. Expand with synonyms ----------------------------------------
        expanded = self._expand_with_synonyms(search_text)

        # -- 4. Embed the query ---------------------------------------------
        try:
            query_vector = await self._embedder.embed_query(expanded)
        except Exception:
            logger.error("Embedding failed for query=%r", query, exc_info=True)
            # Fallback to keyword-only search
            return await self._keyword_fallback(query, top_k, doc_type, file_filter)

        # -- 5. Hybrid search -----------------------------------------------
        try:
            raw_results = await self._vector_store.hybrid_search(
                query_text=expanded,
                query_vector=query_vector,
                top_k=top_k * 3,  # over-fetch for reranking headroom
                vector_weight=DEFAULT_VECTOR_WEIGHT,
                keyword_weight=DEFAULT_KEYWORD_WEIGHT,
                file_filter=file_filter,
                doc_type_filter=doc_type,
            )
        except Exception:
            logger.error("Hybrid search failed for query=%r", query, exc_info=True)
            return RetrievalResult(query=query, search_method="hybrid", total_found=0)

        if not raw_results:
            logger.info("No results from hybrid search for query=%r", query)
            return RetrievalResult(query=query, search_method="hybrid", total_found=0)

        # -- 6. Conditional reranking ----------------------------------------
        documents = await self._maybe_rerank(query, raw_results, top_k)

        # -- 7. Filter by similarity threshold ------------------------------
        filtered = [doc for doc in documents if doc.get("score", 0.0) >= SIMILARITY_THRESHOLD]

        # Trim to top_k
        filtered = filtered[:top_k]

        chunks = filtered
        scores = [doc.get("score", 0.0) for doc in filtered]
        search_method = "hybrid+rerank" if self._reranker is not None else "hybrid"

        result = RetrievalResult(
            query=query,
            chunks=chunks,
            scores=scores,
            from_cache=False,
            search_method=search_method,
            total_found=len(chunks),
        )

        # -- 8. Cache result ------------------------------------------------
        if use_cache:
            await self._try_cache_set(query, result)

        logger.info(
            "Retrieval complete: query=%r, method=%s, found=%d, top_score=%.4f",
            query,
            search_method,
            len(chunks),
            scores[0] if scores else 0.0,
        )
        return result

    # ------------------------------------------------------------------
    # Keyword fallback (when embedding fails)
    # ------------------------------------------------------------------
    async def _keyword_fallback(
        self,
        query: str,
        top_k: int,
        doc_type: str | None,
        file_filter: str | None,
    ) -> RetrievalResult:
        """Fallback to keyword-only search when embedding is unavailable."""
        logger.info("Falling back to keyword-only search for query=%r", query)
        try:
            results = await self._vector_store.hybrid_search(
                query_text=query,
                query_vector=[],
                top_k=top_k,
                vector_weight=0.0,
                keyword_weight=1.0,
                file_filter=file_filter,
                doc_type_filter=doc_type,
            )
            chunks = results[:top_k]
            return RetrievalResult(
                query=query,
                chunks=chunks,
                scores=[doc.get("score", 0.0) for doc in chunks],
                from_cache=False,
                search_method="keyword_fallback",
                total_found=len(chunks),
            )
        except Exception:
            logger.error("Keyword fallback also failed for query=%r", query, exc_info=True)
            return RetrievalResult(query=query, search_method="keyword_fallback", total_found=0)

    # ------------------------------------------------------------------
    # Citation insertion
    # ------------------------------------------------------------------
    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences, handling both CJK and Latin delimiters."""
        import re
        # Split on sentence-ending punctuation, keeping the delimiter attached.
        pattern = r'(?<=[.。！？!?])\s*'
        sentences = re.split(pattern, text)
        # Also split on newlines for paragraphs
        expanded: list[str] = []
        for s in sentences:
            for sub in s.split("\n"):
                sub = sub.strip()
                if sub:
                    expanded.append(sub)
        return expanded

    async def retrieve_with_citation(
        self,
        query: str,
        answer: str,
        top_k: int = 5,
    ) -> list[Citation]:
        """
        Post-hoc citation insertion inspired by RAGFlow's insert_citations.

        For each sentence in the answer, find the most similar chunk from
        the knowledge base and attach it as a citation.

        Args:
            query:   Original user query.
            answer:  Generated answer text.
            top_k:   Max citations to return.

        Returns:
            List of Citation objects for sentences that match well.
        """
        sentences = self._split_sentences(answer)
        if not sentences:
            return []

        citations: list[Citation] = []

        try:
            # Embed all sentences in a single batch for efficiency
            sentence_vectors = await self._embedder.embed(sentences)
        except Exception:
            logger.warning("Batch embedding for citations failed, trying one-by-one", exc_info=True)
            sentence_vectors = []
            for s in sentences:
                try:
                    vec = await self._embedder.embed_query(s)
                    sentence_vectors.append(vec)
                except Exception:
                    sentence_vectors.append([])

        for sentence, vector in zip(sentences, sentence_vectors):
            if not vector:
                continue

            try:
                results = await self._vector_store.hybrid_search(
                    query_text=sentence,
                    query_vector=vector,
                    top_k=1,
                    vector_weight=0.8,
                    keyword_weight=0.2,
                )
            except Exception:
                logger.warning("Citation search failed for sentence=%r", sentence, exc_info=True)
                continue

            if not results:
                continue

            best = results[0]
            score = best.get("score", 0.0)
            if score < CITATION_THRESHOLD:
                continue

            citations.append(
                Citation(
                    sentence=sentence,
                    chunk_id=best.get("chunk_id", ""),
                    chunk_content=best.get("content", ""),
                    score=score,
                    source_file=best.get("source_file", best.get("file_path", "")),
                )
            )

        # Sort by score descending and cap at top_k
        citations.sort(key=lambda c: c.score, reverse=True)
        return citations[:top_k]

    # ------------------------------------------------------------------
    # Direct keyword search (no embedding)
    # ------------------------------------------------------------------
    async def keyword_search(
        self,
        keywords: list[str],
        top_k: int = 10,
        doc_type: str | None = None,
    ) -> list[dict]:
        """
        Direct keyword-only search. No embedding is computed.

        Args:
            keywords: List of keyword strings to search for.
            top_k:    Maximum number of results.
            doc_type: Optional document type filter.

        Returns:
            List of matching chunk dicts.
        """
        query_text = " ".join(keywords)
        if not query_text.strip():
            return []

        try:
            results = await self._vector_store.hybrid_search(
                query_text=query_text,
                query_vector=[],
                top_k=top_k,
                vector_weight=0.0,
                keyword_weight=1.0,
                doc_type_filter=doc_type,
            )
            return results[:top_k]
        except Exception:
            logger.error("Keyword search failed for keywords=%r", keywords, exc_info=True)
            return []
