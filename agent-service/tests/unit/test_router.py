"""Rule router tests — cover all routing targets and edge cases.

Source: app/agent/router.py

Tests are written to match the ACTUAL regex patterns in router.py.
If a test fails, it means either:
  1. The test input doesn't match any pattern → update the test to use a matching input
  2. The regex has a bug → fix the regex in router.py
"""

import pytest

from app.agent.router import RuleRouter, RouteResult


class TestRuleRouter:
    """Test the RuleRouter.route() method against real regex patterns."""

    def setup_method(self):
        self.router = RuleRouter()

    # ── order routing ──────────────────────────────────────────

    @pytest.mark.parametrize(
        "message",
        [
            "我的订单在哪",
            "我的物流到哪了",
            "我的快递到了吗",
            "帮我查物流",
            "帮我查订单",
            "帮我退订单",
            "帮我找快递",
            "取消订单",
            "确认收货",
            "催发货",
            "签收",
            "待付款的订单",
            "已发货",
            "已送达",
            "已关闭",
            "未支付",
            "哪些商品还没评价",
            "查看待评价",
            "好评",
            "帮我退掉这个订单",
            "我的包裹到哪了",
        ],
    )
    def test_order_keywords(self, message):
        result = self.router.route(message)
        assert result.target == "order", f"'{message}' should route to order"
        assert result.confidence >= 0.7

    # ── product routing ────────────────────────────────────────

    @pytest.mark.parametrize(
        "message",
        [
            "帮我找个耳机",
            "帮我搜个手机壳",
            "推荐一个手机",
            "推荐个笔记本",
            "想买个耳机",
            "想买个笔记本",      # 之前未命中，现在应该命中
            "想买个平板",
            "想要一个新手表",
            "iPhone 14 多少钱",
            "什么价",
            "最低多少钱",
        ],
    )
    def test_product_keywords(self, message):
        result = self.router.route(message)
        assert result.target == "product", f"'{message}' should route to product"
        assert result.confidence >= 0.7

    # ── address routing ────────────────────────────────────────

    @pytest.mark.parametrize(
        "message",
        [
            "添加新地址",
            "新增地址",
            "删除地址",
            "查看地址",
            "修改收货地址",      # "收货" 不应触发 order 路由
            "换个收货地址",
        ],
    )
    def test_address_keywords(self, message):
        result = self.router.route(message)
        assert result.target == "address", f"'{message}' should route to address"
        assert result.confidence >= 0.7

    # ── cart routing ───────────────────────────────────────────

    @pytest.mark.parametrize(
        "message",
        [
            "看看我的购物车",
            "查看购物车",
            "打开购物车",
            "加入购物车",
            "添加到购物车",
            "放入购物车",
        ],
    )
    def test_cart_keywords(self, message):
        result = self.router.route(message)
        assert result.target == "cart", f"'{message}' should route to cart"
        assert result.confidence >= 0.7

    # ── fallback to LLM classify ───────────────────────────────

    @pytest.mark.parametrize(
        "message",
        [
            "你好",
            "今天天气怎么样",
            "你是谁",
            "退货要几天",          # knowledge_query — policy question
            "会员有什么权益",       # knowledge_query — generic policy
            "这个商品怎么样",
            "谢谢",
            "运费怎么算",
        ],
    )
    def test_fallback_to_llm_classify(self, message):
        result = self.router.route(message)
        assert result.target == "llm_classify", f"'{message}' should fall back"
        assert result.confidence == 0.0

    # ── result type ────────────────────────────────────────────

    def test_returns_route_result(self):
        result = self.router.route("你好")
        assert isinstance(result, RouteResult)
        assert hasattr(result, "target")
        assert hasattr(result, "confidence")

    # ── first match wins ───────────────────────────────────────

    def test_first_matching_target_wins(self):
        """If a message matches multiple targets, the first one in RULES order wins."""
        result = self.router.route("取消订单")
        assert result.target == "order"

    # ── edge cases that SHOULD fall through ────────────────────

    def test_strong_intent_matches_any_product(self):
        """'想买' is a strong shopping signal — should match even without a product keyword."""
        assert self.router.route("想买个笔记本").target == "product"
        assert self.router.route("想要一个新手表").target == "product"

    def test_weak_intent_needs_product_keyword(self):
        """'推荐' alone is ambiguous — needs a product keyword to confirm."""
        # "推荐" without product keyword → falls through
        assert self.router.route("推荐个好办法").target == "llm_classify"

    def test_strong_intent_no_longer_needs_keyword(self):
        """'想买个笔记本' now correctly routes to product (fixed gap)."""
        assert self.router.route("想买个笔记本").target == "product"
