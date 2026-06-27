"""Pydantic 请求/响应模型。"""

from pydantic import BaseModel, Field


# ── 聊天 ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    """前端发来的聊天消息。用户身份通过 JWT token 在请求头中传递。"""

    message: str = Field(..., min_length=1, max_length=10000, description="用户消息文本")
    session_id: str = Field(..., min_length=1, description="客户端生成的会话 UUID")


# ── 响应卡片 ──────────────────────────────────────────


class ProductCard(BaseModel):
    """前端渲染的商品卡片。"""

    id: int
    name: str
    price: float
    original_price: float | None = None
    image: str | None = None
    rating: float | None = None
    reason: str | None = Field(None, description="推荐理由")


class OrderCard(BaseModel):
    """前端渲染的订单卡片。"""

    order_id: int
    order_sn: str
    product_name: str
    product_image: str | None = None
    total_amount: float
    status: int
    status_text: str
    create_time: str | None = None


class LogisticsCard(BaseModel):
    """前端渲染的物流卡片。"""

    order_id: int
    logistics_company: str
    tracking_number: str
    current_status: str
    latest_update: str | None = None
    timeline: list[dict] = Field(default_factory=list)


class AddressCard(BaseModel):
    """前端渲染的地址卡片。"""

    id: int
    name: str
    phone: str
    address: str
    is_default: bool = False


class CartItemCard(BaseModel):
    """前端渲染的购物车商品卡片。"""

    id: int
    product_id: int
    product_name: str
    product_image: str | None = None
    price: float = 0
    quantity: int = 1
    checked: bool = True


class ActionItem(BaseModel):
    """可操作按钮 — 前端渲染为可点击的操作。"""

    type: str  # "view_product" | "view_order" | "apply_refund" | "view_logistics" | "view_address"
    label: str  # 按钮文字
    params: dict = Field(default_factory=dict)  # 跳转参数


class ReviewCard(BaseModel):
    """前端渲染的评价卡片。"""

    order_id: int
    order_item_id: int
    product_id: int
    star: int
    content: str


class ChatResponse(BaseModel):
    """返回给前端的响应 — 包含文本回复和结构化卡片数据。"""

    reply: str = Field(..., description="Agent 回复文本")
    intent: str | None = Field(None, description="分类的意图类型")

    # 结构化卡片数据
    products: list[ProductCard] = Field(default_factory=list, description="商品卡片列表")
    orders: list[OrderCard] = Field(default_factory=list, description="订单卡片列表")
    logistics: LogisticsCard | None = Field(None, description="物流卡片")
    addresses: list[AddressCard] = Field(default_factory=list, description="地址卡片列表")
    cart_items: list[CartItemCard] = Field(default_factory=list, description="购物车商品卡片列表")
    reviews: list[ReviewCard] = Field(default_factory=list, description="评价卡片列表")
    actions: list[ActionItem] = Field(default_factory=list, description="可操作按钮列表")
    sources: list[dict] = Field(default_factory=list, description="RAG 来源文档")

    # 兼容旧字段
    recommended_products: list[ProductCard] = Field(default_factory=list, description="推荐商品（兼容）")


# ── 破坏性操作确认 ──────────────────────────────────────


class PendingAction(BaseModel):
    """待用户确认的破坏性操作。"""

    action_id: str = Field(..., description="操作唯一 ID")
    tool_name: str = Field(..., description="工具名称")
    description: str = Field(..., description="人类可读的操作描述")
    params: dict = Field(default_factory=dict, description="工具调用参数")
    created_at: float = Field(..., description="创建时间戳")


class ConfirmActionRequest(BaseModel):
    """用户确认执行操作的请求。"""

    action_id: str = Field(..., min_length=1, description="待确认操作的 ID")


class ConfirmActionResponse(BaseModel):
    """确认执行后的响应。"""

    success: bool = Field(..., description="是否执行成功")
    message: str = Field(..., description="执行结果消息")
    tool_name: str = Field("", description="执行的工具名")
    tool_result: dict | None = Field(None, description="工具返回的结构化数据")


class UpdatePendingActionRequest(BaseModel):
    """更新待确认操作状态的请求（前端确认后持久化状态用）。"""

    session_id: str = Field(..., min_length=1, description="会话 ID")
    action_id: str = Field(..., min_length=1, description="待确认操作的 ID")
    status: str = Field(..., description="确认状态：confirmed / cancelled / error")
    result_message: str = Field("", description="执行结果消息")


# ── 健康检查 ─────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
