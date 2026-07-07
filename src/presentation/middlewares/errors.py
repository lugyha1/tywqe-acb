from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from core.exceptions.base import AppError

logger = structlog.get_logger(__name__)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except AppError as exc:
            await self._notify(event, exc.user_message)
            logger.warning("user_error", error=str(exc))
        except Exception as exc:
            await self._notify(
                event,
                (
                    "╭──────────────╮\n"
                    "⚠️ <b>Ошибка</b>\n"
                    "╰──────────────╯\n\n"
                    "Мы уже получили отчёт и скоро всё исправим."
                ),
            )
            logger.exception("unhandled_error", error=str(exc))

    async def _notify(self, event: TelegramObject, text: str) -> None:
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer("Ошибка", show_alert=True)
            if event.message:
                await event.message.answer(text)
