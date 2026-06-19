"""基于规则的轻量路由层 — 零 Token 消耗。

只匹配"不可能有歧义"的明确指令模式，
模糊的、可能涉及政策/知识的问题全部交给 LLM 意图分类器判断。
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """路由结果。"""

    target: str  # "order" | "product" | "address" | "cart" | "llm_classify"
    confidence: float  # 0.0 ~ 1.0


class RuleRouter:
    """基于规则的轻量路由，零 Token 消耗。

    设计原则：每条规则都要通过"有没有第二种解释"的测试。
    有歧义的一律不收，交给 LLM 判断。
    """

    # 关键词 → 路由目标（只收不可能有歧义的模式）
    RULES: dict[str, list[str]] = {
        "order": [
            # 带主语"我的" — 一定是在查个人数据
            r"我的(订单|物流|快递|包裹|退货|退款|单)",
            # 带"帮我"的请求 — 明确执行意图
            r"帮我.*(查|看|退|取消|催|找).*(订单|物流|快递|包裹)",
            # 明确操作指令（带祈使语气）
            # "收货" 需排除"收货地址"（那是 address 意图）
            r"(取消|催一下|催发货|确认收货|签收|确认|收货(?!地址))",
            # 评价相关 — 查未评价 / 提交评价
            r"(未评价|待评价|还没评价|评价一下|哪些.*评价|查看.*评价|好评|差评|给.*评|写.*评|几星|星级|评个)",
            # 按状态查订单
            r"(未支付|待付款|待发货|已发货|已送达|已关闭)",
        ],
        "product": [
            # 强购物意图 — "想买/想要" 后面跟什么都行
            r"(想买|想要).+",
            # 弱购物意图 — "推荐/帮我找" 需要商品词确认
            r"(推荐|帮我找|帮我搜).*(商品|手机|电脑|笔记本|平板|衣服|鞋|耳机|包|什么|一个)",
            # 明确问价
            r"(多少钱|什么价|最低.*多少)",
        ],
        "address": [
            # 明确地址操作
            r"(改|修改|添加|新增|删除|换|查看|看下).*地址",
        ],
        "cart": [
            # 购物车操作
            r"(我的|查看|看下|打开|看看).*购物车",
            r"加(入|到|进).*购物车",
            r"(添加|放|丢|扔).*购物车",
        ],
    }

    def route(self, message: str) -> RouteResult:
        """根据规则匹配路由目标。"""
        for target, patterns in self.RULES.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    logger.info("规则路由命中 | target=%s pattern=%s", target, pattern)
                    return RouteResult(target=target, confidence=0.9)

        # 未命中 → 交给 LLM 分类
        logger.info("规则路由未命中，回退到 LLM 分类")
        return RouteResult(target="llm_classify", confidence=0.0)


# 全局单例
rule_router = RuleRouter()
