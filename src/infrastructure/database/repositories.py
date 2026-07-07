from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.download import Download, DownloadStatus
from domain.entities.user import User
from domain.repositories.download_repository import DownloadRepository
from domain.repositories.user_repository import UserRepository
from infrastructure.database.models import DownloadModel, UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, user: User) -> User:
        stmt = (
            insert(UserModel)
            .values(**asdict(user))
            .on_conflict_do_update(
                index_elements=[UserModel.telegram_id],
                set_={
                    "username": user.username,
                    "first_name": user.first_name,
                    "language_code": user.language_code,
                    "is_blocked": user.is_blocked,
                },
            )
            .returning(UserModel)
        )
        model = (await self._session.execute(stmt)).scalar_one()
        return User(
            model.telegram_id,
            model.username,
            model.first_name,
            model.language_code,
            model.is_blocked,
            model.created_at,
        )

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        model = (
            await self._session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
        ).scalar_one_or_none()
        return (
            None
            if model is None
            else User(
                model.telegram_id,
                model.username,
                model.first_name,
                model.language_code,
                model.is_blocked,
                model.created_at,
            )
        )


class SqlAlchemyDownloadRepository(DownloadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, download: Download) -> Download:
        model = DownloadModel(
            user_id=download.user_id,
            source_url=download.source_url,
            title=download.title,
            status=download.status.value,
            file_size=download.file_size,
        )
        self._session.add(model)
        await self._session.flush()
        return Download(
            model.id,
            model.user_id,
            model.source_url,
            model.title,
            DownloadStatus(model.status),
            model.file_size,
            model.created_at,
        )

    async def list_by_user(self, telegram_id: int, *, limit: int, offset: int) -> list[Download]:
        rows = (
            await self._session.execute(
                select(DownloadModel)
                .where(DownloadModel.user_id == telegram_id)
                .order_by(DownloadModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars()
        return [
            Download(
                row.id,
                row.user_id,
                row.source_url,
                row.title,
                DownloadStatus(row.status),
                row.file_size,
                row.created_at,
            )
            for row in rows
        ]
