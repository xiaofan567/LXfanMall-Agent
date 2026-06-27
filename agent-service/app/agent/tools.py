"""LangChain Tool 定义 — Agent 可调用的商城工具。

每个 Tool 的设计原则：
- 内部调用 MallAdapter 获取真实数据（对齐 Java mall-portal 后端 API）
- 完整数据暂存到 ToolResultStore（给前端渲染卡片）
- 返回精简摘要给 LLM（用于决策和生成回复）

认证说明：
- Java 后端通过 JWT token 识别用户（SecurityContextHolder），不需要 member_id 参数
- MallAdapter 的 HTTP 请求只需携带 Authorization 头即可
- 用户名（username）从 JWT 的 sub 字段获取，用于退款等需要 username 的场景

注意：所有工具必须是 async def，因为 MallAdapter 方法是异步的。
LangChain @tool 装饰器原生支持 async 函数。
"""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from typing import Any

from langchain_core.tools import tool

from app.agent.tool_result import tool_result_store
from app.config.constants import DESTRUCTIVE_TOOLS, INJECTION_PATTERNS
from app.mcp.mall_adapter import get_mall_adapter

logger = logging.getLogger(__name__)

# 请求上下文 — 由 chat 端点设置
_current_token: ContextVar[str | None] = ContextVar("current_token", default=None)
_current_member_username: ContextVar[str] = ContextVar("current_member_username", default="")


def set_request_context(
    token: str | None = None,
    member_username: str = "",
) -> None:
    """在请求入口设置上下文。"""
    _current_token.set(token)
    _current_member_username.set(member_username or "")


def _get_token() -> str | None:
    return _current_token.get()


def _get_member_username() -> str:
    return _current_member_username.get()


def get_current_username() -> str:
    """获取当前请求的用户名（来自 JWT sub 字段）。

    供 nodes.py 等外部模块读取，用于查询用户画像。
    未登录时返回空字符串。
    """
    return _current_member_username.get()


def _is_authenticated() -> bool:
    """检查是否有有效的 JWT token。"""
    return _current_token.get() is not None


def _safe_json(data: Any) -> str:
    """安全序列化，避免中文转义。"""
    return json.dumps(data, ensure_ascii=False, default=str)


# ── 输入消毒 ──────────────────────────────────────────


def sanitize_input(text: str) -> bool:
    """检测用户输入中是否包含 prompt 注入模式。

    Returns:
        True 表示安全，False 表示检测到注入。
    """
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in text_lower:
            logger.warning("检测到疑似 prompt 注入 | pattern=%s input=%s", pattern, text[:100])
            return False
    return True


# ── 待确认操作存储 ──────────────────────────────────────


class PendingActionStore:
    """内存存储待确认的破坏性操作。

    每个待确认操作有一个唯一 action_id，TTL 默认 5 分钟。
    """

    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def put(
        self,
        tool_name: str,
        params: dict[str, Any],
        description: str,
        username: str = "",
    ) -> str:
        """存储一个待确认操作，返回 action_id。"""
        # 清理过期条目
        self._cleanup()

        action_id = str(uuid.uuid4())[:8]
        self._store[action_id] = {
            "action_id": action_id,
            "tool_name": tool_name,
            "params": params,
            "description": description,
            "username": username,
            "created_at": time.time(),
        }
        logger.info(
            "PendingAction 存储 | action_id=%s tool=%s desc=%s",
            action_id, tool_name, description,
        )
        return action_id

    def get(self, action_id: str) -> dict[str, Any] | None:
        """取出并移除一个待确认操作（一次性消费）。"""
        self._cleanup()
        return self._store.pop(action_id, None)

    def peek(self, action_id: str) -> dict[str, Any] | None:
        """查看但不移除。"""
        self._cleanup()
        return self._store.get(action_id)

    def get_pending_for_request(self, username: str) -> list[dict[str, Any]]:
        """获取指定用户的所有待确认操作（不移除）。"""
        self._cleanup()
        return [
            v for v in self._store.values()
            if v.get("username") == username
        ]

    def clear_for_request(self, username: str) -> list[dict[str, Any]]:
        """取出并移除指定用户的所有待确认操作。"""
        self._cleanup()
        keys_to_remove = [
            k for k, v in self._store.items()
            if v.get("username") == username
        ]
        results = []
        for k in keys_to_remove:
            results.append(self._store.pop(k))
        return results

    def _cleanup(self) -> None:
        """移除过期条目。"""
        now = time.time()
        expired = [
            k for k, v in self._store.items()
            if now - v.get("created_at", 0) > self._ttl
        ]
        for k in expired:
            self._store.pop(k, None)


# 全局实例
pending_action_store = PendingActionStore()


