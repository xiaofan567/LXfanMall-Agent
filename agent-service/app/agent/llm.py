"""LLM 实例工厂 — 模型创建的唯一入口。"""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config.settings import get_settings


@lru_cache
def create_llm() -> ChatOpenAI:
    """返回一个配置好的 ChatOpenAI 实例（兼容 DeepSeek）。

    使用 lru_cache 保证同一客户端在请求间复用。
    """
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        streaming=True,
    )
