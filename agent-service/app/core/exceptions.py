"""Agent 服务的统一异常层级。"""

from fastapi import HTTPException, status


class AgentException(Exception):
    """Agent 服务所有异常的基类。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class LLMCallException(AgentException):
    """LLM API 调用失败时抛出。"""

    def __init__(self, detail: str = ""):
        super().__init__(
            code=status.HTTP_502_BAD_GATEWAY,
            message=f"LLM service error: {detail}" if detail else "LLM service error",
        )


class MallAPIException(AgentException):
    """调用 Java 商城后端失败时抛出。"""

    def __init__(self, detail: str = ""):
        super().__init__(
            code=status.HTTP_502_BAD_GATEWAY,
            message=f"Mall API error: {detail}" if detail else "Mall API error",
        )


class AuthenticationException(AgentException):
    """JWT 验证或会员查询失败时抛出。"""

    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(
            code=status.HTTP_401_UNAUTHORIZED,
            message=detail,
        )


class IntentClassifyException(AgentException):
    """意图分类失败时抛出。"""

    def __init__(self, detail: str = ""):
        super().__init__(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Intent classification failed: {detail}" if detail else "Intent classification failed",
        )


def agent_exception_to_http(exc: AgentException) -> HTTPException:
    """将 AgentException 转换为 FastAPI HTTPException。"""
    return HTTPException(status_code=exc.code, detail=exc.message)
