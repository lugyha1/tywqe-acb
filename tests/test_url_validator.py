import pytest

from core.exceptions.base import ValidationAppError
from core.validators.url import validate_media_url


def test_accepts_supported_media_url() -> None:
    assert validate_media_url("https://youtu.be/demo") == "https://youtu.be/demo"


def test_rejects_unsupported_url() -> None:
    with pytest.raises(ValidationAppError):
        validate_media_url("https://example.com/demo")
