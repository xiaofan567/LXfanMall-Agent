"""关键词提取器 — 基于 jieba TF-IDF 算法。

功能：
- 从文本中提取 top-k 关键词
- 返回关键词及其权重，用于搜索查询构建
"""

import logging

import jieba.analyse

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """基于 TF-IDF 的关键词提取器。

    使用 jieba.analyse.extract_tags，适合从电商商品描述、
    常见问题等文本中提取核心关键词。
    """

    def __init__(self) -> None:
        """初始化关键词提取器。"""
        # jieba.analyse 会自动初始化停用词表
        logger.info("KeywordExtractor 初始化完成")

    def extract(self, text: str, top_k: int = 5) -> list[str]:
        """从文本中提取 top_k 个关键词。

        Args:
            text: 输入文本
            top_k: 返回关键词数量，默认 5

        Returns:
            关键词列表，按 TF-IDF 权重降序排列

        Examples:
            >>> extractor = KeywordExtractor()
            >>> extractor.extract("这款手机壳采用硅胶材质，防摔效果好，适合iPhone15Pro")
            ['手机壳', '硅胶', '材质', '防摔', 'iPhone15Pro']
        """
        if not text or not text.strip():
            return []

        try:
            # jieba TF-IDF 提取
            keywords = jieba.analyse.extract_tags(text, topK=top_k)
            return keywords
        except Exception as e:
            logger.error("关键词提取失败 | text=%s error=%s", text[:50], e)
            return []

    def extract_with_weight(
        self, text: str, top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """提取关键词及其 TF-IDF 权重。

        Args:
            text: 输入文本
            top_k: 返回关键词数量，默认 5

        Returns:
            (关键词, 权重) 元组列表，权重范围 ~0~1

        Examples:
            >>> extractor = KeywordExtractor()
            >>> extractor.extract_with_weight("退货退款流程")
            [('退货', 0.85), ('退款', 0.72), ('流程', 0.45)]
        """
        if not text or not text.strip():
            return []

        try:
            # withWeight=True 返回 (word, weight) 元组
            keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
            return [(kw, float(w)) for kw, w in keywords]
        except Exception as e:
            logger.error("关键词权重提取失败 | text=%s error=%s", text[:50], e)
            return []
