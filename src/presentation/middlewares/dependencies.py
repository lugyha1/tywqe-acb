from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.create_download import CreateDownloadUseCase
from application.use_cases.list_history import ListHistoryUseCase
from application.use_cases.register_user import RegisterUserUseCase
from infrastructure.database.uow import SqlAlchemyUnitOfWork


class DependencyMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        uow = SqlAlchemyUnitOfWork(self._session_factory)
        data["register_user"] = RegisterUserUseCase(uow)
        data["create_download"] = CreateDownloadUseCase(uow)
        data["list_history"] = ListHistoryUseCase(uow)
        return await handler(event, data)
