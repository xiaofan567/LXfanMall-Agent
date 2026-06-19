"""RAG 文档管理服务 — 文档上传、解析、分块、入库全流程。

使用 deepdoc 解析引擎 + chunker 分块策略的全新流水线：
  解析器(get_parser) → 分块器(ChunkerFactory) → Embedding → Milvus 入库

支持的文档格式: PDF, DOCX, Excel, TXT, Markdown, HTML
分块策略: general, product, faq, manual, policy
"""

import logging
import time
import uuid
from pathlib import Path

from app.config.settings import get_settings
from app.rag.chunker import ChunkerFactory
from app.rag.query_cache import RAGQueryCache
from app.rag.vector_store import MilvusVectorStore

logger = logging.getLogger(__name__)

# ── 策略描述信息（供 API 返回） ─────────────────────────────
STRATEGY_DESCRIPTIONS: dict[str, dict] = {
    "general": {
        "key": "general",
        "label": "通用策略",
        "description": "默认策略，类似 RAGFlow naive。表格保持原样，文本按段落合并，支持重叠。",
        "best_for": "通用文档、混合格式文档",
    },
    "product": {
        "key": "product",
        "label": "商品文档策略",
        "description": "保留规格参数表格和商品描述的语义边界，标题+内容组合输出。",
        "best_for": "商品说明书、产品参数表、SKU 描述",
    },
    "faq": {
        "key": "faq",
        "label": "问答策略",
        "description": "检测 Q&A 对（Q:/A:、问:/答:、编号问题），每个问答对作为一个完整 chunk。",
        "best_for": "常见问题、客服问答、帮助文档",
    },
    "manual": {
        "key": "manual",
        "label": "手册/指南策略",
        "description": "按章节标题（第X章、1.1、步骤N）切分，保持同一章节内容完整。",
        "best_for": "用户手册、操作指南、教程文档",
    },
    "policy": {
        "key": "policy",
        "label": "条款/政策策略",
        "description": "按条款边界（第X条、Article N）切分，合并相关小条款。",
        "best_for": "服务条款、隐私政策、规则协议",
    },
}


