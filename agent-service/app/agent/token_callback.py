"""LangChain Callback — 捕获每次 LLM 调用的 Token 用量。

在请求级别实例化，通过 config={"callbacks": [cb]} 注入 LangChain 调用链。
SSE 流结束后由 chat.py 汇总并异步上报到 mall-admin。
"""

import logging
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class TokenUsageCallback(BaseCallbackHandler):
    """捕获每次 LLM 调用的 token usage。"""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, int]] = []
        self.model: str = ""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束时提取 usage 信息。

        流式模式下 token usage 的位置因模型/平台而异，按优先级逐处检查。
        """
        llm_output = response.llm_output or {}

        # ── 提取 usage ──
        usage: dict = {}

        # 来源 1: llm_output 标准字段（非流式 OpenAI）
        usage = llm_output.get("token_usage", {})
        if not usage:
            usage = llm_output.get("usage", {})

        # 来源 2: generation_info（流式模式下 langchain-openai 提取的 usage）
        if not usage:
            for gen in (response.generations or []):
                for g in gen:
                    info = getattr(g, "generation_info", None) or {}
                    usage = info.get("token_usage", {})
                    if not usage:
                        usage = info.get("usage", {})
                    if usage:
                        break
                if usage:
                    break

        # 来源 3: 某些版本将 usage 放在 generation 的 message 的 usage_metadata 中
        if not usage:
            for gen in (response.generations or []):
                for g in gen:
                    msg = getattr(g, "message", None)
                    if msg:
                        meta = getattr(msg, "usage_metadata", None)
                        if meta and isinstance(meta, dict) and meta.get("input_tokens", 0) > 0:
                            usage = {
                                "prompt_tokens": meta.get("input_tokens", 0),
                                "completion_tokens": meta.get("output_tokens", 0),
                                "total_tokens": meta.get("total_tokens", 0),
                            }
                            break
                if usage:
                    break

        if usage:
            record = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
            self.records.append(record)
            logger.info("Token usage captured: %s", record)
        else:
            logger.warning("No token usage found in LLM result")

        # 记录模型名称（取最后一次）
        if response.llm_output:
            self.model = response.llm_output.get("model_name", "")

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r["prompt_tokens"] for r in self.records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r["completion_tokens"] for r in self.records)

    @property
    def total_tokens(self) -> int:
        return sum(r["total_tokens"] for r in self.records)

    @property
    def llm_call_count(self) -> int:
        return len(self.records)

    def summary(self) -> dict:
        """返回汇总数据，用于上报。"""
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_call_count,
            "model": self.model,
        }
