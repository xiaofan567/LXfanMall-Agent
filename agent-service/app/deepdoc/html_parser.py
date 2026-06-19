"""
deepdoc/html_parser.py - HTML 文档解析器

使用 BeautifulSoup 提取文本内容，移除 script/style 标签，保留结构信息。
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path

from .base import BaseParser, DocumentChunk, ParserRegistry
from .utils import clean_text

logger = logging.getLogger(__name__)


@ParserRegistry.register(["html", "htm"])
class HtmlParser(BaseParser):
    """HTML 文档解析器。"""

    # 需要移除的标签（及其内容）
    REMOVE_TAGS = {"script", "style", "noscript", "iframe", "svg", "head"}
    # 块级标签，用于分段
    BLOCK_TAGS = {"p", "div", "section", "article", "li", "td", "th", "tr", "blockquote", "pre"}

    def parse(self, file_path: str | Path) -> list[DocumentChunk]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
        except Exception:
            # 回退二进制读取 + 编码检测
            from .utils import detect_encoding
            encoding = detect_encoding(file_path)
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                html = f.read()

        return self._parse_html(html, file_path.name)

    def parse_bytes(self, data: bytes, filename: str = "") -> list[DocumentChunk]:
        # 尝试从 meta 标签检测编码
        html = self._decode_html(data)
        return self._parse_html(html, filename)

    @staticmethod
    def _decode_html(data: bytes) -> str:
        """解码 HTML 字节数据，尝试检测编码。"""
        # 先尝试从 <meta charset=...> 提取编码
        head = data[:4096].decode("ascii", errors="ignore")
        charset_match = re.search(
            r'charset=["\']?([a-zA-Z0-9_\-]+)', head, re.IGNORECASE
        )
        if charset_match:
            try:
                return data.decode(charset_match.group(1))
            except (UnicodeDecodeError, LookupError):
                pass

        for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue

        return data.decode("utf-8", errors="replace")

    def _parse_html(self, html: str, source: str) -> list[DocumentChunk]:
        """解析 HTML 并提取结构化内容。"""
        try:
            from bs4 import BeautifulSoup, NavigableString
        except ImportError:
            raise ImportError("需要安装 beautifulsoup4: pip install beautifulsoup4 lxml")

        soup = BeautifulSoup(html, "lxml")

        # 移除不需要的标签
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        chunks: list[DocumentChunk] = []
        heading_stack: dict[int, str] = {}
        current_section = ""

        # 提取标题
        for level in range(1, 7):
            for heading in soup.find_all(f"h{level}"):
                text = clean_text(heading.get_text())
                if not text:
                    continue
                heading_stack[level] = text
                for k in list(heading_stack.keys()):
                    if k > level:
                        del heading_stack[k]
                current_section = " > ".join(
                    heading_stack[k] for k in sorted(heading_stack.keys())
                )
                chunks.append(DocumentChunk(
                    content=text,
                    metadata={
                        "source": source,
                        "chunk_type": "heading",
                        "heading_level": level,
                        "section": current_section,
                    },
                ))

        # 提取正文内容（按块级元素分段）
        body = soup.find("body") or soup
        self._extract_block_text(body, chunks, source, heading_stack)

        # 提取表格
        for table in soup.find_all("table"):
            table_text = self._table_to_text(table)
            if table_text:
                chunks.append(DocumentChunk(
                    content=table_text,
                    metadata={
                        "source": source,
                        "chunk_type": "table",
                    },
                ))

        logger.info("HTML 解析完成: %s (%d 个块)", source, len(chunks))
        return chunks

    def _extract_block_text(self, element, chunks: list, source: str, heading_stack: dict):
        """递归提取块级元素的文本。"""
        buffer: list[str] = []

        def flush():
            if buffer:
                text = clean_text(" ".join(buffer))
                if text and len(text) > 10:  # 过滤过短的文本
                    current_section = " > ".join(
                        heading_stack[k] for k in sorted(heading_stack.keys())
                    ) if heading_stack else ""
                    metadata: dict = {
                        "source": source,
                        "chunk_type": "text",
                    }
                    if current_section:
                        metadata["section"] = current_section
                    chunks.append(DocumentChunk(content=text, metadata=metadata))
                buffer.clear()

        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    buffer.append(text)
            else:
                tag_name = child.name.lower() if child.name else ""
                if tag_name in self.REMOVE_TAGS:
                    continue
                if tag_name == "table":
                    flush()  # 表格单独处理
                    continue
                if tag_name in self.BLOCK_TAGS:
                    flush()
                    text = clean_text(child.get_text())
                    if text:
                        current_section = " > ".join(
                            heading_stack[k] for k in sorted(heading_stack.keys())
                        ) if heading_stack else ""
                        metadata = {
                            "source": source,
                            "chunk_type": "text",
                        }
                        if current_section:
                            metadata["section"] = current_section
                        chunks.append(DocumentChunk(content=text, metadata=metadata))
                else:
                    text = child.get_text().strip()
                    if text:
                        buffer.append(text)

        flush()

    @staticmethod
    def _table_to_text(table_tag) -> str:
        """将 HTML 表格转换为 Markdown 风格文本。"""
        rows: list[list[str]] = []
        for tr in table_tag.find_all("tr"):
            cells = []
            for cell in tr.find_all(["td", "th"]):
                cells.append(clean_text(cell.get_text()))
            if cells:
                rows.append(cells)

        if not rows:
            return ""

        # 统一列数
        max_cols = max(len(row) for row in rows)
        for row in rows:
            while len(row) < max_cols:
                row.append("")

        lines: list[str] = []
        for i, row in enumerate(rows):
            lines.append("| " + " | ".join(row) + " |")
            if i == 0:
                lines.append("| " + " | ".join("---" for _ in row) + " |")

        return "\n".join(lines)
