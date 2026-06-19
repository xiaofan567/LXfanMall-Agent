"""Milvus 向量存储 — 管理 mall_knowledge 集合（混合检索版）。

功能：
- Dense vector search (COSINE + IVF_FLAT)
- Keyword / BM25 search via tokenized fields
- Hybrid search: weighted score fusion of vector + keyword
- Schema migration for existing collections
"""

import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusException,
    connections,
    utility,
)

from app.config.settings import get_settings
from app.rag.embedder import QwenEmbedder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VECTOR_INDEX_PARAMS = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {"nlist": 128},
}

_SEARCH_PARAMS = {"metric_type": "COSINE", "params": {"nprobe": 16}}

# New fields added for hybrid search — used by migration logic
_HYBRID_FIELDS_SPEC: list[dict] = [
    {"name": "content_tokens", "dtype": DataType.VARCHAR, "max_length": 8192, "default": ""},
    {"name": "title", "dtype": DataType.VARCHAR, "max_length": 512, "default": ""},
    {"name": "title_tokens", "dtype": DataType.VARCHAR, "max_length": 512, "default": ""},
    {"name": "keywords", "dtype": DataType.VARCHAR, "max_length": 1024, "default": ""},
    {"name": "doc_type", "dtype": DataType.VARCHAR, "max_length": 64, "default": "general"},
]


# ---------------------------------------------------------------------------
# Helper: lazy NLP singletons
# ---------------------------------------------------------------------------

_tokenizer = None
_keyword_extractor = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from app.nlp import get_tokenizer
        _tokenizer = get_tokenizer()
    return _tokenizer


def _get_keyword_extractor():
    global _keyword_extractor
    if _keyword_extractor is None:
        from app.nlp import get_keyword_extractor
        _keyword_extractor = get_keyword_extractor()
    return _keyword_extractor


# ---------------------------------------------------------------------------
# MilvusVectorStore
# ---------------------------------------------------------------------------


