from domain.entities.user import User
from domain.interfaces.unit_of_work import UnitOfWork


class RegisterUserUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, user: User) -> User:
        async with self._uow as uow:
            result = await uow.users.upsert(user)
            await uow.commit()
            return result
