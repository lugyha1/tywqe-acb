from core.validators.url import validate_media_url
from domain.entities.download import Download, DownloadStatus
from domain.interfaces.unit_of_work import UnitOfWork


class CreateDownloadUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, telegram_id: int, url: str) -> Download:
        clean_url = validate_media_url(url)
        async with self._uow as uow:
            download = await uow.downloads.add(
                Download(None, telegram_id, clean_url, "Media file", DownloadStatus.queued)
            )
            await uow.commit()
            return download
