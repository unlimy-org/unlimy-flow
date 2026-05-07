from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PostRecord:
    id: int
    created_at: datetime
    news_text: str
    post_text: str
    publish_mode: str
    published: bool
    published_at: datetime | None

