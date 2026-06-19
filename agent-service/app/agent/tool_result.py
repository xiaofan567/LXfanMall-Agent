"""工具结果分流存储。

工具返回值做两路分流：
- 精简摘要 → 给 LLM（用于决策和生成回复）
- 完整数据 → 给前端（用于渲染卡片）

同类工具结果互斥：
- 搜索类 (search_products) ↔ 推荐类 (get_recommendations/get_hot_products/get_new_products)
- 调用一方时自动清除另一方的结果，避免前端卡片混入无关商品
"""

import logging
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)

# 当前请求 ID（由 chat 端点在请求开始时设置）
_current_request_id: ContextVar[str] = ContextVar("current_request_id", default="")

# 互斥工具分组：同一组内只保留最后一次调用的结果
_SEARCH_TOOLS = {"search_products"}
_RECOMMEND_TOOLS = {"get_recommendations", "get_hot_products", "get_new_products"}
_ORDER_LIST_TOOLS = {"get_user_orders"}
_ORDER_DETAIL_TOOLS = {"get_order_detail"}
_MUTEX_GROUPS = [_SEARCH_TOOLS, _RECOMMEND_TOOLS, _ORDER_LIST_TOOLS, _ORDER_DETAIL_TOOLS]


def set_current_request_id(request_id: str) -> None:
    """设置当前请求 ID（在请求入口调用）。"""
    _current_request_id.set(request_id)


def get_current_request_id() -> str:
    """获取当前请求 ID。"""
    return _current_request_id.get()


class ToolResultStore:
    """暂存工具返回的完整数据，用于附带到响应中。"""

    def __init__(self) -> None:
        self._results: dict[str, list[dict[str, Any]]] = {}

    def store(self, tool_name: str, data: Any) -> None:
        """存储工具返回的完整数据。

        同类工具互斥：调用搜索类工具时清除推荐类结果，反之亦然。
        """
        request_id = get_current_request_id()
        if not request_id:
            return
        if request_id not in self._results:
            self._results[request_id] = []

        # 互斥清除：找到当前工具所属的分组，清除其他分组的结果
        current_group = None
        for group in _MUTEX_GROUPS:
            if tool_name in group:
                current_group = group
                break

        if current_group:
            other_tools = set()
            for group in _MUTEX_GROUPS:
                if group is not current_group:
                    other_tools |= group
            before = len(self._results[request_id])
            self._results[request_id] = [
                r for r in self._results[request_id]
                if r["tool"] not in other_tools
            ]
            after = len(self._results[request_id])
            if before != after:
                logger.debug(
                    "互斥清除 | request=%s tool=%s cleared=%d",
                    request_id, tool_name, before - after,
                )

        self._results[request_id].append({
            "tool": tool_name,
            "data": data,
        })
        logger.debug("工具结果已暂存 | request=%s tool=%s", request_id, tool_name)

    def get_and_clear(self, request_id: str) -> list[dict[str, Any]]:
        """获取并清除暂存数据。"""
        return self._results.pop(request_id, [])


# 全局单例
tool_result_store = ToolResultStore()