def _build_tool_description(tool_name: str, params: dict[str, Any]) -> str:
    """为待确认操作生成人类可读的描述。"""
    descriptions = {
        "cancel_order": lambda p: f"取消订单 #{p.get('order_id', '?')}",
        "delete_order": lambda p: f"删除订单 #{p.get('order_id', '?')}",
        "apply_refund": lambda p: f"为订单 #{p.get('order_id', '?')} 申请退款（原因: {p.get('reason', '?')}）",
        "confirm_receive": lambda p: f"确认收货 订单 #{p.get('order_id', '?')}",
        "mark_delivered": lambda p: f"标记订单 #{p.get('order_id', '?')} 为已送达",
        "delete_address": lambda p: f"删除收货地址 #{p.get('address_id', '?')}",
        "create_address": lambda p: f"新增收货地址: {p.get('name', '?')} {p.get('phone', '?')} {p.get('address', '?')}",
        "update_address": lambda p: f"修改收货地址 #{p.get('address_id', '?')}: {p.get('name', '?')} {p.get('phone', '?')} {p.get('address', '?')}",
        "add_to_cart": lambda p: f"添加 {p.get('quantity', 1)} 件商品 (ID: {p.get('product_id', '?')}) 到购物车",
        "create_review": lambda p: f"提交商品评价: {p.get('star', '?')} 星",
    }
    builder = descriptions.get(tool_name)
    if builder:
        return builder(params)
    return f"执行操作: {tool_name}({params})"


def _is_destructive(tool_name: str) -> bool:
    """判断工具是否为破坏性操作。"""
    return tool_name in DESTRUCTIVE_TOOLS


# ── 工具包装：破坏性操作拦截 ─────────────────────────────


def _wrap_destructive(original_tool_fn):
    """包装破坏性工具：拦截执行，存入 PendingActionStore，返回确认请求文本。"""
    tool_name = original_tool_fn.name

    async def wrapped_fn(**kwargs):
        # LangChain 调用 @tool 包装的函数时，会把参数包在 'kwargs' key 里传入
        # 例如 wrapped_fn(kwargs={'order_id': 89, ...}) 而非 wrapped_fn(order_id=89, ...)
        # 需要解包才能拿到真正的参数
        actual_params = kwargs
        if len(kwargs) == 1 and "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
            actual_params = kwargs["kwargs"]

        # 构建描述
        description = _build_tool_description(tool_name, actual_params)
        username = _get_member_username()

        # 存入待确认队列
        action_id = pending_action_store.put(
            tool_name=tool_name,
            params=actual_params,
            description=description,
            username=username,
        )

        logger.info("破坏性操作已拦截，等待用户确认 | tool=%s action_id=%s", tool_name, action_id)

        # 返回确认请求文本给 LLM（LLM 会据此生成回复告知用户）
        return (
            f"[待确认操作] {description}\n"
            f"action_id: {action_id}\n"
            f"此操作需要用户确认后才能执行。请告知用户需要确认，并说明操作内容。"
        )

    # 复制原工具的元数据（LangChain 需要 name 和 description 来注册工具）
    wrapped_fn.__name__ = original_tool_fn.name
    wrapped_fn.__doc__ = original_tool_fn.description
    wrapped_fn.name = original_tool_fn.name
    wrapped_fn.description = original_tool_fn.description
    wrapped_fn.args_schema = original_tool_fn.args_schema

    # 标记为已包装（用于调试）
    wrapped_fn._is_wrapped = True
    wrapped_fn._original_tool = original_tool_fn

    return wrapped_fn


# ── 商品工具 ──────────────────────────────────────────


@tool
async def search_products(
    keyword: str,
    category_id: int | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
) -> str:
    """搜索商城商品。根据关键词查找商品，可选分类和价格范围筛选。返回商品列表摘要。"""
    adapter = get_mall_adapter()
    try:
        result = await adapter.search_products(
            keyword=keyword,
            category_id=category_id,
            page_num=1,  # PageHelper 从 1 开始
            page_size=10,
        )
    except Exception as exc:
        logger.error("搜索商品失败: %s", exc)
        return f"搜索商品时出错: {exc}"

    # ── 调试：记录 Java 后端原始返回 ──
    logger.info(
        "🔍 [DEBUG] search_products raw | keyword=%s code=%s total=%s list_len=%s",
        keyword,
        result.get("code"),
        result.get("data", {}).get("total") if isinstance(result.get("data"), dict) else "N/A",
        len(result.get("data", {}).get("list", [])) if isinstance(result.get("data"), dict) else "N/A",
    )

    code = result.get("code")
    data = result.get("data", {})
    # CommonPage 格式: { pageNum, pageSize, totalPage, total, list }
    products = data.get("list", []) if isinstance(data, dict) else []

    # 完整数据暂存（给前端渲染卡片）
    # 即使无结果也要存（空列表），触发互斥清除推荐类工具的脏数据
    tool_result_store.store("search_products", products)

    if code != 200 or not products:
        return f"未找到与「{keyword}」相关的商品"

    # 精简摘要返回给 LLM
    summary_parts = [f"找到 {len(products)} 个与「{keyword}」相关的商品:"]
    for i, p in enumerate(products[:8], 1):
        name = p.get("name", "未知")
        price = p.get("price", "?")
        summary_parts.append(f"{i}. {name} (¥{price})")
    return "\n".join(summary_parts)


