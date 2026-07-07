from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DownloadStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


@dataclass(slots=True, frozen=True)
class Download:
    id: int | None
    user_id: int
    source_url: str
    title: str | None
    status: DownloadStatus
    file_size: int | None = None
    created_at: datetime | None = None
