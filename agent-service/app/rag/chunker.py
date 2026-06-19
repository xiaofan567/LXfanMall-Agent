"""
RAG 文档分块模块 - 基于 RAGFlow 思想的 5 种分块策略

每种策略针对特定文档类型优化，保留语义边界（段落、章节、表格等）。
替代旧的 splitter.py，直接操作 DocumentChunk 对象。

策略列表：
  - general:  通用策略（默认），类似 RAGFlow naive
  - product:  商品文档策略，保留规格表格和描述
  - faq:      问答策略，Q&A 对不拆分
  - manual:   手册/指南策略，按章节/步骤切分
  - policy:   条款/政策策略，按条款边界切分
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import tiktoken

from app.deepdoc.base import DocumentChunk

logger = logging.getLogger(__name__)

# ─── 全局工具 ───────────────────────────────────────────────

_encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """使用 cl100k_base 编码计算 token 数"""
    return len(_encoder.encode(text))


def _clone_chunk(src: DocumentChunk, content: str, extra_meta: dict | None = None) -> DocumentChunk:
    """基于源 chunk 创建新 chunk，保留原始 metadata 并追加额外字段"""
    meta = dict(src.metadata) if src.metadata else {}
    if extra_meta:
        meta.update(extra_meta)
    return DocumentChunk(content=content, metadata=meta)


def _is_table_chunk(chunk: DocumentChunk) -> bool:
    """判断 chunk 是否为表格类型"""
    return (chunk.metadata or {}).get("chunk_type") == "table"


def _is_heading_chunk(chunk: DocumentChunk) -> bool:
    """判断 chunk 是否为标题类型"""
    return (chunk.metadata or {}).get("chunk_type") == "heading"


# ─── 基类 ───────────────────────────────────────────────────

class BaseChunker(ABC):
    """分块策略基类"""

    strategy_name: str = "base"

    @abstractmethod
    def chunk(self, documents: list[DocumentChunk]) -> list[DocumentChunk]:
        """
        对输入文档片段列表进行分块。

        Args:
            documents: 解析器产出的 DocumentChunk 列表

        Returns:
            分块后的 DocumentChunk 列表，每个 chunk 携带:
              - chunk_index: 在结果列表中的序号
              - chunk_strategy: 使用的策略名
              - token_count: 该 chunk 的 token 数
        """
        ...

    # ── 通用辅助 ──

    @staticmethod
    def _finalize(chunks: list[DocumentChunk], strategy: str) -> list[DocumentChunk]:
        """为结果 chunk 列表统一补充元信息"""
        for i, c in enumerate(chunks):
            c.metadata["chunk_index"] = i
            c.metadata["chunk_strategy"] = strategy
            c.metadata["token_count"] = count_tokens(c.content)
        return chunks


# ─── 1. 通用分块 (GeneralChunker) ───────────────────────────

class GeneralChunker(BaseChunker):
    """
    通用分块策略，类似 RAGFlow 的 naive 策略。

    规则：
      - 表格 chunk 保持原样，不与其他内容合并
      - 文本 chunk 按段落合并，直到接近 max_tokens
      - 相邻 chunk 之间保留 overlap 个 token 的重叠
    """

    strategy_name = "general"

    def __init__(self, max_tokens: int = 512, overlap: int = 64):
        self.max_tokens = max_tokens
        self.overlap = max_tokens if overlap > max_tokens else overlap

    def chunk(self, documents: list[DocumentChunk]) -> list[DocumentChunk]:
        if not documents:
            return []

        result: list[DocumentChunk] = []
        text_buffer: list[DocumentChunk] = []  # 暂存待合并的文本 chunk
        buffer_tokens = 0

        def flush_buffer():
            """将当前文本 buffer 合并为一个或多个输出 chunk"""
            nonlocal buffer_tokens
            if not text_buffer:
                return

            # 拼接所有 buffer 中的内容
            merged_text = "\n".join(c.content.strip() for c in text_buffer if c.content.strip())
            if not merged_text:
                text_buffer.clear()
                buffer_tokens = 0
                return

            # 用第一个 chunk 的 metadata 作为基础
            base_chunk = text_buffer[0]

            # 如果合并后超长，需要二次切分
            total_tokens = count_tokens(merged_text)
            if total_tokens <= self.max_tokens:
                result.append(_clone_chunk(base_chunk, merged_text))
            else:
                # 按段落二次切分
                paragraphs = merged_text.split("\n")
                sub_buf: list[str] = []
                sub_tokens = 0
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    pt = count_tokens(para)
                    if sub_tokens + pt > self.max_tokens and sub_buf:
                        result.append(_clone_chunk(base_chunk, "\n".join(sub_buf)))
                        # 保留 overlap：从尾部回退若干段落
                        overlap_buf: list[str] = []
                        overlap_t = 0
                        for p in reversed(sub_buf):
                            t = count_tokens(p)
                            if overlap_t + t > self.overlap:
                                break
                            overlap_buf.insert(0, p)
                            overlap_t += t
                        sub_buf = overlap_buf
                        sub_tokens = overlap_t
                    sub_buf.append(para)
                    sub_tokens += pt
                if sub_buf:
                    result.append(_clone_chunk(base_chunk, "\n".join(sub_buf)))

            text_buffer.clear()
            buffer_tokens = 0

        for doc in documents:
            content = (doc.content or "").strip()
            if not content:
                continue

            # 表格 chunk：单独输出，不参与文本合并
            if _is_table_chunk(doc):
                flush_buffer()
                result.append(doc)
                continue

            # 文本 chunk：累积到 buffer
            doc_tokens = count_tokens(content)
            if buffer_tokens + doc_tokens > self.max_tokens and text_buffer:
                # 当前 buffer 已满，先 flush
                flush_buffer()
                # 从前一个 chunk 末尾取 overlap
                if result and not _is_table_chunk(result[-1]):
                    overlap_text = self._extract_tail_overlap(result[-1].content)
                    if overlap_text:
                        text_buffer.append(_clone_chunk(doc, overlap_text))
                        buffer_tokens = count_tokens(overlap_text)

            text_buffer.append(doc)
            buffer_tokens += doc_tokens

        flush_buffer()
        return self._finalize(result, self.strategy_name)

    def _extract_tail_overlap(self, text: str) -> str:
        """从文本末尾提取约 overlap 个 token 的内容"""
        tokens = _encoder.encode(text)
        if len(tokens) <= self.overlap:
            return text
        overlap_tokens = tokens[-self.overlap:]
        return _encoder.decode(overlap_tokens)


# ─── 2. 商品文档分块 (ProductChunker) ────────────────────────

class ProductChunker(BaseChunker):
    """
    商品文档分块策略。

    规则：
      - 规格参数表格作为独立 chunk
      - 商品描述段落合并到合理大小
      - 标题 + 内容组合输出（title+content 模式）
      - key-value 规格参数保持原子性
    """

    strategy_name = "product"
    MAX_DESC_TOKENS = 384

    def chunk(self, documents: list[DocumentChunk]) -> list[DocumentChunk]:
        if not documents:
            return []

        result: list[DocumentChunk] = []
        desc_buffer: list[DocumentChunk] = []
        current_title = ""

        def flush_desc():
            nonlocal current_title
            if not desc_buffer:
                return
            parts = []
            for c in desc_buffer:
                text = c.content.strip()
                if text:
                    parts.append(text)
            if not parts:
                desc_buffer.clear()
                return
            merged = "\n".join(parts)
            # 标题 + 内容组合
            if current_title:
                merged = f"{current_title}\n{merged}"
            base = desc_buffer[0]
            result.append(_clone_chunk(base, merged, {"product_section": current_title or "描述"}))
            desc_buffer.clear()

        for doc in documents:
            content = (doc.content or "").strip()
            if not content:
                continue

            # 表格 chunk（规格参数表）：独立输出
            if _is_table_chunk(doc):
                flush_desc()
                result.append(doc)
                continue

            # 标题 chunk：记录当前标题，flush 已有描述
            if _is_heading_chunk(doc):
                flush_desc()
                current_title = content
                continue

            # 普通文本（商品描述）：累积
            desc_tokens = count_tokens(content)
            if desc_buffer and sum(count_tokens(c.content) for c in desc_buffer) + desc_tokens > self.MAX_DESC_TOKENS:
                flush_desc()
            desc_buffer.append(doc)

        flush_desc()
        return self._finalize(result, self.strategy_name)


# ─── 3. 问答分块 (FAQChunker) ────────────────────────────────

class FAQChunker(BaseChunker):
    """
    问答对分块策略（参考 RAGFlow 实现）。

    核心思路：利用 MarkdownParser 已有的标题切分结果，
    以 Q/问 开头的标题作为 Q&A 对边界，将标题 + 后续内容合并为一个 chunk。

    支持的问题格式：
      - ### Q1: 如何注册？
      - Q1: 如何注册？
      - Question: 如何注册？
      - 问：如何注册？
      - ### 如何注册？（标题含问号）
      - 1. 如何注册？（编号问题）

    每个 Q&A 对作为一个 chunk，不拆分。
    """

    strategy_name = "faq"

    # 问题行检测正则（按优先级排列）
    _Q_PATTERNS = [
        # Q1: / Q2: / Q12：（带编号，最常见）
        re.compile(r"^\s*(?:Q|Question|问)\s*\d*\s*[\.：:\s]", re.IGNORECASE),
        # 标题含问号：### 如何注册？
        re.compile(r"^#{1,6}\s+.+[?？]"),
        # 编号问题：1. 如何注册？  ⑴ 如何注册？
        re.compile(r"^\s*(?:\d+[\.\、\)）]|[①②③④⑤⑥⑦⑧⑨⑩])\s*.+[?？]"),
    ]

    # 匹配纯文本中的 Q&A 格式（用于非 heading chunk）
    _INLINE_QA = re.compile(
        r"^\s*(?:Q|Question|问)\s*\d*\s*[\.：:\s]",
        re.IGNORECASE,
    )

    def chunk(self, documents: list[DocumentChunk]) -> list[DocumentChunk]:
        if not documents:
            return []

        # 策略：利用 MarkdownParser 的 chunk 结构直接合并
        # 以 Q 开头的 heading 为边界，将 Q 标题 + 后续 text/heading 合并为一个 chunk
        result: list[DocumentChunk] = []
        current_qa_lines: list[str] = []
        current_qa_meta: dict = {}
        qa_index = 0

        def flush_qa():
            nonlocal qa_index
            if not current_qa_lines:
                return
            content = "\n".join(current_qa_lines).strip()
            if not content:
                current_qa_lines.clear()
                return
            meta = {**current_qa_meta, "qa_index": qa_index}
            result.append(_clone_chunk(documents[0], content, meta))
            qa_index += 1
            current_qa_lines.clear()

        for doc in documents:
            content = (doc.content or "").strip()
            if not content:
                continue

            chunk_type = doc.metadata.get("chunk_type", "text")

            # 判断是否是新的 Q&A 边界
            is_q_boundary = False
            if chunk_type == "heading":
                # heading 类型：检查标题内容是否是问题
                for pattern in self._Q_PATTERNS:
                    if pattern.search(content):
                        is_q_boundary = True
                        break
            else:
                # text 类型：检查是否以 Q/A 格式开头（如 "Q1: xxx" 不在 heading 中）
                if self._INLINE_QA.match(content):
                    is_q_boundary = True

            if is_q_boundary:
                # 新的 Q&A 对开始：先保存上一个
                flush_qa()
                current_qa_meta = {
                    "section": doc.metadata.get("section", ""),
                    "question": content.split("\n")[0][:200],  # 第一行作为问题摘要
                }
                current_qa_lines.append(content)
            else:
                # 非 Q 边界：追加到当前 Q&A 对
                # 跳过纯分隔线
                if content.strip() in ("---", "***", "___"):
                    continue
                # 跳过章节大标题（一、二、三...）但保留其文本作为上下文
                current_qa_lines.append(content)

        # 收尾：保存最后一个 Q&A 对
        flush_qa()

        if not result:
            # 没有检测到 Q&A 模式，回退到通用策略
            logger.info("FAQChunker: 未检测到 Q&A 模式，回退到通用分块")
            from app.rag.chunker import GeneralChunker
            return GeneralChunker().chunk(documents)

        logger.info("FAQChunker: 检测到 %d 个 Q&A 对", len(result))
        return self._finalize(result, self.strategy_name)


# ─── 4. 手册/指南分块 (ManualChunker) ───────────────────────

class ManualChunker(BaseChunker):
    """
    手册/指南分块策略。

    切分依据：
      - 章节标题（第一章、1.、1.1 等）
      - 编号步骤（步骤 1、Step 1 等）
      - 标题层级边界

    同一章节/步骤序列尽量保持在同一 chunk 内。
    """

    strategy_name = "manual"
    MAX_SECTION_TOKENS = 512

    # 章节/步骤检测正则
    _SECTION_RE = re.compile(
        r"^\s*(?:"
        r"第[一二三四五六七八九十百千\d]+[章节篇部]"  # 第X章
        r"|(\d+\.){2,}\s*\S"                             # 1.1 / 1.1.1（多级编号，空格可选）
        r"|\d+\.\d+\s*\S"                               # 4.2 格式（至少两级，空格可选）
        r"|步骤\s*\d+"                                  # 步骤N
        r"|Step\s*\d+"                                  # Step N
        r"|[一二三四五六七八九十]+[、\.]\s*\S"            # 一、二、
        r")",
        re.IGNORECASE,
    )

    def chunk(self, documents: list[DocumentChunk]) -> list[DocumentChunk]:
        if not documents:
            return []

        # 预处理：将大型纯文本 chunk 按章节边界拆分为多个小 chunk
        # 解决 PDF 整页文本无法被后续章节检测识别的问题
        documents = self._pre_split_by_sections(documents)

        # 按章节边界切分
        sections: list[list[DocumentChunk]] = [[]]
        for doc in documents:
            content = (doc.content or "").strip()
            if not content:
                continue
            # 标题 chunk 或匹配章节模式的行 → 新 section
            is_section_start = _is_heading_chunk(doc)
            if not is_section_start and self._SECTION_RE.match(content.split("\n")[0]):
                is_section_start = True
            if is_section_start and sections[-1]:
                sections.append([])
            sections[-1].append(doc)

        # 合并过小 section，切分过大 section
        result: list[DocumentChunk] = []
        for section_chunks in sections:
            if not section_chunks:
                continue
            merged_text = "\n".join(c.content.strip() for c in section_chunks if c.content.strip())
            if not merged_text:
                continue
            base = section_chunks[0]
            tokens = count_tokens(merged_text)
            if tokens <= self.MAX_SECTION_TOKENS:
                result.append(_clone_chunk(base, merged_text))
            else:
                # 超长 section 按段落二次切分
                paragraphs = merged_text.split("\n")
                buf: list[str] = []
                buf_t = 0
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    pt = count_tokens(para)
                    if buf_t + pt > self.MAX_SECTION_TOKENS and buf:
                        result.append(_clone_chunk(base, "\n".join(buf)))
                        buf, buf_t = [], 0
                    buf.append(para)
                    buf_t += pt
                if buf:
                    result.append(_clone_chunk(base, "\n".join(buf)))

        return self._finalize(result, self.strategy_name)

    def _pre_split_by_sections(
        self, documents: list[DocumentChunk]
    ) -> list[DocumentChunk]:
        """将大段纯文本 chunk 按章节标题行拆分为多个小 chunk。

        解决问题：PDF 解析器输出整页文本作为单个 chunk，
        ManualChunker 只检查 chunk 第一行来判断章节边界，
        导致页面中间的章节标题被忽略，整页无法拆分。
        """
        result: list[DocumentChunk] = []
        for doc in documents:
            # 只处理纯文本 chunk，跳过表格和已有 heading 标记的
            chunk_type = (doc.metadata or {}).get("chunk_type", "text")
            if chunk_type == "table":
                result.append(doc)
                continue

            content = (doc.content or "").strip()
            if not content:
                continue

            lines = content.split("\n")
            # 如果行数少于3行，没必要拆分
            if len(lines) < 3:
                result.append(doc)
                continue

            # 检查是否有章节标题行（非第一行）
            has_inner_section = any(
                self._SECTION_RE.match(line.strip())
                for line in lines[1:]  # 跳过第一行（已在原逻辑中检查）
                if line.strip()
            )
            if not has_inner_section:
                result.append(doc)
                continue

            # 在章节边界处拆分
            buf: list[str] = []
            for line in lines:
                stripped = line.strip()
                if self._SECTION_RE.match(stripped) and buf:
                    # 当前是章节标题，先 flush 之前的内容
                    merged = "\n".join(buf).strip()
                    if merged:
                        result.append(_clone_chunk(doc, merged))
                    buf = [stripped]
                else:
                    buf.append(line)
            if buf:
                merged = "\n".join(buf).strip()
                if merged:
                    result.append(_clone_chunk(doc, merged))

        return result


# ─── 5. 条款/政策分块 (PolicyChunker) ────────────────────────

class PolicyChunker(BaseChunker):
    """
    条款/政策文档分块策略。

    切分依据：
      - 条款边界：第X条、第X款
      - 编号体系：X.X / X.X.X 层级编号
      - 保持相关条款在同一 chunk（同一章下的多个小条款可合并）
    """

    strategy_name = "policy"
    MAX_CLAUSE_TOKENS = 512

    # 条款边界正则
    _CLAUSE_RE = re.compile(
        r"^\s*(?:"
        r"第[一二三四五六七八九十百千\d]+[条款]"          # 第X条/款
        r"|(?:\d+\.){1,3}\s*\S"                           # X.X.X
        r"|Article\s*\d+"                                  # Article N
        r"|Clause\s*\d+"                                   # Clause N
        r")",
        re.IGNORECASE,
    )

    def chunk(self, documents: list[DocumentChunk]) -> list[DocumentChunk]:
        if not documents:
            return []

        # 按条款边界切分
        clauses: list[list[DocumentChunk]] = [[]]
        for doc in documents:
            content = (doc.content or "").strip()
            if not content:
                continue
            first_line = content.split("\n")[0]
            is_clause_start = _is_heading_chunk(doc) or self._CLAUSE_RE.match(first_line)
            if is_clause_start and clauses[-1]:
                clauses.append([])
            clauses[-1].append(doc)

        # 合并过小条款，切分过大条款
        result: list[DocumentChunk] = []
        pending: list[DocumentChunk] = []
        pending_tokens = 0

        def flush_pending():
            nonlocal pending, pending_tokens
            if not pending:
                return
            merged = "\n".join(c.content.strip() for c in pending if c.content.strip())
            if merged:
                result.append(_clone_chunk(pending[0], merged))
            pending = []
            pending_tokens = 0

        for clause_chunks in clauses:
            if not clause_chunks:
                continue
            clause_text = "\n".join(c.content.strip() for c in clause_chunks if c.content.strip())
            if not clause_text:
                continue
            ct = count_tokens(clause_text)
            base = clause_chunks[0]

            if pending_tokens + ct > self.MAX_CLAUSE_TOKENS:
                flush_pending()

            if ct > self.MAX_CLAUSE_TOKENS:
                # 单条款超长，按行切分
                flush_pending()
                lines = clause_text.split("\n")
                buf: list[str] = []
                buf_t = 0
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    lt = count_tokens(line)
                    if buf_t + lt > self.MAX_CLAUSE_TOKENS and buf:
                        result.append(_clone_chunk(base, "\n".join(buf)))
                        buf, buf_t = [], 0
                    buf.append(line)
                    buf_t += lt
                if buf:
                    result.append(_clone_chunk(base, "\n".join(buf)))
            else:
                pending.extend(clause_chunks)
                pending_tokens += ct

        flush_pending()
        return self._finalize(result, self.strategy_name)


# ─── 工厂类 ─────────────────────────────────────────────────

class ChunkerFactory:
    """
    分块策略工厂。

    用法：
        chunker = ChunkerFactory.get_chunker("general")
        result = chunker.chunk(documents)

        # 或自动检测
        strategy = ChunkerFactory.auto_detect("商品说明书.pdf", "本产品规格如下...")
        chunker = ChunkerFactory.get_chunker(strategy)
    """

    CHUNKER_MAP: dict[str, type[BaseChunker]] = {
        "general": GeneralChunker,
        "product": ProductChunker,
        "faq": FAQChunker,
        "manual": ManualChunker,
        "policy": PolicyChunker,
    }

    # 用于 auto_detect 的文件名模式
    _FILENAME_RULES: list[tuple[str, list[str]]] = [
        ("faq", ["faq", "问答", "常见问题", "q&a", "qa"]),
        ("product", ["商品", "产品", "规格", "spec", "product"]),
        ("manual", ["手册", "指南", "说明", "教程", "manual", "guide", "tutorial"]),
        ("policy", ["政策", "条款", "协议", "规则", "policy", "terms", "clause"]),
    ]

    # 用于 auto_detect 的内容模式
    _CONTENT_RULES: list[tuple[str, re.Pattern]] = [
        ("faq", re.compile(r"(?:Q[：:]|问[：:]|A[：:]|答[：:])")),
        ("policy", re.compile(r"(?:第[一二三四五六七八九十\d]+[条款]|Article\s+\d|Clause\s+\d)")),
        ("manual", re.compile(r"(?:第[一二三四五六七八九十\d]+章|步骤\s*\d|Step\s+\d)")),
        ("product", re.compile(r"(?:规格参数|产品型号|技术参数|商品名称|价格|SKU)")),
    ]

    @classmethod
    def get_chunker(cls, strategy: str, **kwargs) -> BaseChunker:
        """
        根据策略名获取分块器实例。

        Args:
            strategy: 策略名称（general/product/faq/manual/policy）
            **kwargs: 传递给分块器构造函数的参数

        Returns:
            对应的 BaseChunker 实例

        Raises:
            ValueError: 未知的策略名
        """
        strategy = strategy.lower().strip()
        chunker_cls = cls.CHUNKER_MAP.get(strategy)
        if chunker_cls is None:
            available = ", ".join(cls.CHUNKER_MAP.keys())
            raise ValueError(f"未知的分块策略: '{strategy}'，可选: {available}")
        return chunker_cls(**kwargs)

    @classmethod
    def auto_detect(cls, file_name: str, content_preview: str = "") -> str:
        """
        根据文件名和内容预览自动检测最佳分块策略。

        Args:
            file_name: 文件名（如 "商品说明书.pdf"）
            content_preview: 文档内容预览（前几百字）

        Returns:
            推荐的策略名
        """
        name_lower = file_name.lower()

        # 优先按文件名匹配
        for strategy, keywords in cls._FILENAME_RULES:
            for kw in keywords:
                if kw in name_lower:
                    return strategy

        # 其次按内容模式匹配（计算匹配数，选最多的）
        if content_preview:
            scores: dict[str, int] = {}
            for strategy, pattern in cls._CONTENT_RULES:
                matches = pattern.findall(content_preview)
                if matches:
                    scores[strategy] = len(matches)
            if scores:
                return max(scores, key=scores.get)

        # 默认使用通用策略
        return "general"
