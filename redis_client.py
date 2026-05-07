from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis
from redis.asyncio.client import Redis as RedisType


class RedisClient:
    def __init__(self, url: str) -> None:
        self._url = url
        self._redis: RedisType | None = None

    async def connect(self) -> None:
        self._redis = Redis.from_url(self._url, decode_responses=True)
        await self._redis.ping()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    @property
    def raw(self) -> RedisType:
        assert self._redis is not None
        return self._redis

    async def get_publish_mode(self, default_mode: str) -> str:
        value = await self.raw.get("publish_mode")
        return value if value in {"instant", "queue"} else default_mode

    async def set_publish_mode(self, mode: str) -> None:
        await self.raw.set("publish_mode", mode)

    async def incr_session_counter(self) -> int:
        return await self.raw.incr("session_generated_posts")

    async def get_session_counter(self) -> int:
        value = await self.raw.get("session_generated_posts")
        return int(value) if value else 0

    async def set_pending_post(self, user_id: int, payload: dict[str, Any], ttl_sec: int = 1800) -> None:
        key = f"pending_post:{user_id}"
        await self.raw.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl_sec)

    async def get_pending_post(self, user_id: int) -> dict[str, Any] | None:
        key = f"pending_post:{user_id}"
        value = await self.raw.get(key)
        if not value:
            return None
        return json.loads(value)

    async def delete_pending_post(self, user_id: int) -> None:
        key = f"pending_post:{user_id}"
        await self.raw.delete(key)

