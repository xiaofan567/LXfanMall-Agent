"""
deepdoc - 深度文档解析模块

提供多种文档格式的结构化解析，输出 DocumentChunk 列表。
支持: PDF, DOCX, Excel, TXT, Markdown, HTML
"""

from .base import BaseParser, DocumentChunk, ParserRegistry, get_parser

# 导入各解析器以触发 @ParserRegistry.register 装饰器
from . import pdf_parser  # noqa: F401
from . import docx_parser  # noqa: F401
from . import excel_parser  # noqa: F401
from . import txt_parser  # noqa: F401
from . import md_parser  # noqa: F401
from . import html_parser  # noqa: F401

__all__ = ["BaseParser", "DocumentChunk", "ParserRegistry", "get_parser"]
