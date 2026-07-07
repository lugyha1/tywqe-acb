import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app_logging.setup import configure_logging
from config.settings import get_settings
from infrastructure.database.session import create_engine, create_session_factory
from presentation.middlewares.dependencies import DependencyMiddleware
from presentation.middlewares.errors import ErrorMiddleware
from presentation.middlewares.rate_limit import RateLimitMiddleware
from presentation.routers.root import create_root_router


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.debug)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=RedisStorage(redis=redis))
    dp.update.outer_middleware(ErrorMiddleware())
    dp.update.middleware(RateLimitMiddleware(redis, settings.rate_limit_per_minute))
    dp.update.middleware(DependencyMiddleware(session_factory))
    dp.include_router(create_root_router())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
