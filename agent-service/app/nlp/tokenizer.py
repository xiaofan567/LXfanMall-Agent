"""中文分词器 — 基于 jieba，针对电商领域优化。

功能：
- 中英文混合文本分词
- 自定义电商词典加载（商品、订单、物流等）
- 生成用于 BM25 检索的空格分隔 token 字符串
"""

import logging
import os

import jieba

logger = logging.getLogger(__name__)

# 电商领域自定义词典 — 词频, 词性
# jieba.load_userdict 格式: 词语 词频 词性（每行一个，可省略词性）
_ECOMMERCE_TERMS = [
    ("商品", 9999, "n"),
    ("订单", 9999, "n"),
    ("物流", 9999, "n"),
    ("退货", 9999, "n"),
    ("退款", 9999, "n"),
    ("优惠券", 9999, "n"),
    ("购物车", 9999, "n"),
    ("收藏夹", 9999, "n"),
    ("收货地址", 9999, "n"),
    ("下单", 9999, "v"),
    ("发货", 9999, "v"),
    ("签收", 9999, "v"),
    ("支付", 9999, "v"),
    ("包邮", 9999, "a"),
    ("满减", 9999, "n"),
    ("秒杀", 9999, "n"),
    ("抢购", 9999, "v"),
    ("评价", 9999, "n"),
    ("售后", 9999, "n"),
    ("客服", 9999, "n"),
    ("库存", 9999, "n"),
    ("SKU", 9999, "nz"),
    ("SPU", 9999, "nz"),
    ("详情页", 9999, "n"),
    ("运费", 9999, "n"),
    ("积分", 9999, "n"),
    ("会员", 9999, "n"),
    ("店铺", 9999, "n"),
    ("品牌", 9999, "n"),
    ("规格", 9999, "n"),
    ("型号", 9999, "n"),
    ("尺码", 9999, "n"),
    ("颜色分类", 9999, "n"),
]

# 自定义词典临时文件名
_DIC_FILENAME = "ecommerce_dict.txt"


def _ensure_custom_dict() -> None:
    """确保自定义词典已加载到 jieba。仅首次调用时执行。"""
    # 使用 jieba 的全局标记避免重复加载
    if getattr(jieba, "_ecommerce_dict_loaded", False):
        return

    # 写入临时词典文件
    dict_path = os.path.join(os.path.dirname(__file__), _DIC_FILENAME)
    if not os.path.exists(dict_path):
        try:
            with open(dict_path, "w", encoding="utf-8") as f:
                for word, freq, pos in _ECOMMERCE_TERMS:
                    f.write(f"{word}\t{freq}\t{pos}\n")
            logger.info("电商自定义词典已生成 | path=%s terms=%d", dict_path, len(_ECOMMERCE_TERMS))
        except OSError as e:
            logger.warning("自定义词典写入失败，将使用默认分词 | error=%s", e)
            jieba._ecommerce_dict_loaded = True  # type: ignore[attr-defined]
            return

    try:
        jieba.load_userdict(dict_path)
        logger.info("电商自定义词典已加载 | terms=%d", len(_ECOMMERCE_TERMS))
    except Exception as e:
        logger.warning("自定义词典加载失败，使用默认词典 | error=%s", e)

    jieba._ecommerce_dict_loaded = True  # type: ignore[attr-defined]


def _is_chinese(char: str) -> bool:
    """判断单个字符是否为中文（CJK统一汉字区块）。"""
    if len(char) != 1:
        return False
    cp = ord(char)
    # CJK统一汉字：U+4E00 ~ U+9FFF
    # CJK扩展A：U+3400 ~ U+4DBF
    # CJK兼容汉字：U+F900 ~ U+FAFF
    return (
        (0x4E00 <= cp <= 0x9FFF)
        or (0x3400 <= cp <= 0x4DBF)
        or (0xF900 <= cp <= 0xFAFF)
    )


class Tokenizer:
    """中文分词器，针对电商搜索场景优化。

    使用 jieba 分词，支持：
    - 中英文混合文本分词
    - 电商专业术语识别
    - 搜索用 token 串生成
    """

    # 过滤掉的无意义短 token（标点、纯空格等）
    _SKIP_CHARS = set(" \t\n\r.,;:!?()[]{}\"'`~@#$%^&*-_+=/\\|<>\u3000\uff0c\u3001\u3002\uff01\uff1f\uff1b\uff1a")

    def __init__(self) -> None:
        """初始化分词器，加载自定义词典。"""
        _ensure_custom_dict()
        logger.info("Tokenizer 初始化完成")

    def tokenize(self, text: str) -> list[str]:
        """对文本进行分词，返回 token 列表。

        Args:
            text: 输入文本（中文/英文混合）

        Returns:
            去除空白和标点后的 token 列表

        Examples:
            >>> tok = Tokenizer()
            >>> tok.tokenize("这个商品的物流速度怎么样？")
            ['这个', '商品', '的', '物流', '速度', '怎么样']
        """
        if not text or not text.strip():
            return []

        try:
            text = text.strip()
            # jieba.cut 返回生成器，lcut 返回列表
            tokens = jieba.lcut(text, cut_all=False)
            # 过滤空白 token 和纯标点 token
            result = [t for t in tokens if t.strip() and t not in self._SKIP_CHARS]
            return result
        except Exception as e:
            logger.error("分词失败 | text=%s error=%s", text[:50], e)
            # 降级：按字符返回
            return [c for c in text.strip() if c not in self._SKIP_CHARS]

    def tokenize_for_search(self, text: str) -> str:
        """将文本分词后拼接为空格分隔字符串，用于 BM25 索引存储。

        Args:
            text: 输入文本

        Returns:
            空格分隔的 token 字符串，可直接存入 Milvus 的 VARCHAR 字段

        Examples:
            >>> tok = Tokenizer()
            >>> tok.tokenize_for_search("退货流程是什么？")
            '退货 流程 是 什么'
        """
        tokens = self.tokenize(text)
        return " ".join(tokens)
