"""FastAPI 应用入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter

from app.api.v1.chat import router as chat_router
from app.api.v1.rag import router as rag_router
from app.api.v1.user import router as user_router
from app.config.settings import get_settings
from app.core.exceptions import AgentException
from app.core.logging import setup_logging
from app.mcp.mall_adapter import init_mall_adapter
from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子。"""
    setup_logging()

    # 初始化 MallAdapter
    settings = get_settings()
    adapter = init_mall_adapter(settings.mall_portal_url)
    logger.info("MallAdapter 已初始化 | base_url=%s", settings.mall_portal_url)

    yield

    # 关闭 HTTP 客户端
    await adapter.close()
    logger.info("MallAdapter 已关闭")


app = FastAPI(
    title="LXfanMall Agent Service",
    description="智能客服与购物顾问 AI Agent",
    version="0.2.0",
    lifespan=lifespan,
)

# 注册速率限制器
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"code": 429, "message": "请求过于频繁，请稍后再试", "data": None},
    )

# ── CORS 中间件 ────────────────────────────────────────
# 开发环境白名单：前端 dev server + mall-portal 代理
_CORS_ORIGINS = [
    "http://localhost:5173",   # Vite dev server (LXfanMallWeb)
    "http://localhost:5174",   # Vite dev server (mall-admin-web)
    "http://localhost:8085",   # mall-portal（前端生产代理）
    "http://localhost:8090",   # mall-admin-web 生产代理
    "http://localhost:3000",   # 备用前端端口
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 异常处理器 ───────────────────────────────────────

@app.exception_handler(AgentException)
async def agent_exception_handler(_request: Request, exc: AgentException):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


# ── 路由 ─────────────────────────────────────────────

app.include_router(chat_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse()


# ── 开发入口 ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