@tool
async def get_product_info(product_id: int) -> str:
    """获取商品详情。传入商品ID，返回名称、价格、库存等信息。"""
    adapter = get_mall_adapter()
    try:
        result = await adapter.get_product_info(product_id)
    except Exception as exc:
        logger.error("获取商品详情失败: %s", exc)
        return f"获取商品详情时出错: {exc}"

    code = result.get("code")
    data = result.get("data")

    if code != 200 or not data:
        return f"未找到商品 (ID: {product_id})"

    # PmsPortalProductDetail 结构: { product: PmsProduct, brand, skuStockList, ... }
    product = data.get("product", data)  # 兼容直接返回商品的情况

    # 完整数据暂存
    tool_result_store.store("get_product_info", product)

    # 精简摘要 — 字段对齐 PmsProduct
    name = product.get("name", "未知")
    price = product.get("price", "?")
    original_price = product.get("originalPrice")
    stock = product.get("stock", "?")
    sale = product.get("sale", 0)
    desc = (product.get("subTitle") or product.get("description") or "")[:100]

    lines = [f"商品: {name}", f"价格: ¥{price}"]
    if original_price and original_price != price:
        lines.append(f"原价: ¥{original_price}")
    lines.extend([f"库存: {stock}", f"销量: {sale}"])
    if desc:
        lines.append(f"描述: {desc}")
    return "\n".join(lines)


@tool
async def get_recommendations() -> str:
    """获取个性化商品推荐。根据用户偏好推荐商品。"""
    adapter = get_mall_adapter()
    try:
        result = await adapter.get_recommendations(limit=6)
    except Exception as exc:
        logger.error("获取推荐失败: %s", exc)
        return f"获取推荐时出错: {exc}"

    code = result.get("code")
    # /home/recommendProductList 直接返回 List<PmsProduct>
    data = result.get("data", [])
    products = data if isinstance(data, list) else []

    if code != 200 or not products:
        return "暂无推荐商品"

    tool_result_store.store("get_recommendations", products)

    summary_parts = [f"为您推荐 {len(products)} 个商品:"]
    for i, p in enumerate(products[:6], 1):
        name = p.get("name", "未知")
        price = p.get("price", "?")
        summary_parts.append(f"{i}. {name} (¥{price})")
    return "\n".join(summary_parts)


@tool
async def get_hot_products() -> str:
    """获取热门商品列表。"""
    adapter = get_mall_adapter()
    try:
        result = await adapter.get_hot_products()
    except Exception as exc:
        logger.error("获取热门商品失败: %s", exc)
        return f"获取热门商品时出错: {exc}"

    code = result.get("code")
    data = result.get("data", [])
    products = data if isinstance(data, list) else []

    if code != 200 or not products:
        return "暂无热门商品"

    tool_result_store.store("get_hot_products", products)

    summary_parts = [f"热门商品 {len(products)} 个:"]
    for i, p in enumerate(products[:6], 1):
        name = p.get("name", "未知")
        price = p.get("price", "?")
        summary_parts.append(f"{i}. {name} (¥{price})")
    return "\n".join(summary_parts)


@tool
async def get_new_products() -> str:
    """获取新品上架商品列表。"""
    adapter = get_mall_adapter()
    try:
        result = await adapter.get_new_products()
    except Exception as exc:
        logger.error("获取新品失败: %s", exc)
        return f"获取新品时出错: {exc}"

    code = result.get("code")
    data = result.get("data", [])
    products = data if isinstance(data, list) else []

    if code != 200 or not products:
        return "暂无新品"

    tool_result_store.store("get_new_products", products)

    summary_parts = [f"新品上架 {len(products)} 个:"]
    for i, p in enumerate(products[:6], 1):
        name = p.get("name", "未知")
        price = p.get("price", "?")
        summary_parts.append(f"{i}. {name} (¥{price})")
    return "\n".join(summary_parts)


# ── 订单工具 ──────────────────────────────────────────


@tool
async def get_user_orders(status: int = -1) -> str:
    """查询用户订单列表。status: -1=全部 0=待付款 1=待发货 2=已发货 7=已送达 3=已完成 4=已关闭。"""
    if not _is_authenticated():
        return "用户未登录，无法查询订单。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_user_orders(status=status, token=token)
    except Exception as exc:
        logger.error("查询订单失败: %s", exc)
        return f"查询订单时出错: {exc}"

    code = result.get("code")
    data = result.get("data", {})
    orders = data.get("list", []) if isinstance(data, dict) else []

    if code != 200 or not orders:
        return "您暂无订单记录"

    # 不往 tool_result_store 存数据 — get_user_orders 只给 LLM 看摘要
    # 卡片由 get_order_detail 产生，避免前端渲染全部订单

    # 状态映射对齐 Java OmsOrder.status
    status_map = {0: "待付款", 1: "待发货", 2: "已发货", 7: "已送达", 3: "已完成", 4: "已关闭", 5: "无效"}
    summary_parts = [f"您有 {len(orders)} 个订单:"]
    for o in orders[:5]:
        oid = o.get("id", "?")
        order_sn = o.get("orderSn", "?")
        # OmsOrderItem 字段: productName, productPic
        items = o.get("orderItemList", [])
        product_name = items[0].get("productName", "未知商品") if items else "未知商品"
        total = o.get("totalAmount", "?")
        s = status_map.get(o.get("status", -1), "未知")
        summary_parts.append(f"- ID:{oid} 订单{order_sn}: {product_name} ¥{total} [{s}]")
    return "\n".join(summary_parts)


