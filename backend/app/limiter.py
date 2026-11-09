import os
from slowapi import Limiter
from starlette.requests import Request

# Number of reverse proxies in front of the app that append to X-Forwarded-For
# (Railway/Render/Fly = 1). Set to 0 if the app is exposed directly.
TRUSTED_PROXY_COUNT = int(os.getenv("TRUSTED_PROXY_COUNT", "1"))


def get_real_ip(request: Request) -> str:
    """Get the client IP without trusting values the client can spoof.

    The left-most X-Forwarded-For entries are supplied by the client, so they
    can't be used for rate limiting. Each trusted proxy appends the address it
    saw, so the real client IP is the Nth entry from the right.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and TRUSTED_PROXY_COUNT > 0:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        if len(ips) >= TRUSTED_PROXY_COUNT:
            return ips[-TRUSTED_PROXY_COUNT]
    return request.client.host if request.client else "127.0.0.1"


limiter = Limiter(key_func=get_real_ip)
