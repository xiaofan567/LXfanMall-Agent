"""文本处理器 — 清洗、截断、停用词过滤。

功能：
- 文本清洗（去除控制字符、规范化空白）
- 按 token 数量截断文本
- 中文停用词集合
"""

import logging
import re
import unicodedata

from app.nlp.tokenizer import Tokenizer

logger = logging.getLogger(__name__)

# 中文常见停用词集合
# 来源：百度停用词表 + 哈工大停用词表，精选电商场景高频无意义词
CHINESE_STOP_WORDS: frozenset[str] = frozenset({
    # 代词
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们",
    "这", "那", "这个", "那个", "这些", "那些", "这里", "那里",
    "什么", "怎么", "怎样", "哪", "哪些", "哪里", "多少",
    # 介词 / 连词 / 助词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这", "他", "吗",
    "把", "从", "而", "但", "与", "及", "或", "等", "对",
    "为", "以", "于", "由", "从", "向", "被", "给",
    # 语气词 / 叹词
    "啊", "呀", "吧", "呢", "哦", "哈", "嗯", "嘛", "哎",
    "唉", "呃", "噢", "嘿",
    # 量词 / 数词 / 方位词
    "个", "些", "每", "各", "第", "几", "左右",
    "上", "下", "前", "后", "里", "外", "中",
    # 副词 / 连接词
    "不", "没", "没有", "别", "再", "又", "就", "才", "还",
    "都", "只", "仅", "也", "已", "已经", "曾经",
    "并且", "而且", "但是", "然而", "虽然", "尽管",
    "因为", "所以", "如果", "假如", "只要", "只有",
    "因此", "于是", "不过", "否则", "然后",
    # 常见动词（语义过于泛化）
    "是", "有", "在", "能", "可以", "可能", "应该", "需要",
    "使用", "进行", "通过", "经过", "作为",
    # 标点与特殊符号
    "，", "。", "！", "？", "；", "：", "、", "（", "）",
    "【", "】", "「", "」", "《", "》", "\"", "\"",
    "'", "'", "…", "——", "·", "/", "\\", "|",
    # 英文常见停用词
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "into", "about", "between", "through", "during", "before", "after",
    "and", "but", "or", "not", "no", "nor", "so", "if", "then",
    "up", "out", "off", "over", "under", "again", "further",
})

# 控制字符正则 — 匹配 Unicode 控制字符（保留常见空白）
_CONTROL_CHAR_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffe\uffff]"
)

# 连续空白正则
_MULTI_WHITESPACE_RE = re.compile(r"\s+")


class TextProcessor:
    """文本处理器，提供清洗、截断和停用词功能。"""

    def __init__(self) -> None:
        """初始化文本处理器。"""
        self._tokenizer: Tokenizer | None = None
        logger.info("TextProcessor 初始化完成")

    @property
    def tokenizer(self) -> Tokenizer:
        """懒加载 Tokenizer 实例。"""
        if self._tokenizer is None:
            self._tokenizer = Tokenizer()
        return self._tokenizer

    def clean_for_indexing(self, text: str) -> str:
        """清洗文本用于索引入库。

        处理步骤：
        1. 去除 Unicode 控制字符
        2. Unicode NFKC 规范化（合并全角/半角字符）
        3. 规范化连续空白为单个空格
        4. 去除首尾空白

        Args:
            text: 原始文本

        Returns:
            清洗后的文本

        Examples:
            >>> tp = TextProcessor()
            >>> tp.clean_for_indexing("  商品\\n\\n质量  不错  ")
            '商品 质量 不错'
        """
        if not text:
            return ""

        try:
            # 去除控制字符
            cleaned = _CONTROL_CHAR_RE.sub("", text)
            # Unicode NFKC 规范化：全角→半角，兼容字符→标准字符
            cleaned = unicodedata.normalize("NFKC", cleaned)
            # 规范化空白
            cleaned = _MULTI_WHITESPACE_RE.sub(" ", cleaned)
            return cleaned.strip()
        except Exception as e:
            logger.error("文本清洗失败 | text=%s error=%s", text[:50], e)
            return text.strip()

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """将文本截断到指定 token 数量限制。

        先分词，取前 max_tokens 个 token，再拼接回字符串。
        确保不会因为截断导致半个 UTF-8 字符。

        Args:
            text: 原始文本
            max_tokens: 最大 token 数量

        Returns:
            截断后的文本

        Examples:
            >>> tp = TextProcessor()
            >>> tp.truncate_to_tokens("一二三四五", 3)
            '一 二 三'
        """
        if not text or max_tokens <= 0:
            return ""

        try:
            tokens = self.tokenizer.tokenize(text)
            if len(tokens) <= max_tokens:
                return text  # 未超过限制，原样返回
            # 截断并用空格拼接（token 化后的格式）
            return " ".join(tokens[:max_tokens])
        except Exception as e:
            logger.error("文本截断失败 | text=%s error=%s", text[:50], e)
            # 降级：按字符粗略截断
            if len(text) <= max_tokens * 3:
                return text
            return text[: max_tokens * 3]

    def remove_stop_words(self, tokens: list[str]) -> list[str]:
        """从 token 列表中移除停用词。

        Args:
            tokens: 分词结果列表

        Returns:
            去除停用词后的 token 列表
        """
        return [t for t in tokens if t.lower() not in CHINESE_STOP_WORDS and t.strip()]

    @staticmethod
    def get_stop_words() -> frozenset[str]:
        """返回中文停用词集合（只读）。"""
        return CHINESE_STOP_WORDS
