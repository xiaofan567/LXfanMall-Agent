"""
deepdoc/txt_parser.py - 纯文本解析器

支持编码检测，按段落分块。
"""

from __future__ import annotations

import logging
from pathlib import Path

from .base import BaseParser, DocumentChunk, ParserRegistry
from .utils import clean_text, detect_encoding

logger = logging.getLogger(__name__)

# 段落分割的最大字符数
MAX_CHUNK_CHARS = 2000


@ParserRegistry.register(["txt", "text", "log", "csv"])
class TxtParser(BaseParser):
    """纯文本解析器。"""

    def parse(self, file_path: str | Path) -> list[DocumentChunk]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        encoding = detect_encoding(file_path)
        try:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                text = f.read()
        except Exception as e:
            logger.error("文本文件读取失败: %s - %s", file_path, e)
            # 回退到 utf-8
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

        return self._split_to_chunks(text, file_path.name)

    def parse_bytes(self, data: bytes, filename: str = "") -> list[DocumentChunk]:
        # 尝试多种编码
        for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
            try:
                text = data.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            text = data.decode("utf-8", errors="replace")

        return self._split_to_chunks(text, filename)

    @staticmethod
    def _split_to_chunks(text: str, source: str) -> list[DocumentChunk]:
        """将文本按段落拆分为 chunks。"""
        text = clean_text(text)
        if not text:
            return []

        # 按空行分割段落
        paragraphs = text.split("\n\n")
        chunks: list[DocumentChunk] = []
        buffer = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果缓冲区加上新段落超过限制，先保存缓冲区
            if buffer and len(buffer) + len(para) + 2 > MAX_CHUNK_CHARS:
                chunks.append(DocumentChunk(
                    content=buffer,
                    metadata={"source": source, "chunk_type": "text"},
                ))
                buffer = para
            else:
                buffer = f"{buffer}\n\n{para}".strip() if buffer else para

            # 单个段落超长时直接作为一个 chunk
            if len(buffer) > MAX_CHUNK_CHARS * 2:
                chunks.append(DocumentChunk(
                    content=buffer,
                    metadata={"source": source, "chunk_type": "text"},
                ))
                buffer = ""

        if buffer:
            chunks.append(DocumentChunk(
                content=buffer,
                metadata={"source": source, "chunk_type": "text"},
            ))

        logger.info("TXT 解析完成: %s (%d 个块)", source, len(chunks))
        return chunks
