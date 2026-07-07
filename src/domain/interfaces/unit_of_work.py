from abc import ABC, abstractmethod
from types import TracebackType

from domain.repositories.download_repository import DownloadRepository
from domain.repositories.user_repository import UserRepository


class UnitOfWork(ABC):
    users: UserRepository
    downloads: DownloadRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
