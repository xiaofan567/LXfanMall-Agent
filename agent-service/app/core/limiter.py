"""速率限制器 — 基于 slowapi，使用客户端 IP 作为限流 key。"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# 全局默认：60 次/分钟
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
