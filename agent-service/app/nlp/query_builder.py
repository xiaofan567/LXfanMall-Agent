"""查询构建器 — 为混合检索（向量 + BM25）构建加权查询。

功能：
- 根据查询文本生成带字段权重的结构化查询
- 简单同义词扩展
- 与 Milvus 集合的 title / keywords / content_tokens 字段配合使用
"""

import logging

from app.nlp.keyword_extractor import KeywordExtractor
from app.nlp.tokenizer import Tokenizer

logger = logging.getLogger(__name__)

# 电商领域简单同义词映射（可扩展为同义词表/词林）
_SYNONYM_MAP: dict[str, list[str]] = {
    "手机": ["手机", "智能手机", "电话"],
    "电脑": ["电脑", "笔记本", "笔记本电脑", "台式机"],
    "衣服": ["衣服", "服装", "服饰", "衣物"],
    "鞋": ["鞋", "鞋子", "运动鞋", "靴子"],
    "退货": ["退货", "退款", "退换"],
    "发货": ["发货", "出货", "配送"],
    "物流": ["物流", "快递", "配送", "运输"],
    "便宜": ["便宜", "优惠", "划算", "性价比高"],
    "好用": ["好用", "好使", "实用", "方便"],
    "质量": ["质量", "品质", "做工"],
    "价格": ["价格", "多少钱", "售价", "价钱"],
}


class QueryBuilder:
    """查询构建器，用于生成加权搜索查询。

    参考 RAGFlow 的做法：对 title / keywords / content 不同字段
    赋予不同权重，提高检索精度。
    """

    def __init__(self) -> None:
        """初始化查询构建器及其依赖组件。"""
        self.tokenizer = Tokenizer()
        self.keyword_extractor = KeywordExtractor()
        logger.info("QueryBuilder 初始化完成")

    def build_weighted_query(
        self,
        query_text: str,
        title_weight: float = 10,
        keyword_weight: float = 20,
        content_weight: float = 2,
    ) -> dict:
        """构建带字段权重的结构化查询。

        将用户查询拆分为：
        - 原始分词 tokens → 用于 title / content_tokens 字段匹配
        - TF-IDF 关键词 → 用于 keywords 字段匹配（权重最高）

        Args:
            query_text: 用户查询文本
            title_weight: 标题字段权重，默认 10
            keyword_weight: 关键词字段权重，默认 20
            content_weight: 正文字段权重，默认 2

        Returns:
            结构化查询字典:
            {
                "tokens": str,           # 空格分隔的分词结果
                "keywords": list[str],   # TF-IDF 提取的关键词
                "field_weights": {       # 字段权重映射
                    "title": float,
                    "keywords": float,
                    "content_tokens": float,
                },
                "query_text": str,       # 原始查询文本
            }

        Examples:
            >>> qb = QueryBuilder()
            >>> q = qb.build_weighted_query("退货退款流程是什么")
            >>> q["keywords"]
            ['退货', '退款', '流程']
            >>> q["field_weights"]["keywords"]
            20
        """
        if not query_text or not query_text.strip():
            return {
                "tokens": "",
                "keywords": [],
                "field_weights": {
                    "title": title_weight,
                    "keywords": keyword_weight,
                    "content_tokens": content_weight,
                },
                "query_text": query_text or "",
            }

        query_text = query_text.strip()

        try:
            # 分词，用于 content_tokens 和 title 的 BM25 匹配
            tokens = self.tokenizer.tokenize_for_search(query_text)

            # 提取关键词，用于 keywords 字段的精确匹配
            # 从查询中提取 top-5 关键词
            keywords = self.keyword_extractor.extract(query_text, top_k=5)

            # 如果提取的关键词为空，退化为分词结果取前5个
            if not keywords:
                all_tokens = self.tokenizer.tokenize(query_text)
                keywords = all_tokens[:5]

            result = {
                "tokens": tokens,
                "keywords": keywords,
                "field_weights": {
                    "title": title_weight,
                    "keywords": keyword_weight,
                    "content_tokens": content_weight,
                },
                "query_text": query_text,
            }

            logger.debug(
                "加权查询构建完成 | query=%s keywords=%s",
                query_text[:30], keywords,
            )
            return result

        except Exception as e:
            logger.error("查询构建失败 | query=%s error=%s", query_text[:30], e)
            # 降级：返回基本查询
            return {
                "tokens": query_text,
                "keywords": [query_text],
                "field_weights": {
                    "title": title_weight,
                    "keywords": keyword_weight,
                    "content_tokens": content_weight,
                },
                "query_text": query_text,
            }

    def expand_with_synonyms(self, query_text: str) -> str:
        """简单同义词扩展。

        将查询中的词替换为包含同义词的 OR 查询。
        当前实现为简单的字典映射，可后续接入同义词词林或 LLM 扩展。

        Args:
            query_text: 用户查询文本

        Returns:
            扩展后的查询文本（用空格连接所有同义词变体）

        Examples:
            >>> qb = QueryBuilder()
            >>> qb.expand_with_synonyms("退货流程")
            '退货 退款 退换 流程'
        """
        if not query_text or not query_text.strip():
            return ""

        query_text = query_text.strip()

        try:
            tokens = self.tokenizer.tokenize(query_text)
            expanded_tokens: list[str] = []

            for token in tokens:
                expanded_tokens.append(token)
                # 查找同义词并添加
                synonyms = _SYNONYM_MAP.get(token, [])
                for syn in synonyms:
                    if syn != token and syn not in expanded_tokens:
                        expanded_tokens.append(syn)

            result = " ".join(expanded_tokens)
            logger.debug("同义词扩展 | input=%s output=%s", query_text[:30], result[:60])
            return result

        except Exception as e:
            logger.error("同义词扩展失败 | query=%s error=%s", query_text[:30], e)
            return query_text