@tool
async def get_order_detail(order_id: int) -> str:
    """获取订单详情。传入订单ID，返回完整的订单信息。"""
    if not _is_authenticated():
        return "用户未登录，无法查询订单。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_order_detail(order_id, token=token)
    except Exception as exc:
        logger.error("获取订单详情失败: %s", exc)
        return f"获取订单详情时出错: {exc}"

    code = result.get("code")
    data = result.get("data")

    if code != 200 or not data:
        return f"未找到订单 (ID: {order_id})"

    tool_result_store.store("get_order_detail", data)

    order_sn = data.get("orderSn", "?")
    status_map = {0: "待付款", 1: "待发货", 2: "已发货", 7: "已送达", 3: "已完成", 4: "已关闭", 5: "无效"}
    s = status_map.get(data.get("status", -1), "未知")
    total = data.get("totalAmount", "?")
    pay_amount = data.get("payAmount", "?")
    items = data.get("orderItemList", [])
    item_names = ", ".join([i.get("productName", "?") for i in items[:3]])
    receiver = data.get("receiverName", "?")
    address = data.get("receiverDetailAddress", "?")

    return (
        f"订单ID: {order_id} | 订单号: {order_sn}: {item_names}\n"
        f"总金额: ¥{total} (实付: ¥{pay_amount})\n"
        f"状态: {s}\n"
        f"收件人: {receiver} {address}"
    )


@tool
async def get_logistics(order_id: int | None = None, order_sn: str | None = None) -> str:
    """查询订单物流信息。可以传入订单ID(order_id)或订单编号(order_sn)。
    如果都不传，会自动查询最近已发货订单的物流信息。"""
    if not _is_authenticated():
        return "用户未登录，无法查询物流。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()

    # 如果没有传入任何参数，自动查询已发货订单
    if not order_id and not order_sn:
        try:
            orders_result = await adapter.get_user_orders(status=2, page_num=1, page_size=10, token=token)
            if orders_result.get("code") == 200:
                orders_data = orders_result.get("data", {})
                orders = orders_data.get("list", []) if isinstance(orders_data, dict) else []
                if not orders:
                    return "您暂无已发货的订单"
                # 取第一个已发货订单
                order_id = orders[0].get("id")
                order_sn = orders[0].get("orderSn", "")
                logger.info("自动查询已发货订单: order_id=%s, order_sn=%s", order_id, order_sn)
        except Exception as exc:
            logger.error("查询订单列表失败: %s", exc)
            return f"查询订单列表时出错: {exc}"

    # 如果传入的是 order_sn，需要先查询订单列表找到对应的 order_id
    if order_sn and not order_id:
        try:
            orders_result = await adapter.get_user_orders(status=-1, page_num=1, page_size=100, token=token)
            if orders_result.get("code") == 200:
                orders_data = orders_result.get("data", {})
                orders = orders_data.get("list", []) if isinstance(orders_data, dict) else []
                for order in orders:
                    if order.get("orderSn") == order_sn:
                        order_id = order.get("id")
                        break
        except Exception as exc:
            logger.error("查询订单列表失败: %s", exc)
            return f"查询订单列表时出错: {exc}"

    if not order_id:
        return f"未找到订单编号为 {order_sn} 的订单，请确认订单编号是否正确"

    try:
        result = await adapter.get_logistics(order_id, token=token)
    except Exception as exc:
        logger.error("查询物流失败: %s", exc)
        return f"查询物流时出错: {exc}"

    code = result.get("code")
    data = result.get("data")

    if code != 200 or not data:
        return f"未找到订单 (ID: {order_id}) 的物流信息"

    tool_result_store.store("get_logistics", data)

    # LogisticsDetailResult 字段: deliveryCompany, deliverySn, traceList
    company = data.get("deliveryCompany", "未知快递")
    tracking_no = data.get("deliverySn", "?")
    traces = data.get("traceList", [])
    # traces 按 status_code ASC 排序，取最后一条才是最新状态
    latest = traces[-1].get("statusText", "未知") if traces else "暂无物流信息"

    return f"快递公司: {company}\n运单号: {tracking_no}\n最新状态: {latest}"


@tool
async def apply_refund(order_id: int, product_id: int, reason: str) -> str:
    """申请退货退款。需要提供订单ID、商品ID和退款原因。"""
    if not _is_authenticated():
        return "用户未登录，无法申请退款。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    username = _get_member_username()
    try:
        result = await adapter.apply_refund(
            order_id=order_id,
            product_id=product_id,
            reason=reason,
            member_username=username,
            token=token,
        )
    except Exception as exc:
        logger.error("申请退款失败: %s", exc)
        return f"申请退款时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "申请失败")
        return f"退款申请失败: {msg}"

    tool_result_store.store("apply_refund", {"orderId": order_id, "productId": product_id, "reason": reason})
    return f"退货退款申请已提交（订单ID: {order_id}），请等待商家审核。"


