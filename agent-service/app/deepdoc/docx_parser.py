"""
deepdoc/docx_parser.py - DOCX 文档解析器

使用 python-docx 提取段落和表格，保留标题层级结构。
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

from .base import BaseParser, DocumentChunk, ParserRegistry
from .utils import clean_text

logger = logging.getLogger(__name__)


@ParserRegistry.register(["docx"])
class DocxParser(BaseParser):
    """DOCX 文档解析器。"""

    def parse(self, file_path: str | Path) -> list[DocumentChunk]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            from docx import Document
        except ImportError:
            raise ImportError("需要安装 python-docx: pip install python-docx")

        try:
            doc = Document(str(file_path))
            return self._extract_chunks(doc, file_path.name)
        except Exception as e:
            logger.error("DOCX 解析失败: %s - %s", file_path, e)
            raise

    def parse_bytes(self, data: bytes, filename: str = "") -> list[DocumentChunk]:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("需要安装 python-docx: pip install python-docx")

        try:
            doc = Document(io.BytesIO(data))
            return self._extract_chunks(doc, filename)
        except Exception as e:
            logger.error("DOCX 字节数据解析失败: %s", e)
            raise

    def _extract_chunks(self, doc, source: str) -> list[DocumentChunk]:
        """从 Document 对象中提取结构化 chunks。"""
        chunks: list[DocumentChunk] = []
        # 当前标题路径，用于构建 section 元数据
        heading_stack: dict[int, str] = {}  # level -> heading text
        current_section = ""

        # python-docx 的 body 元素按文档顺序排列段落和表格
        from docx.oxml.ns import qn
        body = doc.element.body

        for element in body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag == "p":
                # 段落
                from docx.text.paragraph import Paragraph
                para = Paragraph(element, doc)
                text = clean_text(para.text)
                if not text:
                    continue

                style_name = (para.style.name or "").lower()
                # 检测标题
                is_heading = style_name.startswith("heading") or style_name.startswith("标题")
                heading_level = 0
                if is_heading:
                    try:
                        heading_level = int(style_name.replace("heading", "").replace("标题", "").strip() or "1")
                    except ValueError:
                        heading_level = 1
                    heading_stack[heading_level] = text
                    # 清除更低层级的标题
                    for k in list(heading_stack.keys()):
                        if k > heading_level:
                            del heading_stack[k]
                    current_section = " > ".join(
                        heading_stack[k] for k in sorted(heading_stack.keys())
                    )

                chunk_type = "heading" if is_heading else "text"
                metadata: dict = {
                    "source": source,
                    "chunk_type": chunk_type,
                }
                if current_section:
                    metadata["section"] = current_section
                if heading_level:
                    metadata["heading_level"] = heading_level

                chunks.append(DocumentChunk(content=text, metadata=metadata))

            elif tag == "tbl":
                # 表格
                from docx.table import Table
                table = Table(element, doc)
                table_text = self._table_to_text(table)
                if table_text:
                    metadata = {
                        "source": source,
                        "chunk_type": "table",
                    }
                    if current_section:
                        metadata["section"] = current_section
                    chunks.append(DocumentChunk(content=table_text, metadata=metadata))

        logger.info("DOCX 解析完成: %s (%d 个块)", source, len(chunks))
        return chunks

    @staticmethod
    def _table_to_text(table) -> str:
        """将表格转换为可读文本。"""
        rows: list[list[str]] = []
        for row in table.rows:
            cells = [clean_text(cell.text) for cell in row.cells]
            rows.append(cells)

        if not rows:
            return ""

        # 使用 Markdown 风格输出表格
        lines: list[str] = []
        for i, row in enumerate(rows):
            line = "| " + " | ".join(row) + " |"
            lines.append(line)
            # 第一行后添加分隔行
            if i == 0:
                sep = "| " + " | ".join("---" for _ in row) + " |"
                lines.append(sep)

        return "\n".join(lines)
