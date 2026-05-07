from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class OwnerOnlyMiddleware(BaseMiddleware):
    def __init__(self, owner_id: int) -> None:
        self._owner_id = owner_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if not event.from_user or event.from_user.id != self._owner_id:
                return None
        return await handler(event, data)