@tool
async def cancel_order(order_id: int) -> str:
    """取消订单。传入订单ID，取消未付款的订单。"""
    if not _is_authenticated():
        return "用户未登录，无法取消订单。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.cancel_order(order_id, token=token)
    except Exception as exc:
        logger.error("取消订单失败: %s", exc)
        return f"取消订单时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "取消失败")
        return f"取消订单失败: {msg}"

    return f"订单 (ID: {order_id}) 已取消。"


@tool
async def confirm_receive(order_id: int) -> str:
    """确认收货。传入订单ID，将已发货/已送达的订单标记为已完成。
    注意：必须先调用 get_user_orders 获取真实订单ID，不要编造ID。
    """
    if not _is_authenticated():
        return "用户未登录，无法确认收货。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.confirm_receive(order_id, token=token)
    except Exception as exc:
        logger.error("确认收货失败: %s", exc)
        return f"确认收货失败: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "确认失败")
        return f"确认收货失败: {msg}"

    return f"订单 (ID: {order_id}) 已确认收货，感谢您的购买！"


@tool
async def mark_delivered(order_id: int) -> str:
    """将已发货的订单标记为已送达。表示货物已送到用户取货地。
    注意：必须先调用 get_user_orders 获取真实订单ID。
    """
    if not _is_authenticated():
        return "用户未登录，无法操作。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.mark_delivered(order_id, token=token)
    except Exception as exc:
        logger.error("标记送达失败: %s", exc)
        return f"标记送达失败: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "操作失败")
        return f"标记送达失败: {msg}"

    return f"订单 (ID: {order_id}) 已标记为已送达。"


@tool
async def delete_order(order_id: int) -> str:
    """删除订单。传入订单ID，删除已完成或已关闭的订单。"""
    if not _is_authenticated():
        return "用户未登录，无法删除订单。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.delete_order(order_id, token=token)
    except Exception as exc:
        logger.error("删除订单失败: %s", exc)
        return f"删除订单时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "删除失败")
        return f"删除订单失败: {msg}"

    return f"订单 (ID: {order_id}) 已删除。"


@tool
async def get_refund_list() -> str:
    """查询用户的退货退款申请列表。"""
    if not _is_authenticated():
        return "用户未登录，无法查询退款记录。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    username = _get_member_username()
    try:
        result = await adapter.get_refund_list(member_username=username, token=token)
    except Exception as exc:
        logger.error("查询退款列表失败: %s", exc)
        return f"查询退款列表时出错: {exc}"

    code = result.get("code")
    data = result.get("data", [])
    refunds = data if isinstance(data, list) else []

    if code != 200 or not refunds:
        return "您暂无退款申请记录"

    tool_result_store.store("get_refund_list", refunds)

    status_map = {0: "待处理", 1: "退货中", 2: "已完成", 3: "已拒绝"}
    summary_parts = [f"您有 {len(refunds)} 条退款申请:"]
    for r in refunds[:5]:
        rid = r.get("id", "?")
        product_name = r.get("productName", "?")
        s = status_map.get(r.get("status", -1), "未知")
        summary_parts.append(f"- 退款#{rid}: {product_name} [{s}]")
    return "\n".join(summary_parts)


@tool
async def get_refund_detail(refund_id: int) -> str:
    """获取退款申请详情。传入退款申请ID。"""
    if not _is_authenticated():
        return "用户未登录，无法查询退款详情。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_refund_detail(refund_id, token=token)
    except Exception as exc:
        logger.error("获取退款详情失败: %s", exc)
        return f"获取退款详情时出错: {exc}"

    code = result.get("code")
    data = result.get("data")

    if code != 200 or not data:
        return f"未找到退款申请 (ID: {refund_id})"

    tool_result_store.store("get_refund_detail", data)

    status_map = {0: "待处理", 1: "退货中", 2: "已完成", 3: "已拒绝"}
    product_name = data.get("productName", "?")
    s = status_map.get(data.get("status", -1), "未知")
    reason = data.get("reason", "?")
    return f"退款#{refund_id}: {product_name}\n状态: {s}\n原因: {reason}"


# ── 地址工具 ──────────────────────────────────────────


