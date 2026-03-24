from redis import RedisError
from redis.asyncio import Redis


class RateLimiterUnavailable(Exception):
    pass


class RedisFixedWindowRateLimiter:
    def __init__(self, redis_url: str, per_minute_limit: int, per_hour_limit: int):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.per_minute_limit = per_minute_limit
        self.per_hour_limit = per_hour_limit

    async def allow(self, key: str) -> bool:
        try:
            within_minute_limit = await self._check_window(
                key=key,
                window_name="minute",
                window_seconds=60,
                max_requests=self.per_minute_limit,
            )
            within_hour_limit = await self._check_window(
                key=key,
                window_name="hour",
                window_seconds=3600,
                max_requests=self.per_hour_limit,
            )
        except RedisError as exc:
            raise RateLimiterUnavailable("redis_unavailable") from exc

        return within_minute_limit and within_hour_limit

    async def _check_window(
        self,
        key: str,
        window_name: str,
        window_seconds: int,
        max_requests: int,
    ) -> bool:
        redis_key = f"vf:rate:{window_name}:{key}"
        count = await self.redis.incr(redis_key)
        if count == 1:
            await self.redis.expire(redis_key, window_seconds)
        return count <= max_requests

    async def close(self) -> None:
        await self.redis.aclose()
