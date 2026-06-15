import logging
import time

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTION MIGRATION PATH: Redis Rate Limiter
# ═══════════════════════════════════════════════════════════════════════════════
#
# Para producción con múltiples réplicas, reemplazar esta implementación en
# memoria por una basada en Redis:
#
#   pip install redis
#
#   class RedisRateLimiter:
#       def __init__(self, redis_url: str, max_attempts: int = 5,
#                    window_seconds: int = 60):
#           import redis.asyncio as aioredis
#           self._redis = aioredis.from_url(redis_url)
#           self.max_attempts = max_attempts
#           self.window_seconds = window_seconds
#
#       async def is_allowed(self, ip: str, email: str) -> bool:
#           key = f"ratelimit:{ip}:{email}"
#           current = await self._redis.llen(key)
#           if current >= self.max_attempts:
#               return False
#           async with self._redis.pipeline() as pipe:
#               await pipe.rpush(key, time.time())
#               await pipe.expire(key, self.window_seconds)
#               await pipe.execute()
#           return True
#
#       async def reset(self, ip: str, email: str):
#           await self._redis.delete(f"ratelimit:{ip}:{email}")
#
# Luego registrar la nueva implementación como singleton en app/core/dependencies.py
# y reemplazar su uso en routers/auth.py y routers/twofa.py.
# ═══════════════════════════════════════════════════════════════════════════════


class RateLimiter:
    """In-memory sliding window rate limiter.

    Key is "{ip}:{email}". Prunes expired entries on access.
    Not thread-safe by design — single-threaded FastAPI dev server.
    For production, replace with Redis-based implementation.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = {}

    def is_allowed(self, ip: str, email: str) -> bool:
        key = f"{ip}:{email}"
        now = time.time()
        timestamps = self._store.get(key, [])
        timestamps = [t for t in timestamps if now - t < self.window_seconds]
        if len(timestamps) >= self.max_attempts:
            self._store[key] = timestamps
            return False
        timestamps.append(now)
        self._store[key] = timestamps
        return True

    def reset(self, ip: str, email: str) -> None:
        key = f"{ip}:{email}"
        self._store.pop(key, None)