@tool
async def get_addresses() -> str:
    """获取用户收货地址列表。"""
    if not _is_authenticated():
        return "用户未登录，无法查询地址。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_addresses(token=token)
    except Exception as exc:
        logger.error("查询地址失败: %s", exc)
        return f"查询地址时出错: {exc}"

    code = result.get("code")
    data = result.get("data", [])
    addresses = data if isinstance(data, list) else []

    if code != 200 or not addresses:
        return "您暂无收货地址"

    tool_result_store.store("get_addresses", addresses)

    # UmsMemberReceiveAddress 字段: name, phoneNumber, detailAddress, defaultStatus, province, city, region
    summary_parts = [f"您有 {len(addresses)} 个收货地址:"]
    for a in addresses[:5]:
        name = a.get("name", "?")
        phone = a.get("phoneNumber", "?")
        addr = a.get("detailAddress", "?")
        province = a.get("province", "")
        city = a.get("city", "")
        region = a.get("region", "")
        full_addr = f"{province}{city}{region}{addr}"
        default_tag = " [默认]" if a.get("defaultStatus") == 1 else ""
        summary_parts.append(f"- {name} {phone}: {full_addr}{default_tag}")
    return "\n".join(summary_parts)


@tool
async def update_address(address_id: int, name: str, phone: str, address: str) -> str:
    """更新收货地址。需要提供地址ID、收件人姓名、手机号、详细地址。"""
    if not _is_authenticated():
        return "用户未登录，无法修改地址。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.update_address(
            address_id,
            {"name": name, "phoneNumber": phone, "detailAddress": address},
            token=token,
        )
    except Exception as exc:
        logger.error("更新地址失败: %s", exc)
        return f"更新地址时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "更新失败")
        return f"地址更新失败: {msg}"

    return f"地址已更新: {name} {phone} {address}"


@tool
async def create_address(name: str, phone: str, address: str) -> str:
    """新增收货地址。需要提供收件人姓名、手机号、详细地址。"""
    if not _is_authenticated():
        return "用户未登录，无法新增地址。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.create_address(
            {"name": name, "phoneNumber": phone, "detailAddress": address, "defaultStatus": 0},
            token=token,
        )
    except Exception as exc:
        logger.error("新增地址失败: %s", exc)
        return f"新增地址时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "新增失败")
        return f"地址新增失败: {msg}"

    return f"地址已新增: {name} {phone} {address}"


@tool
async def get_address(address_id: int) -> str:
    """获取单个收货地址详情。传入地址ID。"""
    if not _is_authenticated():
        return "用户未登录，无法查询地址。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_address(address_id, token=token)
    except Exception as exc:
        logger.error("获取地址详情失败: %s", exc)
        return f"获取地址详情时出错: {exc}"

    code = result.get("code")
    data = result.get("data")

    if code != 200 or not data:
        return f"未找到地址 (ID: {address_id})"

    tool_result_store.store("get_address", data)

    name = data.get("name", "?")
    phone = data.get("phoneNumber", "?")
    addr = data.get("detailAddress", "?")
    province = data.get("province", "")
    city = data.get("city", "")
    region = data.get("region", "")
    full_addr = f"{province}{city}{region}{addr}"
    default_tag = " [默认]" if data.get("defaultStatus") == 1 else ""
    return f"{name} {phone}: {full_addr}{default_tag}"


@tool
async def delete_address(address_id: int) -> str:
    """删除收货地址。传入地址ID。"""
    if not _is_authenticated():
        return "用户未登录，无法删除地址。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.delete_address(address_id, token=token)
    except Exception as exc:
        logger.error("删除地址失败: %s", exc)
        return f"删除地址时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "删除失败")
        return f"地址删除失败: {msg}"

    return f"地址 (ID: {address_id}) 已删除。"


# ── 购物车工具 ──────────────────────────────────────────


@tool
async def get_cart_list() -> str:
    """查询当前用户的购物车列表，返回购物车中的商品信息。"""
    if not _is_authenticated():
        return "用户未登录，无法查询购物车。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_cart_list(token=token)
    except Exception as exc:
        logger.error("查询购物车失败: %s", exc)
        return f"查询购物车时出错: {exc}"

    code = result.get("code")
    data = result.get("data", [])
    items = data if isinstance(data, list) else []

    if code != 200 or not items:
        return "您的购物车是空的"

    tool_result_store.store("get_cart_list", items)

    summary_parts = [f"购物车中有 {len(items)} 件商品:"]
    for i, item in enumerate(items[:8], 1):
        name = item.get("productName", "未知")
        price = item.get("price", "?")
        quantity = item.get("quantity", 1)
        summary_parts.append(f"{i}. {name} × {quantity} (¥{price})")
    return "\n".join(summary_parts)


@tool
async def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """添加商品到购物车。需要商品ID和数量。"""
    if not _is_authenticated():
        return "用户未登录，无法添加到购物车。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.add_to_cart(product_id, quantity, token=token)
    except Exception as exc:
        logger.error("添加到购物车失败: %s", exc)
        return f"添加到购物车时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "添加失败")
        return f"添加到购物车失败: {msg}"

    return f"已将 {quantity} 件商品 (ID: {product_id}) 添加到购物车。"


# ── 用户工具 ──────────────────────────────────────────


