from aiogram import Router

from presentation.handlers import callbacks, messages


def create_root_router() -> Router:
    router = Router(name="root")
    router.include_router(messages.router)
    router.include_router(callbacks.router)
    return router
