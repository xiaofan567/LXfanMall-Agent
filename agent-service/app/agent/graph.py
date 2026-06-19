"""LangGraph Agent 工作流定义。

流程:
    classify_intent ─┬─► rag_engine     ─► END  (knowledge_query)
                     ├─► product_agent  ─► END
                     ├─► order_agent    ─► END
                     ├─► address_agent  ─► END
                     └─► chitchat       ─► END

注意：规则路由命中的场景会直接跳过 classify_intent，
在 chat.py 中直接调用对应的 Agent 节点。
"""

from typing import TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    address_agent_node,
    cart_agent_node,
    chitchat_node,
    classify_intent,
    order_agent_node,
    product_agent_node,
)
from app.config.constants import IntentType


# ── 状态模式 ───────────────────────────────────────────

class AgentState(TypedDict):
    messages: list[BaseMessage]
    intent: str


# ── RAG 节点 ──────────────────────────────────────────

async def rag_node(state: AgentState) -> dict:
    """RAG 知识问答节点 — 检索知识库并生成回答。"""
    from app.api.v1.chat import _rag_query
    from app.agent.nodes import _get_latest_user_message

    messages = state["messages"]
    question = _get_latest_user_message(messages)
    rag_result = await _rag_query(question)
    return {"messages": [AIMessage(content=rag_result["answer"])]}


# ── 路由 ───────────────────────────────────────────────

def route_by_intent(state: AgentState) -> str:
    """根据已分类的意图返回对应的节点名称。"""
    intent = state.get("intent", IntentType.CHITCHAT)
    routing = {
        IntentType.KNOWLEDGE_QUERY: "rag_engine",
        IntentType.PRODUCT_RECOMMEND: "product_agent",
        IntentType.ORDER_QUERY: "order_agent",
        IntentType.CUSTOMER_SERVICE: "order_agent",  # 售后也走 order_agent
        IntentType.ADDRESS_MANAGE: "address_agent",
        IntentType.CART_QUERY: "cart_agent",
        IntentType.CHITCHAT: "chitchat",
    }
    return routing.get(intent, "chitchat")


# ── 构建图 ─────────────────────────────────────────────

def build_agent_graph():
    """编译并返回 LangGraph Agent 工作流。"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("rag_engine", rag_node)
    graph.add_node("product_agent", product_agent_node)
    graph.add_node("order_agent", order_agent_node)
    graph.add_node("address_agent", address_agent_node)
    graph.add_node("cart_agent", cart_agent_node)
    graph.add_node("chitchat", chitchat_node)

    # 入口点
    graph.set_entry_point("classify_intent")

    # 意图分类后的条件路由
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "rag_engine": "rag_engine",
            "product_agent": "product_agent",
            "order_agent": "order_agent",
            "address_agent": "address_agent",
            "cart_agent": "cart_agent",
            "chitchat": "chitchat",
        },
    )

    # 所有叶子节点指向 END
    graph.add_edge("rag_engine", END)
    graph.add_edge("product_agent", END)
    graph.add_edge("order_agent", END)
    graph.add_edge("address_agent", END)
    graph.add_edge("cart_agent", END)
    graph.add_edge("chitchat", END)

    return graph.compile()
