from __future__ import annotations

import os
import subprocess

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


def convert_bytes(bytes: int, format_spec: str = ".2f") -> str:
    if bytes < 1024:
        return f"{bytes:{format_spec}}B"
    elif bytes < 1024**2:
        return f"{bytes / 1024:{format_spec}}KB"
    elif bytes < 1024**3:
        return f"{bytes / 1024 ** 2:{format_spec}}MB"
    elif bytes < 1024**4:
        return f"{bytes / 1024 ** 3:{format_spec}}GB"
    elif bytes < 1024**5:
        return f"{bytes / 1024 ** 4:{format_spec}}TB"
    elif bytes < 1024**6:
        return f"{bytes / 1024 ** 5:{format_spec}}PB"
    else:
        return f"{bytes / 1024 ** 6:{format_spec}}EB"


def color_gradient_generator(
    number: int, steps: list[str[7]] = ["#FF0000", "#00FF00", "#0000FF"]
) -> list[str]:
    if number <= 0:
        return []

    points_n = len(steps)
    points_to_generate = number - points_n

    points_per_step = points_to_generate // (points_n - 1)

    if points_per_step == 0:
        points_per_step = 1

    steps = [(tuple(int(step[i : i + 2], 16) for i in (1, 3, 5))) for step in steps]

    gradients = []
    for i in range(points_n - 1):
        lf_first = i == 0

        if lf_first:
            gradients.append(steps[i])

        start, end = steps[i], steps[i + 1]

        increment = tuple((x - y) / points_per_step for x, y in zip(end, start))

        for j in range(points_per_step):
            color = tuple(int(x + y * j) for x, y in zip(start, increment))
            gradients.append(color)

        gradients.append(end)

    while len(gradients) != number:
        if len(gradients) < number:
            gradients.append(steps[-1])
        elif len(gradients) > number:
            gradients.pop(-2)

    gradients = ["#{:02X}{:02X}{:02X}".format(*gradient) for gradient in gradients]

    return gradients


def execute(command: list[str]):
    return subprocess.run(command, capture_output=True, text=True)