class RAGDocumentService:
    """RAG 文档管理服务。

    职责：
      - 接收上传文件（字节流），通过 deepdoc 解析器提取结构化内容
      - 使用 ChunkerFactory 进行智能分块
      - 调用 MilvusVectorStore 完成 Embedding + 向量入库
      - 管理文档生命周期（列表、删除、查看切片、重新处理）
    """

    def __init__(self):
        """延迟初始化各组件，避免模块导入时建立连接。"""
        self._vector_store: MilvusVectorStore | None = None
        self._cache: RAGQueryCache | None = None
        self._settings = get_settings()

    @property
    def vector_store(self) -> MilvusVectorStore:
        """懒加载 Milvus 向量存储。"""
        if self._vector_store is None:
            self._vector_store = MilvusVectorStore()
        return self._vector_store

    @property
    def cache(self) -> RAGQueryCache:
        """懒加载查询缓存。"""
        if self._cache is None:
            self._cache = RAGQueryCache()
        return self._cache

    # ── 核心方法：文档上传与处理 ──────────────────────────────

    async def upload_document(
        self,
        file_name: str,
        file_content: bytes,
        chunking_strategy: str | None = None,
        doc_type: str | None = None,
    ) -> dict:
        """完整文档处理流水线：解析 → 分块 → Embedding → 入库 Milvus。

        新流水线使用 deepdoc 解析引擎替代旧的 _extract_text，
        使用 ChunkerFactory 替代旧的 SplitterFactory。

        Args:
            file_name: 文件名（含扩展名，如 "商品说明书.pdf"）
            file_content: 文件二进制内容
            chunking_strategy: 分块策略名，None 则自动检测
            doc_type: 文档类型标签，None 则使用策略名作为默认值

        Returns:
            处理结果字典:
            {
                "status": "success",
                "file_name": str,
                "strategy_used": str,
                "chunk_count": int,
                "doc_type": str,
                "processing_time_ms": int,
            }
        """
        start_time = time.time()

        # ── Step 1: 根据文件扩展名获取解析器 ──
        try:
            file_ext = Path(file_name).suffix
            from app.deepdoc import get_parser
            parser = get_parser(file_ext)
            logger.info("文档解析器已加载 | file=%s ext=%s parser=%s",
                        file_name, file_ext, type(parser).__name__)
        except ValueError:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        except Exception as e:
            logger.error("获取解析器失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"解析器初始化失败: {e}")

        # ── Step 2: 解析文档，提取结构化内容 ──
        try:
            raw_chunks = parser.parse_bytes(file_content, file_name)
            logger.info("文档解析完成 | file=%s raw_chunks=%d",
                        file_name, len(raw_chunks))
        except Exception as e:
            logger.error("文档解析失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"文档解析失败: {e}")

        if not raw_chunks:
            raise ValueError("文档解析结果为空，请检查文件内容")

        # ── Step 3: 自动检测或使用指定的分块策略 ──
        if not chunking_strategy:
            try:
                preview = " ".join(
                    (c.content or "")[:200] for c in raw_chunks[:3]
                )
                chunking_strategy = ChunkerFactory.auto_detect(file_name, preview)
                logger.info("自动检测分块策略 | file=%s strategy=%s",
                            file_name, chunking_strategy)
            except Exception as e:
                logger.warning("策略自动检测失败，使用 general | error=%s", e)
                chunking_strategy = "general"

        # ── Step 4: 使用分块器进行分块 ──
        try:
            chunker = ChunkerFactory.get_chunker(chunking_strategy)
            chunks = chunker.chunk(raw_chunks)
            logger.info("文档分块完成 | file=%s strategy=%s chunks=%d",
                        file_name, chunking_strategy, len(chunks))
        except ValueError:
            # 未知策略名，直接抛出
            raise
        except Exception as e:
            logger.error("文档分块失败 | file=%s strategy=%s error=%s",
                         file_name, chunking_strategy, e)
            raise RuntimeError(f"文档分块失败: {e}")

        # ── Step 5: 过滤空 chunk ──
        chunks = [c for c in chunks if (c.content or "").strip()]
        if not chunks:
            raise ValueError("分块后无有效内容，请检查文件或调整策略参数")

        # ── Step 6: 构建 chunk 数据并调用 vector_store 入库 ──
        # vector_store.add_documents 内部已完成:
        #   - 生成 UUID
        #   - Embedding
        #   - 关键词提取
        #   - Milvus 插入
        try:
            chunk_docs = []
            for c in chunks:
                chunk_docs.append({
                    "content": c.content.strip(),
                    "metadata": c.metadata or {},
                })

            # 确定 doc_type：优先使用用户指定，否则使用策略名
            effective_doc_type = doc_type or chunking_strategy

            # 从第一个有标题的 chunk 提取文档标题
            title = self._extract_title(chunks)

            inserted_ids = await self.vector_store.add_documents(
                file_name=file_name,
                chunks=chunk_docs,
                title=title,
                doc_type=effective_doc_type,
            )
            logger.info("文档入库完成 | file=%s ids=%d", file_name, len(inserted_ids))

        except Exception as e:
            logger.error("文档入库失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"向量入库失败: {e}")

        # ── Step 7: 失效查询缓存 ──
        try:
            await self.cache.invalidate_all()
        except Exception as e:
            # 缓存失效失败不影响主流程，仅记录警告
            logger.warning("缓存失效失败（不影响入库）| error=%s", e)

        # ── 构建返回结果 ──
        elapsed_ms = int((time.time() - start_time) * 1000)
        result = {
            "status": "success",
            "file_name": file_name,
            "strategy_used": chunking_strategy,
            "chunk_count": len(chunks),
            "doc_type": effective_doc_type,
            "processing_time_ms": elapsed_ms,
        }
        logger.info("文档处理全流程完成 | %s", result)
        return result

    # ── 文档管理方法 ─────────────────────────────────────────

    async def list_documents(self) -> list[dict]:
        """列出所有已入库的文档（按文件名去重）。

        Returns:
            文档信息列表，每项包含:
            - file_name: 文件名
            - strategy: 使用的分块策略
            - upload_time: 上传时间
            - doc_type: 文档类型
            - title: 文档标题
        """
        try:
            documents = await self.vector_store.list_documents()
            return documents
        except Exception as e:
            logger.error("获取文档列表失败 | error=%s", e)
            raise RuntimeError(f"获取文档列表失败: {e}")

    async def delete_document(self, file_name: str) -> None:
        """删除指定文档及其所有向量切片。

        Args:
            file_name: 要删除的文件名
        """
        try:
            await self.vector_store.delete_by_name(file_name)
            # 删除后失效缓存
            try:
                await self.cache.invalidate_all()
            except Exception as e:
                logger.warning("删除后缓存失效失败 | error=%s", e)
            logger.info("文档已删除 | file_name=%s", file_name)
        except Exception as e:
            logger.error("文档删除失败 | file_name=%s error=%s", file_name, e)
            raise RuntimeError(f"文档删除失败: {e}")

    async def get_document_chunks(self, file_name: str) -> list[dict]:
        """获取指定文档的所有切片，按 chunk_index 排序。

        Args:
            file_name: 文件名

        Returns:
            切片列表，每项包含 id, content, metadata, title, doc_type, keywords
        """
        try:
            chunks = await self.vector_store.get_chunks_by_file_name(file_name)
            return chunks
        except Exception as e:
            logger.error("获取文档切片失败 | file_name=%s error=%s", file_name, e)
            raise RuntimeError(f"获取文档切片失败: {e}")

    async def reprocess_document(
        self,
        file_name: str,
        new_strategy: str,
    ) -> dict:
        """使用新策略重新处理已入库的文档。

        流程:
          1. 从 Milvus 获取现有切片的完整内容
          2. 删除旧切片
          3. 使用新策略重新分块
          4. 重新 Embedding 并入库
          5. 失效缓存

        注意：此方法基于已有切片内容重新分块，无法完全还原原始文档结构。
        如需最佳效果，建议重新上传原始文件。

        Args:
            file_name: 要重新处理的文件名
            new_strategy: 新的分块策略名

        Returns:
            处理结果字典，格式同 upload_document
        """
        start_time = time.time()

        # ── Step 1: 获取现有切片 ──
        try:
            existing_chunks = await self.vector_store.get_chunks_by_file_name(file_name)
        except Exception as e:
            logger.error("获取现有切片失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"获取现有切片失败: {e}")

        if not existing_chunks:
            raise ValueError(f"文档 '{file_name}' 不存在或无切片数据")

        # ── Step 2: 删除旧切片 ──
        try:
            await self.vector_store.delete_by_name(file_name)
            logger.info("旧切片已删除 | file=%s count=%d", file_name, len(existing_chunks))
        except Exception as e:
            logger.error("删除旧切片失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"删除旧切片失败: {e}")

        # ── Step 3: 将现有切片内容转换为 DocumentChunk，使用新策略重新分块 ──
        try:
            from app.deepdoc.base import DocumentChunk

            # 从已有切片重建 DocumentChunk 列表
            # 按 chunk_index 排序确保内容顺序正确
            existing_chunks.sort(
                key=lambda x: int((x.get("metadata") or {}).get("chunk_index", 0))
            )

            # 提取原始 doc_type（从旧切片元数据中获取）
            old_doc_type = "general"
            for c in existing_chunks:
                dt = c.get("doc_type", "")
                if dt and dt != "general":
                    old_doc_type = dt
                    break

            reconstructed_chunks = []
            for c in existing_chunks:
                content = c.get("content", "")
                if content and content.strip():
                    meta = c.get("metadata") or {}
                    reconstructed_chunks.append(
                        DocumentChunk(content=content, metadata=meta)
                    )

            if not reconstructed_chunks:
                raise ValueError("从现有切片重建内容失败，切片内容为空")

            # 使用新策略分块
            chunker = ChunkerFactory.get_chunker(new_strategy)
            new_chunks = chunker.chunk(reconstructed_chunks)
            logger.info("重新分块完成 | file=%s old_count=%d new_strategy=%s new_count=%d",
                        file_name, len(existing_chunks), new_strategy, len(new_chunks))

        except ValueError:
            raise
        except Exception as e:
            logger.error("重新分块失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"重新分块失败: {e}")

        # ── Step 4: 过滤空 chunk 并入库 ──
        new_chunks = [c for c in new_chunks if (c.content or "").strip()]
        if not new_chunks:
            raise ValueError("重新分块后无有效内容")

        try:
            chunk_docs = []
            for c in new_chunks:
                chunk_docs.append({
                    "content": c.content.strip(),
                    "metadata": c.metadata or {},
                })

            # 保留原始 doc_type，除非新策略提供更合适的类型
            effective_doc_type = old_doc_type if old_doc_type != "general" else new_strategy
            title = self._extract_title(new_chunks)

            inserted_ids = await self.vector_store.add_documents(
                file_name=file_name,
                chunks=chunk_docs,
                title=title,
                doc_type=effective_doc_type,
            )
            logger.info("重新入库完成 | file=%s ids=%d", file_name, len(inserted_ids))

        except Exception as e:
            logger.error("重新入库失败 | file=%s error=%s", file_name, e)
            raise RuntimeError(f"重新入库失败: {e}")

        # ── Step 5: 失效缓存 ──
        try:
            await self.cache.invalidate_all()
        except Exception as e:
            logger.warning("缓存失效失败（不影响重新处理）| error=%s", e)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result = {
            "status": "success",
            "file_name": file_name,
            "strategy_used": new_strategy,
            "chunk_count": len(new_chunks),
            "doc_type": effective_doc_type,
            "processing_time_ms": elapsed_ms,
        }
        logger.info("文档重新处理完成 | %s", result)
        return result

    # ── 策略与统计信息 ───────────────────────────────────────

    @staticmethod
    def get_strategies() -> list[dict]:
        """获取所有可用的分块策略及其描述。

        Returns:
            策略信息列表，每项包含 key, label, description, best_for
        """
        return list(STRATEGY_DESCRIPTIONS.values())

    async def get_stats(self) -> dict:
        """获取知识库统计信息。

        Returns:
            包含 collection 名称、总切片数、维度、索引类型等信息
        """
        try:
            stats = await self.vector_store.get_stats()
            return stats
        except Exception as e:
            logger.error("获取统计信息失败 | error=%s", e)
            return {"error": str(e)}

    # ── 内部辅助方法 ─────────────────────────────────────────

    @staticmethod
    def _extract_title(chunks: list) -> str:
        """从 chunk 列表中提取文档标题。

        优先查找 metadata 中的 title 字段，
        其次查找 chunk_type 为 heading 的内容，
        最后返回空前缀（让 vector_store 使用文件名）。
        """
        for c in chunks[:5]:  # 只检查前 5 个 chunk
            # DocumentChunk 对象
            if hasattr(c, "metadata"):
                meta = c.metadata or {}
                if meta.get("title"):
                    return meta["title"]
                if meta.get("chunk_type") == "heading" and c.content:
                    return c.content.strip()[:128]
            # dict 对象
            elif isinstance(c, dict):
                meta = c.get("metadata") or {}
                if meta.get("title"):
                    return meta["title"]
        return ""
