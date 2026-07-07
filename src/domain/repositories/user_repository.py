from abc import ABC, abstractmethod

from domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def upsert(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> User | None: ...
