#!/usr/bin/env python3

from __future__ import annotations

from core import utility

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def get_battery_percentage() -> float | None:
    command = ["acpi", "-b"]

    output = utility.execute(command)

    if output.returncode != 0:
        return

    output = output.stdout.strip().split("\n")[0].split(" ")
    output = tuple(filter(lambda x: "%" in x, output))[0]
    output = output.strip("%,")

    try:
        return int(output)
    except ValueError:
        return None


PALLETTE = ["#FF0000", "#00FF00"]
COLORS = utility.color_gradient_generator(100, PALLETTE)

PERC = get_battery_percentage()

if not PERC:
    print("NA")
    exit(0)

# S = 20
# BAR = "".join(
#     r"${color " + c + r"}" + (" " if (i * (100 / S)) > PERC else "\\#") + r"${color}"
#     for i, c in enumerate(utility.color_gradient_generator(S, PALLETTE))
# )
# BAR = "[" + BAR + "]"

COLOR = COLORS[round(PERC)]
print(r"${color " + COLOR + r"}" + str(PERC) + r"%${color}")
