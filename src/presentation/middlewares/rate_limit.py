from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from redis.asyncio import Redis

from core.exceptions.base import RateLimitExceededError


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, limit_per_minute: int) -> None:
        self._redis = redis
        self._limit = limit_per_minute

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = self._extract_user_id(event)
        if user_id is None:
            return await handler(event, data)
        key = f"rate-limit:{user_id}"
        current = await self._redis.incr(key)
        if current == 1:
            await self._redis.expire(key, 60)
        if current > self._limit:
            raise RateLimitExceededError()
        return await handler(event, data)

    def _extract_user_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery):
            return event.from_user.id
        return None
