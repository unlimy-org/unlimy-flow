from __future__ import annotations

from typing import Any

import asyncpg

from models import PostRecord


CREATE_POSTS_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    news_text TEXT NOT NULL,
    post_text TEXT NOT NULL,
    publish_mode TEXT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ
);
"""

CREATE_SCHEDULED_SQL = """
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    channel_id TEXT NOT NULL,
    post_text TEXT NOT NULL,
    media_type TEXT,
    media_file_id TEXT,
    publish_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool[Any] | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=1, max_size=10)
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_POSTS_SQL)
            await conn.execute(CREATE_SCHEDULED_SQL)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def insert_post(self, news_text: str, post_text: str, publish_mode: str) -> int:
        assert self._pool is not None
        query = """
        INSERT INTO posts (news_text, post_text, publish_mode, published)
        VALUES ($1, $2, $3, FALSE)
        RETURNING id;
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, news_text, post_text, publish_mode)

    async def mark_published(self, post_id: int) -> None:
        assert self._pool is not None
        query = """
        UPDATE posts
        SET published = TRUE, published_at = NOW()
        WHERE id = $1;
        """
        async with self._pool.acquire() as conn:
            await conn.execute(query, post_id)

    async def count_total(self) -> int:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM posts;")

    async def count_last_24h(self) -> int:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM posts WHERE created_at >= NOW() - INTERVAL '24 hours';"
            )

    async def get_recent_posts(self, limit: int = 5) -> list[PostRecord]:
        assert self._pool is not None
        query = """
        SELECT id, created_at, news_text, post_text, publish_mode, published, published_at
        FROM posts
        ORDER BY created_at DESC
        LIMIT $1;
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
        return [
            PostRecord(
                id=row["id"],
                created_at=row["created_at"],
                news_text=row["news_text"],
                post_text=row["post_text"],
                publish_mode=row["publish_mode"],
                published=row["published"],
                published_at=row["published_at"],
            )
            for row in rows
        ]

    async def schedule_post(
        self,
        post_id: int,
        channel_id: str,
        post_text: str,
        publish_at,
        media_type: str | None,
        media_file_id: str | None,
    ) -> int:
        assert self._pool is not None
        query = """
        INSERT INTO scheduled_posts (post_id, channel_id, post_text, media_type, media_file_id, publish_at, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'pending')
        RETURNING id;
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, post_id, channel_id, post_text, media_type, media_file_id, publish_at)

    async def fetch_due_scheduled(self, limit: int = 20) -> list[asyncpg.Record]:
        assert self._pool is not None
        query = """
        SELECT id, post_id, channel_id, post_text, media_type, media_file_id, publish_at
        FROM scheduled_posts
        WHERE status = 'pending' AND publish_at <= NOW()
        ORDER BY publish_at ASC
        LIMIT $1;
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, limit)

    async def mark_scheduled_done(self, scheduled_id: int) -> None:
        assert self._pool is not None
        query = "UPDATE scheduled_posts SET status = 'done' WHERE id = $1;"
        async with self._pool.acquire() as conn:
            await conn.execute(query, scheduled_id)

    async def mark_scheduled_failed(self, scheduled_id: int) -> None:
        assert self._pool is not None
        query = "UPDATE scheduled_posts SET status = 'failed' WHERE id = $1;"
        async with self._pool.acquire() as conn:
            await conn.execute(query, scheduled_id)

    async def list_pending_scheduled(self, limit: int = 10) -> list[asyncpg.Record]:
        assert self._pool is not None
        query = """
        SELECT id, post_id, publish_at, post_text, media_type
        FROM scheduled_posts
        WHERE status = 'pending'
        ORDER BY publish_at ASC
        LIMIT $1;
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, limit)

    async def cancel_scheduled(self, scheduled_id: int) -> bool:
        assert self._pool is not None
        query = """
        UPDATE scheduled_posts
        SET status = 'cancelled'
        WHERE id = $1 AND status = 'pending'
        RETURNING id;
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, scheduled_id)
            return row is not None
