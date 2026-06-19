"""Mall HTTP 适配层 — 封装所有对 Java mall 后端的 HTTP 调用。

所有方法返回 dict，格式为 Java CommonResult { code, message, data }。
分页接口 data 格式为 CommonPage { pageNum, pageSize, totalPage, total, list }。
调用方应检查 code == 200 后再使用 data。
"""

import logging
from typing import Any

import httpx

from app.config.settings import get_settings
from app.core.exceptions import MallAPIException

logger = logging.getLogger(__name__)


class MallAdapter:
    """封装所有对 Java mall 后端的 HTTP 调用。

    路径与 Java Controller 的 @RequestMapping 对齐（不含 /api 前缀）。
    """

    def __init__(self, base_url: str) -> None:
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=10.0,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        await self.client.aclose()

    # ── 通用请求 ──────────────────────────────────────

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict:
        """发送 GET 请求。"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = await self.client.get(path, params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(
                    "Mall API GET 失败 | path=%s status=%d body=%s",
                    path, resp.status_code, resp.text[:500],
                )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise MallAPIException(
                f"GET {path} failed: {exc.response.status_code} body={exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Mall API 请求异常 | path=%s error=%s", path, exc)
            raise MallAPIException(f"GET {path} request error: {exc}") from exc

    async def _post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict:
        """发送 POST 请求。"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = await self.client.post(path, json=json_data, params=params, headers=headers)
            if resp.status_code >= 400:
                # 打印 Java 返回的错误详情（关键调试信息）
                logger.error(
                    "Mall API POST 失败 | path=%s status=%d body=%s params=%s",
                    path, resp.status_code, resp.text[:500], params,
                )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise MallAPIException(
                f"POST {path} failed: {exc.response.status_code} body={exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Mall API 请求异常 | path=%s error=%s", path, exc)
            raise MallAPIException(f"POST {path} request error: {exc}") from exc

    # ── 商品相关 ──────────────────────────────────────
    # Controller: PmsPortalProductController (/product)
    # 白名单，不需要认证

    async def search_products(
        self,
        keyword: str,
        category_id: int | None = None,
        brand_id: int | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        sort: int = 0,
        page_num: int = 0,
        page_size: int = 5,
    ) -> dict:
        """搜索商品（DB 搜索）。

        sort: 0=综合 1=新品 2=销量 3=价格升序 4=价格降序
        注意：Java 默认 pageNum 从 0 开始
        """
        params: dict[str, Any] = {
            "keyword": keyword,
            "pageNum": page_num,
            "pageSize": page_size,
            "sort": sort,
        }
        if category_id is not None:
            params["productCategoryId"] = category_id
        if brand_id is not None:
            params["brandId"] = brand_id
        return await self._get("/product/search", params=params)

    async def get_product_info(self, product_id: int) -> dict:
        """获取商品详情。

        返回 CommonResult<PmsPortalProductDetail>，
        data 中包含 product(商品基础信息)、brand、skuStockList 等。
        """
        return await self._get(f"/product/detail/{product_id}")

    async def get_recommendations(self, limit: int = 6) -> dict:
        """获取推荐商品（首页推荐）。白名单接口。"""
        params: dict[str, Any] = {"pageSize": limit, "pageNum": 1}
        return await self._get("/home/recommendProductList", params=params)

    async def get_hot_products(self, page_num: int = 1, page_size: int = 6) -> dict:
        """获取热门商品。白名单接口。"""
        return await self._get("/home/hotProductList", params={"pageNum": page_num, "pageSize": page_size})

    async def get_new_products(self, page_num: int = 1, page_size: int = 6) -> dict:
        """获取新品。白名单接口。"""
        return await self._get("/home/newProductList", params={"pageNum": page_num, "pageSize": page_size})

    # ── 订单相关 ──────────────────────────────────────
    # Controller: OmsPortalOrderController (/order)
    # 需要认证

    async def get_user_orders(
        self,
        status: int = -1,
        page_num: int = 1,
        page_size: int = 5,
        token: str | None = None,
    ) -> dict:
        """获取用户订单列表。

        status: -1=全部 0=待付款 1=待发货 2=已发货 3=已完成 4=已关闭 5=退货 6=已评价
        """
        params: dict[str, Any] = {
            "status": status,
            "pageNum": page_num,
            "pageSize": page_size,
        }
        return await self._get("/order/list", params=params, token=token)

    async def get_order_detail(self, order_id: int, token: str | None = None) -> dict:
        """获取订单详情（含 orderItemList）。"""
        return await self._get(f"/order/detail/{order_id}", token=token)

    async def get_logistics(self, order_id: int, token: str | None = None) -> dict:
        """查询订单物流信息。

        返回 LogisticsDetailResult:
        - deliveryCompany, deliverySn, deliveryTime
        - receiverName, receiverPhone, receiverAddress
        - traceList: [{traceTime, location, statusText, statusCode}]
        """
        return await self._get(f"/order/logistics/{order_id}", token=token)

    async def cancel_order(self, order_id: int, token: str | None = None) -> dict:
        """取消订单。"""
        return await self._post("/order/cancelUserOrder", params={"orderId": order_id}, token=token)

    async def confirm_receive(self, order_id: int, token: str | None = None) -> dict:
        """确认收货（已发货/已送达 → 已完成）。"""
        return await self._post("/order/confirmReceiveOrder", params={"orderId": order_id}, token=token)

    async def mark_delivered(self, order_id: int, token: str | None = None) -> dict:
        """标记订单为已送达（已发货 → 已送达）。"""
        return await self._post("/order/markDelivered", params={"orderId": order_id}, token=token)

    async def delete_order(self, order_id: int, token: str | None = None) -> dict:
        """删除订单。"""
        return await self._post("/order/deleteOrder", params={"orderId": order_id}, token=token)

    # ── 退款/退货相关 ─────────────────────────────────
    # Controller: OmsPortalOrderReturnApplyController (/returnApply)
    # 需要认证

    async def apply_refund(
        self,
        order_id: int,
        product_id: int,
        reason: str,
        member_username: str = "",
        token: str | None = None,
    ) -> dict:
        """申请退货退款。

        需要提供 orderId、productId、reason。
        """
        data = {
            "orderId": order_id,
            "productId": product_id,
            "reason": reason,
            "memberUsername": member_username,
        }
        return await self._post("/returnApply/create", json_data=data, token=token)

    async def get_refund_list(self, member_username: str, token: str | None = None) -> dict:
        """查询退货申请列表。"""
        return await self._get("/returnApply/list", params={"memberUsername": member_username}, token=token)

    async def get_refund_detail(self, refund_id: int, token: str | None = None) -> dict:
        """查询退货申请详情。"""
        return await self._get(f"/returnApply/{refund_id}", token=token)

    # ── 用户相关 ──────────────────────────────────────
    # Controller: UmsMemberController (/sso)
    # /sso/info 需要认证

    async def get_user_profile(self, token: str | None = None) -> dict:
        """获取当前登录用户信息。JWT token 已包含用户身份，Java 后端通过 SecurityContextHolder 识别。"""
        return await self._get("/sso/info", token=token)

    # ── 地址相关 ──────────────────────────────────────
    # Controller: UmsMemberReceiveAddressController (/member/address)
    # 需要认证

    async def get_addresses(self, token: str | None = None) -> dict:
        """获取用户收货地址列表。JWT token 已包含用户身份。"""
        return await self._get("/member/address/list", token=token)

    async def get_address(self, address_id: int, token: str | None = None) -> dict:
        """获取单个收货地址。"""
        return await self._get(f"/member/address/{address_id}", token=token)

    async def create_address(
        self, data: dict[str, Any], token: str | None = None
    ) -> dict:
        """新增收货地址。

        data 字段: name, phoneNumber, detailAddress, province, city, region, postCode, defaultStatus
        """
        return await self._post("/member/address/add", json_data=data, token=token)

    async def update_address(
        self, address_id: int, data: dict[str, Any], token: str | None = None
    ) -> dict:
        """更新收货地址。"""
        return await self._post(
            f"/member/address/update/{address_id}",
            json_data=data,
            token=token,
        )

    async def delete_address(self, address_id: int, token: str | None = None) -> dict:
        """删除收货地址。"""
        return await self._post(f"/member/address/delete/{address_id}", token=token)

    # ── 优惠券相关 ────────────────────────────────────
    # Controller: UmsMemberCouponController (/member/coupon)
    # 需要认证

    async def get_coupons(
        self, use_status: int | None = None, token: str | None = None
    ) -> dict:
        """获取用户优惠券列表。JWT token 已包含用户身份。

        use_status: 0=未使用 1=已使用 2=已过期
        """
        params = {}
        if use_status is not None:
            params["useStatus"] = use_status
        return await self._get("/member/coupon/list", params=params, token=token)

    # ── 购物车相关 ────────────────────────────────────
    # Controller: OmsCartItemController (/cart)
    # 需要认证

    async def get_cart_list(self, token: str | None = None) -> dict:
        """获取购物车列表。"""
        return await self._get("/cart/list", token=token)

    async def add_to_cart(
        self, product_id: int, quantity: int = 1, token: str | None = None
    ) -> dict:
        """添加到购物车。"""
        return await self._post(
            "/cart/add",
            json_data={"productId": product_id, "quantity": quantity},
            token=token,
        )


    # ── 评价相关 ────────────────────────────────────────
    # Controller: PmsCommentController (/comment)
    # 需要认证

    async def create_review(
        self,
        order_id: int,
        order_item_id: int,
        product_id: int,
        star: int,
        content: str,
        token: str | None = None,
    ) -> dict:
        """创建商品评价。

        POST /comment/create，@RequestBody PmsCommentParam。
        star: 0~5（0 表示 5 星，1~5 直接对应星级）
        """
        data = {
            "orderId": order_id,
            "orderItemId": order_item_id,
            "productId": product_id,
            "star": star,
            "content": content,
        }
        return await self._post("/comment/create", json_data=data, token=token)


# 模块级单例（由 main.py lifespan 初始化）
_mall_adapter: MallAdapter | None = None


def get_mall_adapter() -> MallAdapter:
    """获取全局 MallAdapter 实例。"""
    if _mall_adapter is None:
        settings = get_settings()
        return MallAdapter(settings.mall_portal_url)
    return _mall_adapter


def init_mall_adapter(base_url: str) -> MallAdapter:
    """初始化全局 MallAdapter（在应用启动时调用）。"""
    global _mall_adapter
    _mall_adapter = MallAdapter(base_url)
    return _mall_adapter
