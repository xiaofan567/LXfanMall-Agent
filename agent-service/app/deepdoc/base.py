"""
deepdoc/base.py - 解析器基类与注册工厂

提供 DocumentChunk 数据类、BaseParser 抽象基类、ParserRegistry 注册表和 get_parser 工厂函数。
"""

from __future__ import annotations

import logging
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """文档解析后的文本块。"""
    content: str
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    """文档解析器抽象基类。"""

    @abstractmethod
    def parse(self, file_path: str | Path) -> list[DocumentChunk]:
        """解析文件路径，返回 DocumentChunk 列表。"""
        ...

    def parse_bytes(self, data: bytes, filename: str = "") -> list[DocumentChunk]:
        """解析字节数据。默认写入临时文件后调用 parse()。"""
        suffix = Path(filename).suffix if filename else ".tmp"
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(data)
            tmp.flush()
            tmp.close()
            return self.parse(tmp.name)
        finally:
            if tmp and os.path.exists(tmp.name):
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass

    def parse_fileobj(self, fileobj: IO[bytes], filename: str = "") -> list[DocumentChunk]:
        """解析文件对象。"""
        return self.parse_bytes(fileobj.read(), filename)


# ---------------------------------------------------------------------------
# 解析器注册表
# ---------------------------------------------------------------------------

class ParserRegistry:
    """解析器注册表：扩展名 -> 解析器类。"""

    _registry: dict[str, type[BaseParser]] = {}

    @classmethod
    def register(cls, extensions: list[str]):
        """装饰器，将解析器注册到指定扩展名。"""
        def decorator(parser_cls: type[BaseParser]):
            for ext in extensions:
                cls._registry[ext.lower()] = parser_cls
            return parser_cls
        return decorator

    @classmethod
    def get(cls, extension: str) -> type[BaseParser] | None:
        return cls._registry.get(extension.lower().lstrip("."))

    @classmethod
    def all_extensions(cls) -> list[str]:
        return list(cls._registry.keys())


def get_parser(file_extension: str) -> BaseParser:
    """根据文件扩展名获取解析器实例。"""
    ext = file_extension.lower().lstrip(".")
    parser_cls = ParserRegistry.get(ext)
    if parser_cls is None:
        raise ValueError(
            f"不支持的文件格式: .{ext}，支持的格式: {ParserRegistry.all_extensions()}"
        )
    return parser_cls()
