from redis import RedisError
from redis.asyncio import Redis


class RateLimiterUnavailable(Exception):
    pass


class RedisFixedWindowRateLimiter:
    def __init__(self, redis_url: str, max_requests: int, window_seconds: int):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def allow(self, key: str) -> bool:
        redis_key = f"vf:rate:{key}"

        try:
            count = await self.redis.incr(redis_key)
            if count == 1:
                await self.redis.expire(redis_key, self.window_seconds)
        except RedisError as exc:
            raise RateLimiterUnavailable("redis_unavailable") from exc

        return count <= self.max_requests

    async def close(self) -> None:
        await self.redis.aclose()
