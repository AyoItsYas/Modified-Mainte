from __future__ import annotations

import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def error(message: str, *, status_code: int = 1) -> None:
    print(message)
    exit(status_code)


def getenv(name: str, default: Any = None, *, required: bool = False) -> str:
    value = os.getenv(name, default)

    if not value and required:
        error(f"'{name}' environment variable not set")

    return value