class MilvusVectorStore:
    """Milvus 向量存储，支持 dense vector + keyword 混合检索。"""

    def __init__(self):
        settings = get_settings()
        self._host = settings.milvus_host
        self._port = settings.milvus_port
        self.collection_name = settings.milvus_collection
        self.embedder = QwenEmbedder()
        self._hybrid_fields_available = False  # _ensure_collection 中更新

        self._connect()
        self._ensure_collection()

        logger.info(
            "MilvusVectorStore 初始化 | collection=%s host=%s:%d hybrid=%s",
            self.collection_name, self._host, self._port, self._hybrid_fields_available,
        )

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self):
        """Establish Milvus connection, safe to call multiple times."""
        try:
            connections.connect(alias="default", host=self._host, port=self._port)
        except MilvusException as exc:
            logger.error("Milvus 连接失败 | host=%s:%d error=%s", self._host, self._port, exc)
            raise

    def _ensure_connected(self):
        """Reconnect if the underlying connection was dropped."""
        try:
            # A lightweight probe — if the connection is alive this succeeds.
            utility.has_collection("__ping__")
        except (MilvusException, Exception):
            logger.warning("Milvus 连接已断开，正在重连...")
            self._connect()

    # ------------------------------------------------------------------
    # Partition helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_partition_name(file_name: str) -> str:
        """将文件名转换为合法的 Milvus 分区名。

        规则: 文件名_扩展名（去掉点号），非字母数字下划线替换为下划线。
        例: "商品说明书.pdf" → "商品说明书_pdf"
        """
        from pathlib import Path
        p = Path(file_name)
        stem = p.stem       # 文件名（无扩展名）
        ext = p.suffix.lstrip(".")  # 扩展名（去掉点号）
        raw = f"{stem}_{ext}" if ext else stem
        # 只保留字母、数字、下划线、中文，其他替换为下划线
        sanitized = re.sub(r'[^\w\u4e00-\u9fff]', '_', raw)
        # 去除连续下划线
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        # 确保不以数字开头（Milvus 要求）
        if sanitized and sanitized[0].isdigit():
            sanitized = 'p_' + sanitized
        return sanitized or "unknown"

    def _partition_exists(self, partition_name: str) -> bool:
        """检查分区是否存在。"""
        try:
            return self.collection.has_partition(partition_name)
        except Exception:
            return False

    def _create_partition(self, partition_name: str):
        """创建分区（已存在则跳过）。"""
        if not self._partition_exists(partition_name):
            self.collection.create_partition(partition_name)
            logger.info("Milvus 分区已创建 | partition=%s", partition_name)

    def _drop_partition(self, partition_name: str):
        """删除整个分区。"""
        if self._partition_exists(partition_name):
            self.collection.drop_partition(partition_name)
            logger.info("Milvus 分区已删除 | partition=%s", partition_name)
        else:
            logger.warning("Milvus 分区不存在 | partition=%s", partition_name)

    def list_partitions(self) -> list[str]:
        """列出所有用户分区（排除默认分区 '_default'）。"""
        self._ensure_connected()
        partitions = self.collection.partitions
        return [p.name for p in partitions if p.name != "_default"]

    # ------------------------------------------------------------------
    # Collection creation / migration
    # ------------------------------------------------------------------

    def _ensure_collection(self):
        """确保集合存在，不存在则创建；已存在则迁移缺失字段。"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            logger.info("Milvus 集合已存在 | collection=%s", self.collection_name)
            self._migrate_schema()
            return

        # ── 全新创建 ──
        fields = [
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema("file_name", DataType.VARCHAR, max_length=256),
            FieldSchema("content", DataType.VARCHAR, max_length=8192),
            FieldSchema("metadata", DataType.JSON),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=self.embedder.dimension),
        ]
        # 新增混合检索字段
        for spec in _HYBRID_FIELDS_SPEC:
            fields.append(FieldSchema(spec["name"], spec["dtype"], max_length=spec["max_length"]))

        schema = CollectionSchema(fields, description="商城 RAG 知识库（混合检索）")
        self.collection = Collection(self.collection_name, schema)

        # IVF_FLAT 索引
        self.collection.create_index(field_name="embedding", index_params=_VECTOR_INDEX_PARAMS)
        self._hybrid_fields_available = True
        logger.info("Milvus 集合已创建 | collection=%s", self.collection_name)

    def _migrate_schema(self):
        """为已存在的集合添加缺失的字段（schema migration）。

        如果 Milvus 版本不支持 add_field（旧版本），则跳过迁移，
        混合检索将降级为纯向量检索（关键词分数为 0）。
        """
        existing_fields = {f.name for f in self.collection.schema.fields}
        missing = [spec["name"] for spec in _HYBRID_FIELDS_SPEC if spec["name"] not in existing_fields]

        if not missing:
            self._hybrid_fields_available = True
            logger.info("所有混合检索字段已存在")
            return

        # 尝试动态添加字段
        new_fields_added = False
        try:
            for spec in _HYBRID_FIELDS_SPEC:
                if spec["name"] in existing_fields:
                    continue
                try:
                    self.collection.add_field(
                        field_schema=FieldSchema(
                            spec["name"], spec["dtype"], max_length=spec["max_length"],
                        ),
                    )
                    new_fields_added = True
                    logger.info("Schema 迁移：添加字段 %s", spec["name"])
                except (MilvusException, AttributeError) as exc:
                    logger.warning("添加字段 %s 失败: %s", spec["name"], exc)
                    raise  # 任何一个字段失败就停止

            if new_fields_added:
                self.collection.alter()
                self._hybrid_fields_available = True
                logger.info("Schema 迁移完成")
        except (MilvusException, AttributeError, TypeError) as exc:
            self._hybrid_fields_available = False
            logger.warning(
                "Milvus 版本不支持动态添加字段（%s），混合检索将降级为纯向量检索。"
                "如需完整混合检索功能，请升级 Milvus 到 2.4+ 或删除集合后重建。"
                "缺失字段: %s",
                type(exc).__name__,
                missing,
            )

    # ------------------------------------------------------------------
    # Insert / Add documents
    # ------------------------------------------------------------------

    async def add_documents(
        self,
        file_name: str,
        chunks: list[dict],
        *,
        title: str = "",
        keywords: Optional[list[str]] = None,
        doc_type: str = "general",
    ) -> list[str]:
        """批量插入文档分块（带 NLP 处理），按文件名自动分区。

        Args:
            file_name: 文件名（如 mysql.md）
            chunks: [{"content": str, "metadata": dict}, ...]
            title: 文档标题或章节标题
            keywords: 关键词列表；若为 None 则自动提取
            doc_type: 文档类型 (product/faq/manual/policy/general)

        Returns:
            插入的实体 ID 列表。
        """
        self._ensure_connected()

        # ── 分区：覆盖写入（已存在则先删旧分区再建新分区）──
        partition_name = self.make_partition_name(file_name)
        if self._partition_exists(partition_name):
            logger.info("同名分区已存在，执行覆盖 | partition=%s", partition_name)
            self._drop_partition(partition_name)
        self._create_partition(partition_name)

        ids = [str(uuid.uuid4()) for _ in chunks]
        contents = [c["content"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]

        # 在 metadata 中写入上传时间（精确到分钟）
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        for meta in metadatas:
            meta["upload_time"] = upload_time

        # Embeddings
        embeddings = await self.embedder.embed(contents)

        # NLP processing (lazy import) — 仅在混合字段可用时处理
        if self._hybrid_fields_available:
            tokenizer = _get_tokenizer()
            kw_extractor = _get_keyword_extractor()

            content_tokens_list = [tokenizer.tokenize_for_search(c) for c in contents]
            title_tokens = tokenizer.tokenize_for_search(title) if title else ""

            if keywords is not None:
                keywords_str = ",".join(keywords)
                keywords_list = [keywords_str] * len(chunks)
            else:
                keywords_list = []
                for c in contents:
                    extracted = kw_extractor.extract(c, top_k=8)
                    keywords_list.append(",".join(extracted))

            titles = [title] * len(ids)
            title_tokens_list = [title_tokens] * len(ids)
            doc_types = [doc_type] * len(ids)

            self.collection.insert([
                ids,
                [file_name] * len(ids),
                contents,
                metadatas,
                embeddings,
                content_tokens_list,
                titles,
                title_tokens_list,
                keywords_list,
                doc_types,
            ], partition_name=partition_name)
        else:
            # 无混合字段：只插入基础字段
            self.collection.insert([
                ids,
                [file_name] * len(ids),
                contents,
                metadatas,
                embeddings,
            ], partition_name=partition_name)
        self.collection.flush()

        logger.info(
            "Milvus 文档入库 | file_name=%s partition=%s chunks=%d doc_type=%s title=%s",
            file_name, partition_name, len(chunks), doc_type, title[:50] if title else "",
        )
        return ids

    # ------------------------------------------------------------------
    # Search: unified entry point (backward compatible)
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str = "",
        top_k: int = 5,
        *,
        query_vector: Optional[list[float]] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        file_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """统一检索入口（向后兼容）。

        - 仅 query_text → 关键词搜索
        - 仅 query_vector → 向量搜索
        - 两者都提供 → 混合搜索
        """
        self._ensure_connected()
        self.collection.load()

        # Determine search mode
        if query_vector is not None and query:
            return await self.hybrid_search(
                query_text=query,
                query_vector=query_vector,
                top_k=top_k,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight,
                file_filter=file_filter,
                doc_type_filter=doc_type_filter,
            )
        elif query_vector is not None:
            return await self._vector_search(
                query_vector=query_vector,
                top_k=top_k,
                file_filter=file_filter,
                doc_type_filter=doc_type_filter,
            )
        else:
            return await self._keyword_search(
                query_text=query,
                top_k=top_k,
                file_filter=file_filter,
                doc_type_filter=doc_type_filter,
            )

    # ------------------------------------------------------------------
    # Internal: vector-only search
    # ------------------------------------------------------------------

    async def _vector_search(
        self,
        query_vector: list[float],
        top_k: int,
        file_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """纯向量检索。"""
        self.collection.load()

        expr = self._build_filter_expr(file_filter, doc_type_filter)

        # 根据可用字段动态选择 output_fields
        output_fields = ["file_name", "content", "metadata"]
        if self._hybrid_fields_available:
            output_fields += ["title", "doc_type", "keywords"]

        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=_SEARCH_PARAMS,
            limit=top_k,
            expr=expr or None,
            output_fields=output_fields,
        )

        hits = []
        for hit in results[0]:
            hits.append({
                "id": hit.id,
                "file_name": hit.entity.get("file_name"),
                "content": hit.entity.get("content"),
                "metadata": hit.entity.get("metadata"),
                "title": hit.entity.get("title", ""),
                "doc_type": hit.entity.get("doc_type", "general"),
                "keywords": hit.entity.get("keywords", ""),
                "score": float(hit.score),
            })

        logger.debug(
            "向量检索完成 | top_k=%d results=%d", top_k, len(hits),
        )
        return hits

    # ------------------------------------------------------------------
    # Internal: keyword-only search
    # ------------------------------------------------------------------

    async def _keyword_search(
        self,
        query_text: str,
        top_k: int,
        file_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """关键词检索：在 content_tokens 和 title_tokens 中匹配 query tokens。"""
        if not self._hybrid_fields_available:
            logger.debug("混合字段不可用，关键词检索跳过")
            return []

        self.collection.load()

        tokenizer = _get_tokenizer()
        query_tokens = tokenizer.tokenize(query_text)
        if not query_tokens:
            logger.warning("查询文本分词结果为空 | query=%s", query_text[:50])
            return []

        # Fetch candidates via query (no native BM25 in IVF_FLAT, do in-memory scoring)
        expr = self._build_filter_expr(file_filter, doc_type_filter)

        try:
            rows = self.collection.query(
                expr=expr or 'id != ""',
                output_fields=["id", "file_name", "content", "metadata", "content_tokens",
                               "title_tokens", "title", "doc_type", "keywords"],
                limit=2000,
            )
        except MilvusException as exc:
            logger.error("关键词查询失败: %s", exc)
            return []

        # Score each row by token overlap (BM25-like)
        scored: list[tuple[dict, float]] = []
        for row in rows:
            score = self._keyword_score(query_tokens, row)
            if score > 0:
                scored.append((row, score))

        # Sort descending by score, take top_k
        scored.sort(key=lambda x: x[1], reverse=True)

        hits = []
        for row, score in scored[:top_k]:
            hits.append({
                "id": row.get("id"),
                "file_name": row.get("file_name"),
                "content": row.get("content"),
                "metadata": row.get("metadata"),
                "title": row.get("title", ""),
                "doc_type": row.get("doc_type", "general"),
                "keywords": row.get("keywords", ""),
                "score": score,
            })

        logger.debug(
            "关键词检索完成 | query_tokens=%s top_k=%d results=%d",
            query_tokens[:5], top_k, len(hits),
        )
        return hits

    @staticmethod
    def _keyword_score(query_tokens: list[str], row: dict) -> float:
        """Compute a simple BM25-like score for a document row.

        Score = sum of (1 + log(tf)) for each matching query token,
        weighted by token position (title match gets 2x bonus).
        """
        import math

        # Content tokens
        content_tok_str = row.get("content_tokens", "")
        content_tok_set = set(content_tok_str.split()) if content_tok_str else set()

        # Title tokens (bonus weight)
        title_tok_str = row.get("title_tokens", "")
        title_tok_set = set(title_tok_str.split()) if title_tok_str else set()

        # Keywords field (exact match bonus)
        kw_str = row.get("keywords", "")
        kw_set = set(kw_str.split(",")) if kw_str else set()

        score = 0.0
        for qt in query_tokens:
            # Content match
            if qt in content_tok_set:
                # Count occurrences for tf
                tf = content_tok_str.split().count(qt) if content_tok_str else 0
                score += 1.0 + math.log(1.0 + tf)

            # Title match (2x weight)
            if qt in title_tok_set:
                tf = title_tok_str.split().count(qt) if title_tok_str else 0
                score += 2.0 * (1.0 + math.log(1.0 + tf))

            # Keywords exact match (1.5x weight)
            if qt in kw_set:
                score += 1.5

        return score

    # ------------------------------------------------------------------
    # Hybrid search: vector + keyword score fusion
    # ------------------------------------------------------------------

    async def hybrid_search(
        self,
        *,
        query_text: str,
        query_vector: list[float],
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        file_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """混合检索：dense vector + keyword matching, weighted score fusion.

        如果 Milvus 不支持混合字段，自动降级为纯向量检索。
        """
        # 降级：无混合字段 → 纯向量检索
        if not self._hybrid_fields_available:
            logger.debug("混合字段不可用，降级为纯向量检索")
            return await self._vector_search(query_vector, top_k, file_filter, doc_type_filter)

        self._ensure_connected()
        self.collection.load()

        expr = self._build_filter_expr(file_filter, doc_type_filter)
        candidate_limit = top_k * 3  # oversample

        # ── Step 1: Vector search for candidates ──
        vector_results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=_SEARCH_PARAMS,
            limit=candidate_limit,
            expr=expr or None,
            output_fields=["file_name", "content", "metadata", "content_tokens",
                           "title_tokens", "title", "doc_type", "keywords"],
        )

        # Build candidate map: id -> {entity_data, vector_score}
        candidates: dict[str, dict] = {}
        for hit in vector_results[0]:
            doc_id = hit.id
            candidates[doc_id] = {
                "id": doc_id,
                "file_name": hit.entity.get("file_name"),
                "content": hit.entity.get("content"),
                "metadata": hit.entity.get("metadata"),
                "title": hit.entity.get("title", ""),
                "doc_type": hit.entity.get("doc_type", "general"),
                "keywords": hit.entity.get("keywords", ""),
                "content_tokens": hit.entity.get("content_tokens", ""),
                "title_tokens": hit.entity.get("title_tokens", ""),
                "vector_score": float(hit.score),
            }

        # ── Step 2: Keyword scoring on candidates ──
        tokenizer = _get_tokenizer()
        query_tokens = tokenizer.tokenize(query_text)

        # Also expand candidates via keyword scan if needed
        # (documents that match keywords well but not vector)
        if query_tokens:
            try:
                all_rows = self.collection.query(
                    expr=expr or 'id != ""',
                    output_fields=["id", "file_name", "content", "metadata", "content_tokens",
                                   "title_tokens", "title", "doc_type", "keywords"],
                    limit=2000,
                )
                for row in all_rows:
                    rid = row.get("id")
                    if rid and rid not in candidates:
                        kw_score = self._keyword_score(query_tokens, row)
                        if kw_score > 0:
                            candidates[rid] = {
                                "id": rid,
                                "file_name": row.get("file_name"),
                                "content": row.get("content"),
                                "metadata": row.get("metadata"),
                                "title": row.get("title", ""),
                                "doc_type": row.get("doc_type", "general"),
                                "keywords": row.get("keywords", ""),
                                "content_tokens": row.get("content_tokens", ""),
                                "title_tokens": row.get("title_tokens", ""),
                                "vector_score": 0.0,
                            }
            except MilvusException as exc:
                logger.warning("混合检索关键词扩展查询失败: %s", exc)

        # ── Step 3: Normalize and fuse scores ──
        vector_scores = [c["vector_score"] for c in candidates.values()]
        keyword_scores_raw = []
        for c in candidates.values():
            keyword_scores_raw.append(self._keyword_score(query_tokens, c) if query_tokens else 0.0)

        # Min-max normalization
        v_min, v_max = (min(vector_scores), max(vector_scores)) if vector_scores else (0, 1)
        k_min, k_max = (min(keyword_scores_raw), max(keyword_scores_raw)) if keyword_scores_raw else (0, 1)

        v_range = v_max - v_min if v_max != v_min else 1.0
        k_range = k_max - k_min if k_max != k_min else 1.0

        final_results: list[dict] = []
        for idx, (doc_id, cand) in enumerate(candidates.items()):
            v_norm = (cand["vector_score"] - v_min) / v_range
            k_norm = (keyword_scores_raw[idx] - k_min) / k_range if keyword_scores_raw else 0.0

            final_score = vector_weight * v_norm + keyword_weight * k_norm

            final_results.append({
                "id": doc_id,
                "file_name": cand["file_name"],
                "content": cand["content"],
                "metadata": cand["metadata"],
                "title": cand["title"],
                "doc_type": cand["doc_type"],
                "keywords": cand["keywords"],
                "score": round(final_score, 6),
                "vector_score": round(cand["vector_score"], 6),
                "keyword_score": round(keyword_scores_raw[idx] if keyword_scores_raw else 0.0, 6),
            })

        # ── Step 4: Sort and return top_k ──
        final_results.sort(key=lambda x: x["score"], reverse=True)

        logger.debug(
            "混合检索完成 | query=%s candidates=%d top_k=%d",
            query_text[:30], len(candidates), top_k,
        )
        return final_results[:top_k]

    # ------------------------------------------------------------------
    # Keyword-only direct search
    # ------------------------------------------------------------------

    async def search_by_keywords(
        self,
        keywords: list[str],
        top_k: int = 10,
        *,
        file_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """直接按关键词列表搜索（无需 embed query）。

        Args:
            keywords: 关键词列表
            top_k: 返回结果数
            file_filter: 按 file_name 过滤
            doc_type_filter: 按 doc_type 过滤

        Returns:
            按匹配分数降序排列的结果
        """
        self._ensure_connected()
        self.collection.load()

        if not keywords or not self._hybrid_fields_available:
            return []

        expr = self._build_filter_expr(file_filter, doc_type_filter)

        try:
            rows = self.collection.query(
                expr=expr or 'id != ""',
                output_fields=["id", "file_name", "content", "metadata", "content_tokens",
                               "title_tokens", "title", "doc_type", "keywords"],
                limit=2000,
            )
        except MilvusException as exc:
            logger.error("关键词搜索查询失败: %s", exc)
            return []

        scored: list[tuple[dict, float]] = []
        for row in rows:
            score = self._keyword_score(keywords, row)
            if score > 0:
                scored.append((row, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        hits = []
        for row, score in scored[:top_k]:
            hits.append({
                "id": row.get("id"),
                "file_name": row.get("file_name"),
                "content": row.get("content"),
                "metadata": row.get("metadata"),
                "title": row.get("title", ""),
                "doc_type": row.get("doc_type", "general"),
                "keywords": row.get("keywords", ""),
                "score": score,
            })

        logger.debug(
            "关键词搜索完成 | keywords=%s top_k=%d results=%d",
            keywords[:5], top_k, len(hits),
        )
        return hits

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_by_name(self, file_name: str):
        """删除文档分区及其所有向量。"""
        self._ensure_connected()
        partition_name = self.make_partition_name(file_name)
        self._drop_partition(partition_name)
        logger.info("Milvus 文档已删除 | file_name=%s partition=%s", file_name, partition_name)

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    async def count(self) -> int:
        """返回集合中实际可见的实体总数。"""
        try:
            self._ensure_connected()
            self.collection.flush()
            return self.collection.num_entities
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # List documents
    # ------------------------------------------------------------------

    async def list_documents(self) -> list[dict]:
        """列出所有文档（基于分区），每个分区代表一个文档。

        返回按 upload_time 降序排列（最新上传的排前面）。
        """
        self._ensure_connected()
        self.collection.load()

        partition_names = self.list_partitions()
        if not partition_names:
            return []

        output_fields = ["file_name", "metadata"]
        if self._hybrid_fields_available:
            output_fields.append("doc_type")

        documents = []
        for pname in partition_names:
            try:
                # 每个分区取 1 条记录，获取文档元信息
                rows = self.collection.query(
                    expr='id != ""',
                    output_fields=output_fields,
                    limit=1,
                    partition_names=[pname],
                )
                if not rows:
                    continue
                r = rows[0]
                fname = r.get("file_name", pname)
                meta = r.get("metadata", {}) or {}
                documents.append({
                    "file_name": fname,
                    "partition": pname,
                    "strategy": meta.get("chunk_strategy") or meta.get("strategy", "未知"),
                    "upload_time": meta.get("upload_time", ""),
                    "doc_type": r.get("doc_type", "general"),
                })
            except Exception as exc:
                logger.warning("读取分区 %s 元信息失败: %s", pname, exc)

        # 按上传时间降序排列
        documents.sort(key=lambda d: d.get("upload_time", ""), reverse=True)
        return documents

    # ------------------------------------------------------------------
    # Get chunks by file name
    # ------------------------------------------------------------------

    async def get_chunks_by_file_name(self, file_name: str) -> list[dict]:
        """查询指定文档的所有切片，按 chunk_index 排序。"""
        self._ensure_connected()
        self.collection.load()

        partition_name = self.make_partition_name(file_name)
        output_fields = ["id", "content", "metadata"]
        if self._hybrid_fields_available:
            output_fields += ["title", "doc_type", "keywords"]

        # 优先在指定分区查询
        if self._partition_exists(partition_name):
            results = self.collection.query(
                expr='id != ""',
                output_fields=output_fields,
                limit=1000,
                partition_names=[partition_name],
            )
        else:
            # 回退：按 file_name 表达式查询（兼容旧数据）
            safe_name = self._sanitize_milvus_value(file_name)
            results = self.collection.query(
                expr=f'file_name == "{safe_name}"',
                output_fields=output_fields,
                limit=1000,
            )
        results.sort(key=lambda x: int((x.get("metadata") or {}).get("chunk_index", 0)))
        return results

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        """返回集合统计信息。"""
        self._ensure_connected()
        try:
            count = await self.count()
            return {
                "collection": self.collection_name,
                "total_chunks": count,
                "dimension": self.embedder.dimension,
                "index_type": "IVF_FLAT",
                "metric": "COSINE",
                "hybrid_search": True,
            }
        except Exception as exc:
            logger.error("获取统计信息失败: %s", exc)
            return {"collection": self.collection_name, "error": str(exc)}

    # ------------------------------------------------------------------
    # Internal: filter expression builder
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_milvus_value(value: str) -> str:
        """转义 Milvus 表达式中的特殊字符，防止注入。

        移除双引号、反斜杠、换行符等可能破坏表达式的字符。
        """
        return value.replace("\\", "").replace('"', "").replace("\n", "").replace("\r", "")

    @staticmethod
    def _build_filter_expr(
        file_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
    ) -> str:
        """Build a Milvus boolean expression from optional filters."""
        parts: list[str] = []
        if file_filter:
            safe = MilvusVectorStore._sanitize_milvus_value(file_filter)
            parts.append(f'file_name == "{safe}"')
        if doc_type_filter:
            safe = MilvusVectorStore._sanitize_milvus_value(doc_type_filter)
            parts.append(f'doc_type == "{safe}"')
        return " and ".join(parts) if parts else ""
