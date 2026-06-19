"""Token 用量上报器 — 异步 POST 到 mall-admin。

在 SSE 流结束后以 fire-and-forget 方式调用，不阻塞用户响应。
"""

import asyncio
import logging

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_REPORT_PATH = "/home/tokenUsage/report"
_TIMEOUT = 5.0


def _get_report_url() -> str:
    settings = get_settings()
    return settings.mall_admin_url.rstrip("/") + _REPORT_PATH


async def report_token_usage(
    username: str,
    session_id: str,
    intent: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    tool_calls: int,
    latency_ms: int,
) -> None:
    """异步上报 token 用量到 mall-admin。失败仅记录日志，不影响业务。"""
    payload = {
        "username": username,
        "sessionId": session_id,
        "intent": intent,
        "model": model,
        "promptTokens": prompt_tokens,
        "completionTokens": completion_tokens,
        "totalTokens": total_tokens,
        "toolCalls": tool_calls,
        "latencyMs": latency_ms,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(_get_report_url(), json=payload, timeout=_TIMEOUT)
            if resp.status_code == 200:
                logger.info("Token usage reported | user=%s tokens=%d", username, total_tokens)
            else:
                logger.warning("Token usage report failed | status=%d body=%s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Token usage report error: %s", exc)


def report_token_usage_async(
    username: str,
    session_id: str,
    intent: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    tool_calls: int,
    latency_ms: int,
) -> None:
    """Fire-and-forget 包装，在事件循环中调度异步上报。"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            report_token_usage(
                username=username,
                session_id=session_id,
                intent=intent,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                tool_calls=tool_calls,
                latency_ms=latency_ms,
            )
        )
    except RuntimeError:
        # 没有运行中的事件循环（如测试环境），跳过
        logger.debug("No running event loop, skipping token usage report")
