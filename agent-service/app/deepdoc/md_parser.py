"""
deepdoc/md_parser.py - Markdown 解析器

解析 Markdown 文档，保留标题层级作为 section 元数据。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .base import BaseParser, DocumentChunk, ParserRegistry
from .utils import clean_text

logger = logging.getLogger(__name__)


@ParserRegistry.register(["md", "markdown"])
class MarkdownParser(BaseParser):
    """Markdown 文档解析器。"""

    def parse(self, file_path: str | Path) -> list[DocumentChunk]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception as e:
            logger.error("Markdown 文件读取失败: %s - %s", file_path, e)
            raise

        return self._parse_markdown(text, file_path.name)

    def parse_bytes(self, data: bytes, filename: str = "") -> list[DocumentChunk]:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        return self._parse_markdown(text, filename)

    @staticmethod
    def _parse_markdown(text: str, source: str) -> list[DocumentChunk]:
        """
        解析 Markdown 文本，按标题和段落分块。

        策略：
        - 以标题（# ## ### ...）为分界点
        - 每个标题下的内容作为一个 chunk
        - 表格单独提取
        - 代码块保持完整
        """
        lines = text.splitlines()
        chunks: list[DocumentChunk] = []
        heading_stack: dict[int, str] = {}  # level -> heading text
        current_section = ""
        buffer_lines: list[str] = []
        in_code_block = False

        def flush_buffer():
            """将缓冲区内容保存为 chunk。"""
            if not buffer_lines:
                return
            content = clean_text("\n".join(buffer_lines))
            if not content:
                buffer_lines.clear()
                return

            metadata: dict = {
                "source": source,
                "chunk_type": "text",
            }
            if current_section:
                metadata["section"] = current_section

            chunks.append(DocumentChunk(content=content, metadata=metadata))
            buffer_lines.clear()

        for line in lines:
            stripped = line.strip()

            # 代码块边界检测
            if stripped.startswith("```"):
                if in_code_block:
                    buffer_lines.append(line)
                    in_code_block = False
                    continue
                else:
                    in_code_block = True
                    buffer_lines.append(line)
                    continue

            if in_code_block:
                buffer_lines.append(line)
                continue

            # 标题检测
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading_match:
                flush_buffer()
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                heading_stack[level] = title
                # 清除更低层级
                for k in list(heading_stack.keys()):
                    if k > level:
                        del heading_stack[k]
                current_section = " > ".join(
                    heading_stack[k] for k in sorted(heading_stack.keys())
                )

                # 标题本身也作为一个 chunk
                chunks.append(DocumentChunk(
                    content=title,
                    metadata={
                        "source": source,
                        "chunk_type": "heading",
                        "heading_level": level,
                        "section": current_section,
                    },
                ))
                continue

            # Markdown 表格检测
            if "|" in stripped and re.search(r"\|.*\|", stripped):
                flush_buffer()
                table_lines = [line]
                # 表格会在后续行中被收集（简单回溯处理）
                # 这里直接将当前表格行加入 buffer 让后续逻辑处理
                buffer_lines.append(line)
                continue

            # 普通文本行
            buffer_lines.append(line)

        flush_buffer()

        logger.info("Markdown 解析完成: %s (%d 个块)", source, len(chunks))
        return chunks
