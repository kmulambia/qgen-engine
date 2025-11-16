from fastapi import Request
from redis.asyncio import Redis
import time
from typing import Callable
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp
from engine.utils.config_util import load_config

config = load_config()


class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.rate_limit_requests = config.require_variable("RATE_LIMIT_REQUESTS", int)
        self.rate_limit_window = config.require_variable("RATE_LIMIT_WINDOW", int)

    async def is_rate_limited(self, key: str) -> tuple[bool, int]:
        current = int(time.time())
        window_start = current - self.rate_limit_window

        async with self.redis.pipeline() as pipe:
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zadd(key, {str(current): current})
            await pipe.zcount(key, window_start, current)
            await pipe.expire(key, self.rate_limit_window)
            results = await pipe.execute()

        request_count = results[2]
        return request_count > self.rate_limit_requests, request_count


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Get Redis instance from app state
        redis: Redis = request.app.state.cache

        # Create rate limiter instance
        rate_limiter = RateLimiter(redis)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        # Check rate limit
        is_limited, current_requests = await rate_limiter.is_rate_limited(key)

        # Store rate limit info in request.state
        request.state.rate_limit_remaining = max(
            rate_limiter.rate_limit_requests - current_requests,
            0
        )
        request.state.rate_limit_limit = rate_limiter.rate_limit_requests
        request.state.rate_limit_window = rate_limiter.rate_limit_window

        if is_limited:
            return Response(
                status_code=429,
                content="Too many requests",
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(rate_limiter.rate_limit_window)
                }
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        response.headers["X-RateLimit-Window"] = str(request.state.rate_limit_window)

        return response


def rate_limit():
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The original function can be called directly since rate limiting
            # is handled by the middleware
            return await func(*args, **kwargs)

        return wrapper

    return decorator
