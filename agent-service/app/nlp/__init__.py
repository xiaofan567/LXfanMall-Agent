"""
NLP处理模块 - 提供中文分词、关键词提取、查询构建、文本处理等功能。
用于电商购物助手的RAG检索系统，支持BM25/关键词匹配通道。
"""

from .tokenizer import Tokenizer
from .keyword_extractor import KeywordExtractor
from .query_builder import QueryBuilder
from .text_processor import TextProcessor

__all__ = [
    "Tokenizer",
    "KeywordExtractor",
    "QueryBuilder",
    "TextProcessor",
]

# 模块级别的懒加载单例
_tokenizer: Tokenizer | None = None
_keyword_extractor: KeywordExtractor | None = None
_query_builder: QueryBuilder | None = None
_text_processor: TextProcessor | None = None


def get_tokenizer() -> Tokenizer:
    """获取全局Tokenizer单例"""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = Tokenizer()
    return _tokenizer


def get_keyword_extractor() -> KeywordExtractor:
    """获取全局KeywordExtractor单例"""
    global _keyword_extractor
    if _keyword_extractor is None:
        _keyword_extractor = KeywordExtractor()
    return _keyword_extractor


def get_query_builder() -> QueryBuilder:
    """获取全局QueryBuilder单例"""
    global _query_builder
    if _query_builder is None:
        _query_builder = QueryBuilder()
    return _query_builder


def get_text_processor() -> TextProcessor:
    """获取全局TextProcessor单例"""
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor
