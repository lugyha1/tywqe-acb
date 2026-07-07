from urllib.parse import urlparse

from core.exceptions.base import ValidationAppError

SUPPORTED_HOSTS = (
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "pinterest.",
)


def validate_media_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if parsed.scheme not in {"http", "https"} or not any(item in host for item in SUPPORTED_HOSTS):
        raise ValidationAppError("unsupported media url")
    return value.strip()
