from abc import ABC, abstractmethod

from domain.entities.download import Download


class DownloadRepository(ABC):
    @abstractmethod
    async def add(self, download: Download) -> Download: ...

    @abstractmethod
    async def list_by_user(
        self, telegram_id: int, *, limit: int, offset: int
    ) -> list[Download]: ...
