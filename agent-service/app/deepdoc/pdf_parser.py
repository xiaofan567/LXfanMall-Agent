"""
deepdoc/pdf_parser.py - PDF 文档解析器

使用 pypdf 提取文本，按页分块，检测表格模式。
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path

from .base import BaseParser, DocumentChunk, ParserRegistry
from .utils import clean_text

logger = logging.getLogger(__name__)


@ParserRegistry.register(["pdf"])
class PdfParser(BaseParser):
    """PDF 文档解析器。"""

    def parse(self, file_path: str | Path) -> list[DocumentChunk]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("需要安装 pypdf: pip install pypdf")

        chunks: list[DocumentChunk] = []
        try:
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)
            logger.info("解析 PDF: %s (%d 页)", file_path.name, total_pages)

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    raw_text = page.extract_text() or ""
                except Exception as e:
                    logger.warning("第 %d 页提取文本失败: %s", page_num, e)
                    continue

                text = clean_text(raw_text)
                if not text:
                    continue

                # 检测页面中的表格模式
                table_regions = self._detect_table_regions(text)

                if table_regions:
                    # 将文本按表格区域拆分
                    chunks.extend(
                        self._split_by_tables(text, page_num, table_regions, file_path.name)
                    )
                else:
                    chunks.append(DocumentChunk(
                        content=text,
                        metadata={
                            "source": file_path.name,
                            "page": page_num,
                            "total_pages": total_pages,
                            "chunk_type": "text",
                        },
                    ))

        except Exception as e:
            logger.error("PDF 解析失败: %s - %s", file_path, e)
            raise

        return chunks

    def parse_bytes(self, data: bytes, filename: str = "") -> list[DocumentChunk]:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("需要安装 pypdf: pip install pypdf")

        chunks: list[DocumentChunk] = []
        try:
            reader = PdfReader(io.BytesIO(data))
            total_pages = len(reader.pages)

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    raw_text = page.extract_text() or ""
                except Exception as e:
                    logger.warning("第 %d 页提取文本失败: %s", page_num, e)
                    continue

                text = clean_text(raw_text)
                if not text:
                    continue

                table_regions = self._detect_table_regions(text)
                if table_regions:
                    chunks.extend(
                        self._split_by_tables(text, page_num, table_regions, filename)
                    )
                else:
                    chunks.append(DocumentChunk(
                        content=text,
                        metadata={
                            "source": filename,
                            "page": page_num,
                            "total_pages": total_pages,
                            "chunk_type": "text",
                        },
                    ))
        except Exception as e:
            logger.error("PDF 字节数据解析失败: %s", e)
            raise

        return chunks

    @staticmethod
    def _detect_table_regions(text: str) -> list[tuple[int, int]]:
        """检测文本中的表格行区域，返回 (start_line, end_line) 列表。"""
        lines = text.splitlines()
        regions: list[tuple[int, int]] = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # 表格行特征：多个连续的多空格分隔字段，或包含 |
            if line and (
                "|" in line
                or len(re.split(r"\s{2,}", line)) >= 3
            ):
                start = i
                while i < len(lines):
                    l = lines[i].strip()
                    if not l:
                        break
                    if "|" in l or len(re.split(r"\s{2,}", l)) >= 3:
                        i += 1
                    else:
                        break
                    # 防止单行误判，至少 2 行才算表格
                if i - start >= 2:
                    regions.append((start, i - 1))
                continue
            i += 1
        return regions

    @staticmethod
    def _split_by_tables(
        text: str, page_num: int, regions: list[tuple[int, int]], source: str
    ) -> list[DocumentChunk]:
        """将页面文本按表格区域拆分为多个 chunk。"""
        lines = text.splitlines()
        chunks: list[DocumentChunk] = []
        last_end = -1

        for start, end in regions:
            # 表格前的普通文本
            if start > last_end + 1:
                plain = "\n".join(lines[last_end + 1 : start]).strip()
                if plain:
                    chunks.append(DocumentChunk(
                        content=plain,
                        metadata={
                            "source": source,
                            "page": page_num,
                            "chunk_type": "text",
                        },
                    ))
            # 表格文本
            table_text = "\n".join(lines[start : end + 1]).strip()
            if table_text:
                chunks.append(DocumentChunk(
                    content=table_text,
                    metadata={
                        "source": source,
                        "page": page_num,
                        "chunk_type": "table",
                    },
                ))
            last_end = end

        # 最后一段普通文本
        if last_end + 1 < len(lines):
            plain = "\n".join(lines[last_end + 1 :]).strip()
            if plain:
                chunks.append(DocumentChunk(
                    content=plain,
                    metadata={
                        "source": source,
                        "page": page_num,
                        "chunk_type": "text",
                    },
                ))

        return chunks
