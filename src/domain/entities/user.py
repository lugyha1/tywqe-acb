from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class User:
    telegram_id: int
    username: str | None
    first_name: str | None
    language_code: str
    is_blocked: bool = False
    created_at: datetime | None = None