@tool
async def get_user_profile() -> str:
    """获取当前登录用户的基础信息，包括昵称、手机号、积分等。"""
    if not _is_authenticated():
        return "用户未登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_user_profile(token=token)
    except Exception as exc:
        logger.error("获取用户信息失败: %s", exc)
        return f"获取用户信息时出错: {exc}"

    code = result.get("code")
    data = result.get("data")

    if code != 200 or not data:
        return "获取用户信息失败"

    tool_result_store.store("get_user_profile", data)

    # UmsMember 字段: username, nickname, phone, integration, growth, memberLevelId
    nickname = data.get("nickname") or data.get("username", "?")
    phone = data.get("phone", "未绑定")
    integration = data.get("integration", 0)
    growth = data.get("growth", 0)
    return f"用户: {nickname}\n手机: {phone}\n积分: {integration}\n成长值: {growth}"


@tool
async def get_coupons() -> str:
    """获取用户可用优惠券列表。"""
    if not _is_authenticated():
        return "用户未登录，无法查询优惠券。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.get_coupons(token=token)
    except Exception as exc:
        logger.error("查询优惠券失败: %s", exc)
        return f"查询优惠券时出错: {exc}"

    code = result.get("code")
    # /member/coupon/list 直接返回 List<SmsCoupon>
    data = result.get("data", [])
    coupons = data if isinstance(data, list) else []

    if code != 200 or not coupons:
        return "您暂无可用优惠券"

    tool_result_store.store("get_coupons", coupons)

    # SmsCoupon 字段: name, amount, minPoint, type, startTime, endTime
    summary_parts = [f"您有 {len(coupons)} 张优惠券:"]
    for c in coupons[:5]:
        name = c.get("name", "?")
        amount = c.get("amount", "?")
        min_point = c.get("minPoint", 0)
        summary_parts.append(f"- {name}: 满{min_point}减{amount}")
    return "\n".join(summary_parts)


# ── 评价工具 ──────────────────────────────────────────


@tool
async def check_unreviewed_products() -> str:
    """查询当前用户已确认收货但还未评价的商品列表。

    返回所有已完成(status=3)但没有评价(commentTime为空)的订单及其商品信息。
    用户问"哪些商品还没评价"、"查看未评价订单"时调用此工具。
    """
    if not _is_authenticated():
        return "用户未登录，无法查询。请先登录。"

    adapter = get_mall_adapter()
    token = _get_token()

    try:
        # 查询已完成的订单 (status=3)
        result = await adapter.get_user_orders(status=3, token=token)
    except Exception as exc:
        logger.error("查询已完成订单失败: %s", exc)
        return f"查询订单时出错: {exc}"

    code = result.get("code")
    data = result.get("data", {})
    orders = data.get("list", []) if isinstance(data, dict) else []

    if code != 200 or not orders:
        return "您没有已完成的订单。"

    # 筛选未评价的订单（commentTime 为空）
    unreviewed = []
    for o in orders:
        comment_time = o.get("commentTime")
        if not comment_time:
            items = o.get("orderItemList", [])
            unreviewed.append({
                "order_id": o.get("id"),
                "order_sn": o.get("orderSn"),
                "total_amount": o.get("totalAmount"),
                "pay_amount": o.get("payAmount"),
                "items": [
                    {
                        "item_id": i.get("id"),
                        "product_id": i.get("productId"),
                        "product_name": i.get("productName"),
                        "product_pic": i.get("productPic"),
                        "product_price": i.get("productPrice"),
                        "product_attr": i.get("productAttr"),
                    }
                    for i in items
                ],
            })

    if not unreviewed:
        return "您所有已完成的订单都已经评价过了，没有待评价的商品。"

    # 暂存完整数据给前端卡片渲染
    tool_result_store.store("check_unreviewed_products", unreviewed)

    summary_parts = [f"您有 {len(unreviewed)} 个订单的商品尚未评价:"]
    for u in unreviewed:
        oid = u["order_id"]
        order_sn = u["order_sn"]
        for item in u["items"]:
            name = item["product_name"]
            price = item["product_price"]
            attr = item.get("product_attr", "")
            attr_str = f" ({attr})" if attr else ""
            summary_parts.append(
                f"- 订单{order_sn} | {name}{attr_str} ¥{price} "
                f"[order_id={oid}, item_id={item['item_id']}, product_id={item['product_id']}]"
            )
    summary_parts.append("\n如需评价，请告诉我要评价哪个商品，给几星。")
    return "\n".join(summary_parts)


@tool
async def create_review(
    order_id: int,
    order_item_id: int,
    product_id: int,
    star: int,
    content: str,
) -> str:
    """提交商品评价。需要提供订单ID、订单项ID、商品ID、星级(1~5)和评价内容。

    调用前必须先通过 get_user_orders 或 get_order_detail 获取正确的 order_item_id 和 product_id。
    """
    if not _is_authenticated():
        return "用户未登录，无法提交评价。请先登录。"

    # 校验星级范围
    if star < 1 or star > 5:
        return "星级必须在 1~5 之间，请重新填写。"

    # 如果用户未提供内容，使用星级对应的默认内容
    if not content or not content.strip():
        from app.config.constants import ReviewDefaults
        content = ReviewDefaults.STAR_CONTENT_MAP.get(star, ReviewDefaults.DEFAULT_CONTENT)

    adapter = get_mall_adapter()
    token = _get_token()
    try:
        result = await adapter.create_review(
            order_id=order_id,
            order_item_id=order_item_id,
            product_id=product_id,
            star=star,
            content=content.strip(),
            token=token,
        )
    except Exception as exc:
        logger.error("提交评价失败: %s", exc)
        return f"提交评价时出错: {exc}"

    code = result.get("code")
    if code != 200:
        msg = result.get("message", "评价失败")
        return f"评价提交失败: {msg}"

    tool_result_store.store("create_review", {
        "order_id": order_id,
        "order_item_id": order_item_id,
        "product_id": product_id,
        "star": star,
        "content": content.strip(),
    })
    return f"评价提交成功！{star} 星 | 内容: {content.strip()}"


# ── 工具执行映射（用于确认后直接执行）─────────────────────

# 工具名 → 原始函数的映射（在模块加载时构建）
_TOOL_REGISTRY: dict[str, Any] = {}


def _register_tool(fn):
    """注册工具到全局注册表。"""
    _TOOL_REGISTRY[fn.name if hasattr(fn, 'name') else fn.__name__] = fn
    return fn


async def execute_confirmed_tool(tool_name: str, params: dict[str, Any], token: str | None = None) -> str:
    """确认后执行破坏性工具。由 /chat/action/confirm 端点调用。

    Args:
        tool_name: 工具名称
        params: 工具参数
        token: 用户 JWT token（用于设置请求上下文）

    Returns:
        工具执行结果的文本摘要
    """
    fn = _TOOL_REGISTRY.get(tool_name)
    if not fn:
        return f"未知工具: {tool_name}"

    # 如果传入了 token，更新请求上下文
    if token:
        set_request_context(token=token)

    # 获取原始工具函数（如果是 wrapped 版本，取 _original_tool）
    original_fn = getattr(fn, '_original_tool', fn)

    # 字段名别名映射：LLM 常用的字段名 → Pydantic schema 实际字段名
    _FIELD_ALIASES: dict[str, str] = {
        "rating": "star",
        "item_id": "order_item_id",
        "review_content": "content",
        "review_star": "star",
        "score": "star",
    }
    for alias, actual in _FIELD_ALIASES.items():
        if alias in params and actual not in params:
            params[actual] = params.pop(alias)

    try:
        # LangChain @tool 包装的函数需要通过 .invoke() 调用
        if hasattr(original_fn, 'invoke'):
            result = await original_fn.ainvoke(params)
        else:
            result = await original_fn(**params)
        return result
    except Exception as exc:
        logger.error("确认执行工具失败 | tool=%s params=%s error=%s", tool_name, params, exc)
        return f"操作执行失败: {exc}"


# ── 工具分组 ──────────────────────────────────────────

# 只读工具（直接执行）
PRODUCT_TOOLS = [search_products, get_product_info, get_recommendations, get_hot_products, get_new_products]
READ_ONLY_ORDER_TOOLS = [get_user_orders, get_order_detail, get_logistics, get_refund_list, get_refund_detail, check_unreviewed_products]
READ_ONLY_ADDRESS_TOOLS = [get_addresses, get_address]
READ_ONLY_CART_TOOLS = [get_cart_list]
USER_TOOLS = [get_user_profile, get_coupons]

# 破坏性工具（原始函数，用于注册表）
_DESTRUCTIVE_ORDER_TOOLS = [cancel_order, confirm_receive, mark_delivered, delete_order, apply_refund, create_review]
_DESTRUCTIVE_ADDRESS_TOOLS = [update_address, create_address, delete_address]
_DESTRUCTIVE_CART_TOOLS = [add_to_cart]

# 注册所有工具到全局注册表
for _t in PRODUCT_TOOLS + READ_ONLY_ORDER_TOOLS + _DESTRUCTIVE_ORDER_TOOLS + READ_ONLY_ADDRESS_TOOLS + _DESTRUCTIVE_ADDRESS_TOOLS + READ_ONLY_CART_TOOLS + _DESTRUCTIVE_CART_TOOLS + USER_TOOLS:
    _register_tool(_t)

# 包装破坏性工具
_wrapped_order_tools = [_wrap_destructive(t) for t in _DESTRUCTIVE_ORDER_TOOLS]
_wrapped_address_tools = [_wrap_destructive(t) for t in _DESTRUCTIVE_ADDRESS_TOOLS]
_wrapped_cart_tools = [_wrap_destructive(t) for t in _DESTRUCTIVE_CART_TOOLS]

# 合并工具组（Agent 绑定用）
ORDER_TOOLS = READ_ONLY_ORDER_TOOLS + _wrapped_order_tools
ADDRESS_TOOLS = READ_ONLY_ADDRESS_TOOLS + _wrapped_address_tools
CART_TOOLS = READ_ONLY_CART_TOOLS + _wrapped_cart_tools

# 所有工具（用于调试或全量绑定）
ALL_TOOLS = PRODUCT_TOOLS + ORDER_TOOLS + ADDRESS_TOOLS + CART_TOOLS + USER_TOOLS
