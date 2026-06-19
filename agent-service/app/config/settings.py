from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（agent-service/）
_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """从环境变量 / .env 文件加载的应用配置。"""

    # ── LLM ──
    llm_api_key: str
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model_name: str = "deepseek-v4-flash"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ── 商城后端 ──
    mall_portal_url: str = "http://localhost:8085"
    mall_admin_url: str = "http://localhost:8080"
    mall_search_url: str = "http://localhost:8081"
    jwt_secret: str
    admin_jwt_secret: str = ""  # mall-admin 的 JWT secret（空则 fallback 到 jwt_secret）
    jwt_algorithm: str = "HS512"

    # ── Milvus ──
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "LXfanmall_knowledge"
    milvus_dimension: int = 1024            # text-embedding-v4 输出维度

    # ── Redis 缓存（RAG 查询缓存，复用现有 Redis db2） ──
    rag_redis_url: str = "redis://localhost:6379/2"
    rag_cache_ttl: int = 86400              # 缓存 24 小时
    rag_similarity_high: float = 0.95       # 高相似度阈值 — 直接返回
    rag_similarity_mid: float = 0.85        # 中相似度阈值 — 取 Top3

    # ── RAG 分块与检索（新） ──
    chunk_max_tokens: int = 512
    chunk_overlap_tokens: int = 64
    retrieval_vector_weight: float = 0.7
    retrieval_keyword_weight: float = 0.3
    retrieval_similarity_threshold: float = 0.4
    rerank_threshold: float = 0.85
    default_chunking_strategy: str = "general"

    # ── Embedding（阿里云百炼 Qwen text-embedding-v4 API） ──
    embedding_api_key: str = ""             # 百炼 API Key
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v4"

    # ── 重排序（阿里云百炼 gte-rerank-v2 API） ──
    reranker_api_key: str = ""              # 默认复用 embedding_api_key
    reranker_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    reranker_model: str = "gte-rerank-v2"

    # ── 文件上传 ──
    upload_dir: str = "./uploads/rag_docs"
    max_upload_size: int = 20 * 1024 * 1024  # 20MB

    # ── Session & 用户画像（Redis db3）──
    session_redis_url: str = "redis://localhost:6379/3"
    session_ttl: int = 3600       # 会话滑动过期时间（秒）
    session_max_turns: int = 20   # 单会话最大保留轮数

    # ── 应用配置 ──
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(_BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """应用配置的缓存单例。"""
    return Settings()
