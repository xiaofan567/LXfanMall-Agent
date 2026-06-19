"""聊天 API 端点 — AI Agent 的主要交互接口。

支持两种模式：
- POST /chat       — 一次性返回完整响应
- POST /chat/stream — SSE 流式逐 token 返回

路由策略：
1. 规则路由优先（零 Token），命中则直接调用对应 Agent
2. 未命中则走 LLM 意图分类，再路由到对应 Agent
3. RAG 场景走轻量 LCEL 链（Phase 2 实现）
"""

import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from app.agent.graph import build_agent_graph
from app.agent.nodes import (
    address_agent_node,
    cart_agent_node,
    chitchat_node,
    order_agent_node,
    product_agent_node,
)
from app.agent.router import rule_router
from app.agent.session import session_store
from app.agent.token_callback import TokenUsageCallback
from app.agent.token_reporter import report_token_usage_async
from app.agent.tool_result import set_current_request_id, tool_result_store
from app.agent.tools import execute_confirmed_tool, pending_action_store, sanitize_input, set_request_context
from app.api.v1.deps import CurrentUser, get_optional_user
from app.config.constants import IntentType
from app.core.exceptions import AgentException, agent_exception_to_http
from app.core.limiter import limiter
from app.memory.user_profile import user_profile_store
from app.models.schemas import (
    ActionItem,
    AddressCard,
    CartItemCard,
    ChatRequest,
    ChatResponse,
    ConfirmActionRequest,
    ConfirmActionResponse,
    LogisticsCard,
    OrderCard,
    ProductCard,
    ReviewCard,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ── 会话管理接口 ────────────────────────────────────

@router.get("/latest-session")
async def get_latest_session(
    user: CurrentUser | None = Depends(get_optional_user),
):
    """获取当前用户最近活跃的 session_id（登录用户专属）。

    Returns:
        {"code": 200, "data": {"session_id": "uuid" | null}}
    """
    if not user:
        return {"code": 200, "data": {"session_id": None}}
    session_id = await session_store.get_latest_session_id(user.username)
    return {"code": 200, "data": {"session_id": session_id}}


@router.get("/history")
async def get_chat_history(
    session_id: str,
    user: CurrentUser | None = Depends(get_optional_user),
):
    """获取指定会话的对话历史（用于前端刷新后恢复）。"""
    username = user.username if user else "anonymous"
    history = await session_store.get_raw_history_dicts(username, session_id)
    return {"code": 200, "data": history}


@router.delete("/history")
async def clear_chat_history(
    session_id: str,
    user: CurrentUser | None = Depends(get_optional_user),
):
    """清空指定会话的对话历史。"""
    username = user.username if user else "anonymous"
    await session_store.clear(username, session_id)
    return {"code": 200, "message": "对话记录已清除"}

# 编译后的图 — 跨请求复用（用于 LLM 意图分类路径）
_agent_graph = build_agent_graph()

# 路由目标 → 意图映射
_ROUTE_TO_INTENT = {
    "product": IntentType.PRODUCT_RECOMMEND,
    "order": IntentType.ORDER_QUERY,
    "address": IntentType.ADDRESS_MANAGE,
    "cart": IntentType.CART_QUERY,
    "chitchat": IntentType.CHITCHAT,
}

# 意图 → Agent 节点函数映射
_INTENT_TO_NODE = {
    IntentType.PRODUCT_RECOMMEND: product_agent_node,
    IntentType.ORDER_QUERY: order_agent_node,
    IntentType.CUSTOMER_SERVICE: order_agent_node,
    IntentType.ADDRESS_MANAGE: address_agent_node,
    IntentType.CART_QUERY: cart_agent_node,
    IntentType.CHITCHAT: chitchat_node,
}


# 非流式端点已暂时禁用，只保留流式 /stream 端点，避免 Agent 被执行两次
# @router.post("", response_model=ChatResponse)
# async def chat(
#     request: ChatRequest,
#     req: Request,
#     user: CurrentUser | None = Depends(get_optional_user),
# ) -> ChatResponse:
#     """向 AI Agent 发送消息并接收完整响应（非流式）。"""
#     try:
#         request_id = str(uuid.uuid4())
#         set_current_request_id(request_id)
#         token = user.token if user else _extract_token(req)
#         set_request_context(token=token, member_username=user.username if user else "")
#
#         session_id = request.session_id
#         user_msg = HumanMessage(content=request.message)
#
#         # 获取历史 + 当前用户消息
#         history = session_store.get_history(session_id)
#         messages = history + [user_msg]
#
#         # ── 规则路由 ──
#         route = rule_router.route(request.message)
#         intent = None
#
#         if route.confidence >= 0.7:
#             # 规则命中（order/product/address）— 直接执行对应 Agent
#             intent = _ROUTE_TO_INTENT.get(route.target, IntentType.CHITCHAT)
#             logger.info("规则路由命中 | target=%s → intent=%s", route.target, intent)
#             node_fn = _INTENT_TO_NODE.get(intent, chitchat_node)
#             state = {"messages": messages, "intent": intent}
#             node_result = await node_fn(state)
#             result = {
#                 "messages": node_result.get("messages", []),
#                 "intent": intent,
#             }
#         else:
#             # 规则未命中 → 交给图：LLM 意图分类 → RAG 或 Agent
#             logger.info("规则路由未命中，走 LLM 意图分类")
#             result = await _agent_graph.ainvoke({
#                 "messages": messages,
#                 "intent": "",
#             })
#
#         reply = _extract_reply(result["messages"])
#
#         # 持久化本轮对话
#         session_store.add_message(session_id, user_msg)
#         session_store.add_message(session_id, AIMessage(content=reply))
#
#         # 构建结构化响应
#         response = _build_structured_response(
#             reply=reply,
#             intent=result.get("intent", intent or "unknown"),
#             request_id=request_id,
#         )
#
#         logger.info(
#             "聊天完成 | session=%s user=%s intent=%s route=%s",
#             session_id, user.username if user else "anonymous", response.intent, route.target,
#         )
#
#         return response
#
#     except AgentException as exc:
#         raise agent_exception_to_http(exc)
#     except Exception as exc:
#         logger.exception("聊天端点发生意外错误")
#         raise agent_exception_to_http(
#             AgentException(code=500, message="Internal server error")
#         )


@router.post("/stream")
@limiter.limit("20/minute")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    user: CurrentUser | None = Depends(get_optional_user),
):
    """SSE 流式端点 — 逐 token 推送 AI 回复。"""
    # 输入消毒：检测 prompt 注入
    if not sanitize_input(body.message):
        import random
        redirect_replies = [
            "抱歉，我是 LXfanMall 的智能助手小L，只能帮您处理商城相关的购物问题哦～有什么商品或订单需要帮忙的吗？",
            "不好意思，我专注于帮您处理购物、订单、商品等方面的问题，其他内容我可能帮不上忙。您可以问我关于商品推荐、订单查询等问题～",
            "我是商城助手小L，我的能力范围是商品搜索、订单管理、地址管理等购物相关服务。请问有什么可以帮您的？",
            "抱歉没太理解您的意思，我是 LXfanMall 的购物助手，可以帮您查商品、查订单、管理地址等。您有什么购物方面的需求吗？",
        ]
        block_msg = random.choice(redirect_replies)

        async def blocked_generator():
            yield f"data: {json.dumps({'token': block_msg}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'reply': block_msg}, ensure_ascii=False)}\n\n"
        return StreamingResponse(
            blocked_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # 未登录用户无法使用 Agent
    if not user:
        login_msg = "请先登录后再使用 AI 助手功能～"

        async def login_required_generator():
            yield f"data: {json.dumps({'token': login_msg}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True, 'reply': login_msg}, ensure_ascii=False)}\n\n"
        return StreamingResponse(
            login_required_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        request_id = str(uuid.uuid4())
        set_current_request_id(request_id)
        token = user.token
        set_request_context(token=token, member_username=user.username)

        session_id = body.session_id
        user_msg = HumanMessage(content=body.message)
        username = user.username if user else "anonymous"
        logger.info("chat_stream | user=%s session_id=%s", username, session_id)

        # Token 用量采集
        token_callback = TokenUsageCallback()
        request_start_time = time.time()

        history = await session_store.get_history(username, session_id)
        messages = history + [user_msg]

        # 路由决策
        route = rule_router.route(body.message)

        # 流式输出的节点名（叶子 Agent + RAG 节点）
        _STREAM_NODES = ("rag_engine", "product_agent", "order_agent", "address_agent", "cart_agent", "chitchat")

        async def event_generator():
            full_reply = ""
            _seen_final_reply = ""  # 保险：捕获节点返回的完整 AIMessage 作为兜底
            _intent = IntentType.CHITCHAT  # 默认意图，路由命中后会更新

            if route.confidence >= 0.7:
                # 规则路由命中（order/product/address）— 直接执行对应 Agent
                _intent = _ROUTE_TO_INTENT.get(route.target, IntentType.CHITCHAT)
                graph_input = {"messages": messages, "intent": _intent}
                async for chunk in _agent_graph.astream(
                    graph_input, stream_mode="messages", version="v2",
                    config={"callbacks": [token_callback]},
                ):
                    if chunk["type"] == "messages":
                        msg, metadata = chunk["data"]
                        node = metadata.get("langgraph_node", "")
                        if isinstance(msg, AIMessageChunk):
                            # 流式 token
                            if node in _STREAM_NODES:
                                if hasattr(msg, "content") and msg.content:
                                    full_reply += msg.content
                                    yield f"data: {json.dumps({'token': msg.content}, ensure_ascii=False)}\n\n"
                        elif isinstance(msg, AIMessage) and msg.content:
                            # 节点返回的完整 AIMessage（兜底：如果流式 token 为空则使用）
                            if node in _STREAM_NODES and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                                _seen_final_reply = msg.content
            else:
                # 规则未命中 → 交给图：LLM 意图分类 → RAG 或 Agent
                graph_input = {"messages": messages, "intent": ""}
                # 节点名 → 意图映射（用于从流式 chunk 推断意图）
                _NODE_TO_INTENT = {
                    "product_agent": IntentType.PRODUCT_RECOMMEND,
                    "order_agent": IntentType.ORDER_QUERY,
                    "address_agent": IntentType.ADDRESS_MANAGE,
                    "cart_agent": IntentType.CART_QUERY,
                    "chitchat": IntentType.CHITCHAT,
                    "rag_engine": IntentType.KNOWLEDGE_QUERY,
                }
                async for chunk in _agent_graph.astream(
                    graph_input, stream_mode="messages", version="v2",
                    config={"callbacks": [token_callback]},
                ):
                    if chunk["type"] == "messages":
                        msg, metadata = chunk["data"]
                        node = metadata.get("langgraph_node", "")
                        # 从节点名推断意图
                        if node in _NODE_TO_INTENT:
                            _intent = _NODE_TO_INTENT[node]
                        if isinstance(msg, AIMessageChunk):
                            # 流式 token
                            if node in _STREAM_NODES:
                                if hasattr(msg, "content") and msg.content:
                                    full_reply += msg.content
                                    yield f"data: {json.dumps({'token': msg.content}, ensure_ascii=False)}\n\n"
                        elif isinstance(msg, AIMessage) and msg.content:
                            # 节点返回的完整 AIMessage（兜底）
                            if node in _STREAM_NODES and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                                _seen_final_reply = msg.content

            # 兜底：如果流式 token 没有累积任何内容，使用节点返回的完整回复
            if not full_reply and _seen_final_reply:
                full_reply = _seen_final_reply
                yield f"data: {json.dumps({'token': full_reply}, ensure_ascii=False)}\n\n"

            # 发送结束标记（包含结构化数据）
            tool_data = tool_result_store.get_and_clear(request_id)
            logger.info(
                "🔍 [TRACE] tool_data | request_id=%s count=%d tools=%s",
                request_id, len(tool_data), [d["tool"] for d in tool_data] if tool_data else [],
            )
            end_data = {"done": True, "reply": full_reply}
            if tool_data:
                end_data["tool_results"] = tool_data

            # 检查是否有待确认的破坏性操作
            username_for_pending = user.username if user else "anonymous"
            pending = pending_action_store.get_pending_for_request(username_for_pending)
            if pending:
                end_data["pending_actions"] = pending
                logger.info("待确认操作 | user=%s count=%d", username_for_pending, len(pending))

            # ⚠️ 持久化必须在 yield 之前！
            # 前端收到 done 事件后会关闭 SSE 连接，之后的代码不会执行
            await session_store.add_message(username, session_id, user_msg)
            await session_store.add_message(username, session_id, AIMessage(content=full_reply), tool_results=tool_data)

            # 异步提取用户画像（不阻塞 SSE 流）
            if user and user.username:
                import asyncio

                recent_history = await session_store.get_raw_history_dicts(username, session_id)
                asyncio.create_task(
                    user_profile_store.extract_and_merge(
                        user.username, recent_history,
                    ),
                )

            # 上报 Token 用量（fire-and-forget，不阻塞 SSE 流）
            latency_ms = int((time.time() - request_start_time) * 1000)
            usage = token_callback.summary()
            report_token_usage_async(
                username=username,
                session_id=session_id,
                intent=_intent,
                model=usage.get("model", ""),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                tool_calls=usage.get("llm_calls", 0),
                latency_ms=latency_ms,
            )

            logger.info(
                "流式聊天完成 | session=%s user=%s reply_len=%d tokens=%d intent=%s",
                session_id, user.username if user else "anonymous", len(full_reply), usage.get("total_tokens", 0), _intent,
            )

            yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except AgentException as exc:
        raise agent_exception_to_http(exc)
    except Exception as exc:
        logger.exception("流式聊天端点发生意外错误")
        raise agent_exception_to_http(
            AgentException(code=500, message="Internal server error")
        )


# ── 破坏性操作确认端点 ────────────────────────────────


@router.post("/action/confirm")
async def confirm_action(
    request: ConfirmActionRequest,
    req: Request,
    user: CurrentUser | None = Depends(get_optional_user),
):
    """确认并执行一个待确认的破坏性操作。

    流程：
    1. 前端从 SSE done 事件的 pending_actions 中获取 action_id
    2. 用户点击确认后，前端调用此端点
    3. 后端从 PendingActionStore 取出操作并执行
    4. 返回执行结果
    """
    username = user.username if user else "anonymous"

    # 取出待确认操作
    action = pending_action_store.get(request.action_id)
    if not action:
        return ConfirmActionResponse(
            success=False,
            message="操作不存在或已过期，请重新发起操作。",
        )

    # 验证操作归属
    if action.get("username") and action.get("username") != username:
        # 放回去，不是这个用户的
        pending_action_store.put(
            tool_name=action["tool_name"],
            params=action["params"],
            description=action["description"],
            username=action["username"],
        )
        return ConfirmActionResponse(
            success=False,
            message="无权执行此操作。",
        )

    # 设置请求上下文
    token = user.token if user else None
    set_request_context(
        token=token,
        member_username=username,
    )

    # 执行原始工具
    tool_name = action["tool_name"]
    params = action["params"]
    logger.info("确认执行 | user=%s tool=%s params=%s", username, tool_name, params)

    result_text = await execute_confirmed_tool(tool_name, params, token=token)

    return ConfirmActionResponse(
        success=True,
        message=result_text,
        tool_name=tool_name,
    )


# ── 辅助函数 ──────────────────────────────────────────

def _extract_reply(messages: list) -> str:
    """返回消息列表中最后一条 AIMessage 的内容。"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return "抱歉，暂时无法处理您的请求。"


def _extract_token(request: Request) -> str | None:
    """从请求头中提取 JWT token。"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def _rag_query(question: str) -> dict:
    """RAG 引擎查询 — 三级检索策略。"""
    from app.rag.engine import RAGEngine
    engine = RAGEngine()
    return await engine.query(question)


async def _rag_quick_check(question: str) -> bool:
    """快速检测用户问题是否与 RAG 知识库相关（仅做向量检索，不调 LLM）。"""
    try:
        from app.rag.vector_store import MilvusVectorStore
        store = MilvusVectorStore()
        count = await store.count()
        if count == 0:
            logger.info("RAG 快速检测 | 知识库为空，跳过")
            return False
        results = await store.search(question, top_k=1)
        if results:
            score = results[0]["score"]
            logger.info(
                "RAG 快速检测 | query=%s top1_score=%.4f threshold=0.5 hit=%s",
                question[:50], score, score >= 0.5,
            )
            return score >= 0.5
        logger.info("RAG 快速检测 | query=%s 无检索结果", question[:50])
        return False
    except Exception:
        logger.warning("RAG 快速检测异常，跳过 RAG", exc_info=True)
        return False


def _build_structured_response(
    reply: str,
    intent: str,
    request_id: str,
) -> ChatResponse:
    """从工具执行结果构建结构化响应。

    ToolResultStore 中暂存的完整数据会被转换为前端可渲染的卡片。
    """
    tool_data = tool_result_store.get_and_clear(request_id)

    products = []
    orders = []
    logistics = None
    addresses = []
    cart_items = []
    reviews = []
    actions = []

    for item in tool_data:
        tool_name = item["tool"]
        data = item["data"]

        if tool_name == "search_products" and isinstance(data, list):
            # PmsProduct 字段: id, name, price, originalPrice, pic, subTitle, stock, sale
            for p in data:
                products.append(ProductCard(
                    id=p.get("id", 0),
                    name=p.get("name", ""),
                    price=p.get("price", 0),
                    original_price=p.get("originalPrice"),
                    image=p.get("pic"),  # Java 字段是 pic
                    rating=p.get("sale"),  # 用销量代替评分
                ))
            for p in data[:5]:
                actions.append(ActionItem(
                    type="view_product",
                    label=f"查看 {p.get('name', '商品')}",
                    params={"product_id": p.get("id", 0)},
                ))

        elif tool_name == "get_product_info" and isinstance(data, dict):
            # data 可能是 PmsPortalProductDetail（含 product 字段）或直接是 PmsProduct
            product = data.get("product", data)
            products.append(ProductCard(
                id=product.get("id", 0),
                name=product.get("name", ""),
                price=product.get("price", 0),
                original_price=product.get("originalPrice"),
                image=product.get("pic"),
                rating=product.get("sale"),
            ))
            actions.append(ActionItem(
                type="view_product",
                label="查看详情",
                params={"product_id": product.get("id", 0)},
            ))

        elif tool_name == "get_recommendations" and isinstance(data, list):
            for p in data:
                products.append(ProductCard(
                    id=p.get("id", 0),
                    name=p.get("name", ""),
                    price=p.get("price", 0),
                    original_price=p.get("originalPrice"),
                    image=p.get("pic"),
                    rating=p.get("sale"),
                ))

        elif tool_name == "get_user_orders" and isinstance(data, list):
            # OmsOrder 字段: id, orderSn, totalAmount, status, createTime, orderItemList
            # OmsOrderItem 字段: productName, productPic, productPrice
            status_map = {0: "待付款", 1: "待发货", 2: "已发货", 3: "已完成", 4: "已关闭", 5: "无效"}
            for o in data:
                items = o.get("orderItemList", [])
                product_name = items[0].get("productName", "未知商品") if items else "未知商品"
                product_image = items[0].get("productPic") if items else None  # OmsOrderItem.productPic
                orders.append(OrderCard(
                    order_id=o.get("id", 0),
                    order_sn=o.get("orderSn", ""),
                    product_name=product_name,
                    product_image=product_image,
                    total_amount=o.get("totalAmount", 0),
                    status=o.get("status", -1),
                    status_text=status_map.get(o.get("status", -1), "未知"),
                    create_time=o.get("createTime"),
                ))
                order_id = o.get("id", 0)
                actions.append(ActionItem(
                    type="view_order",
                    label="查看详情",
                    params={"order_id": order_id},
                ))
                if o.get("status") in (2, 3):  # 已发货/已完成
                    actions.append(ActionItem(
                        type="view_logistics",
                        label="查看物流",
                        params={"order_id": order_id},
                    ))
                if o.get("status") in (0, 1, 2):  # 可退款
                    actions.append(ActionItem(
                        type="apply_refund",
                        label="申请退款",
                        params={"order_id": order_id},
                    ))

        elif tool_name == "get_order_detail" and isinstance(data, dict):
            status_map = {0: "待付款", 1: "待发货", 2: "已发货", 3: "已完成", 4: "已关闭", 5: "无效"}
            items = data.get("orderItemList", [])
            product_name = items[0].get("productName", "未知商品") if items else "未知商品"
            orders.append(OrderCard(
                order_id=data.get("id", 0),
                order_sn=data.get("orderSn", ""),
                product_name=product_name,
                product_image=items[0].get("productPic") if items else None,
                total_amount=data.get("totalAmount", 0),
                status=data.get("status", -1),
                status_text=status_map.get(data.get("status", -1), "未知"),
                create_time=data.get("createTime"),
            ))

        elif tool_name == "get_logistics" and isinstance(data, dict):
            # LogisticsDetailResult: deliveryCompany, deliverySn, traceList
            # LogisticsTraceResult: traceTime, location, statusText, statusCode
            traces = data.get("traceList", [])
            latest_trace = traces[0].get("statusText", "未知") if traces else "暂无物流信息"
            logistics = LogisticsCard(
                order_id=data.get("orderId", 0) if "orderId" in data else 0,
                logistics_company=data.get("deliveryCompany", "未知快递"),
                tracking_number=data.get("deliverySn", ""),
                current_status=latest_trace,
                latest_update=str(traces[0].get("traceTime", "")) if traces else None,
                timeline=[
                    {
                        "time": str(t.get("traceTime", "")),
                        "location": t.get("location", ""),
                        "status": t.get("statusText", ""),
                    }
                    for t in traces
                ],
            )
            actions.append(ActionItem(
                type="view_logistics",
                label="查看物流详情",
                params={"order_id": logistics.order_id},
            ))

        elif tool_name == "get_addresses" and isinstance(data, list):
            # UmsMemberReceiveAddress: id, name, phoneNumber, detailAddress, defaultStatus, province, city, region
            for a in data:
                province = a.get("province", "")
                city = a.get("city", "")
                region = a.get("region", "")
                detail = a.get("detailAddress", "")
                full_addr = f"{province}{city}{region}{detail}"
                addresses.append(AddressCard(
                    id=a.get("id", 0),
                    name=a.get("name", ""),
                    phone=a.get("phoneNumber", ""),
                    address=full_addr,
                    is_default=a.get("defaultStatus") == 1,
                ))

        elif tool_name == "apply_refund" and isinstance(data, dict):
            actions.append(ActionItem(
                type="view_refund",
                label="查看退款进度",
                params={"order_id": data.get("orderId", 0)},
            ))

        elif tool_name == "get_cart_list" and isinstance(data, list):
            # OmsCartItem 字段: id, productId, productName, productPic, price, quantity, productAttr
            for item in data:
                cart_items.append(CartItemCard(
                    id=item.get("id", 0),
                    product_id=item.get("productId", 0),
                    product_name=item.get("productName", "未知商品"),
                    product_image=item.get("productPic"),
                    price=item.get("price", 0),
                    quantity=item.get("quantity", 1),
                    checked=item.get("checked", 1) == 1,
                ))
            for item in data[:5]:
                actions.append(ActionItem(
                    type="view_product",
                    label=f"查看 {item.get('productName', '商品')}",
                    params={"product_id": item.get("productId", 0)},
                ))

        elif tool_name == "create_review" and isinstance(data, dict):
            reviews.append(ReviewCard(
                order_id=data.get("order_id", 0),
                order_item_id=data.get("order_item_id", 0),
                product_id=data.get("product_id", 0),
                star=data.get("star", 5),
                content=data.get("content", ""),
            ))

    return ChatResponse(
        reply=reply,
        intent=intent if isinstance(intent, str) else str(intent),
        products=products,
        orders=orders,
        logistics=logistics,
        addresses=addresses,
        cart_items=cart_items,
        reviews=reviews,
        actions=actions,
        recommended_products=products if intent == IntentType.PRODUCT_RECOMMEND else [],
    )
