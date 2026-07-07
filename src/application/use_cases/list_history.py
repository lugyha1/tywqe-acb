from domain.entities.download import Download
from domain.interfaces.unit_of_work import UnitOfWork


class ListHistoryUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, telegram_id: int, page: int = 0, page_size: int = 5) -> list[Download]:
        async with self._uow as uow:
            return await uow.downloads.list_by_user(
                telegram_id, limit=page_size, offset=page * page_size
            )
