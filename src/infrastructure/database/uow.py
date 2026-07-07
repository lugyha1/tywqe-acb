from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.interfaces.unit_of_work import UnitOfWork
from infrastructure.database.repositories import (
    SqlAlchemyDownloadRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._factory()
        self.users = SqlAlchemyUserRepository(self.session)
        self.downloads = SqlAlchemyDownloadRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
