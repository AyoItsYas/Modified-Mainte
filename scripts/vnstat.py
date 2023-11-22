#!/usr/bin/env python3

from __future__ import annotations

import datetime
import json
import os
import subprocess

from core import utility

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, Union

CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

# utility functions


def get_active_interface() -> str:
    # fmt: off
    cmd = ["ip", "route", "get", "1.1.1.1"]                    # command
    prc = subprocess.run(cmd, capture_output=True, text=True)  # process
    # fmt: on

    if prc.returncode != 0:
        utility.error("Error: Unable to get active interface!")

    return prc.stdout.split(" ")[4]


def get_data(interface: str) -> dict:
    # fmt: off
    cmd = ["vnstat", "-h", "-i", interface, "--json"]          # command
    prc = subprocess.run(cmd, capture_output=True, text=True)  # process
    # fmt: on

    try:
        data = json.loads(prc.stdout)

        data = list(filter(lambda x: x["name"] == interface, data["interfaces"]))[0]

        return data
    except json.decoder.JSONDecodeError:
        print(prc.stdout)
        utility.error("Error: Unable to parse vnstat output!")


NOW = datetime.datetime.now()
ACTIVE_INTF = get_active_interface()
VNSTAT_DATA = get_data(ACTIVE_INTF)


def check_entry(entry: dict) -> bool:
    checks = (
        entry["rx"] > 0 or entry["tx"] > 0,
        entry["date"]["year"] == NOW.year,
        entry["date"]["month"] == NOW.month,
        entry["date"]["day"] == NOW.day,
    )

    return all(checks)


def trim_entry(entry: dict) -> dict:
    return {
        "rx": entry["rx"],
        "tx": entry["tx"],
        "date": entry["date"],
        "total": entry["rx"] + entry["tx"],
    }


# hourly data

DATA: list[dict] = list(filter(check_entry, VNSTAT_DATA["traffic"]["hour"]))
DATA: dict[int, Union[dict, None]] = {
    i: trim_entry(x[0])
    if len((x := tuple(filter(lambda x: x["time"]["hour"] == i, DATA)))) > 0
    else None
    for i in range(24)
}
DATA_NO_NONE: dict[int, dict] = {k: v for k, v in DATA.items() if v is not None}
DATA_NO_NONE_N = len(DATA_NO_NONE)

HOURLY_TOTAL_RX = sum([x["rx"] for x in DATA_NO_NONE.values()])
HOURLY_TOTAL_TX = sum([x["tx"] for x in DATA_NO_NONE.values()])

HOURLY_TOTAL = HOURLY_TOTAL_RX + HOURLY_TOTAL_TX
HOURLY_AVG = HOURLY_TOTAL / x if (x := len(DATA_NO_NONE)) > 0 else 0

DATA_MAX_ENTRY = max(DATA_NO_NONE, key=lambda x: DATA[x]["total"]) if x > 0 else 0
DATA_MIN_ENTRY = min(DATA_NO_NONE, key=lambda x: DATA[x]["total"]) if x > 0 else 0


# scroll index for hourly data

HOURLY_SCROLL_INDEX_FILE = os.path.join(CACHE_DIR, "vnstat-scroll.index")
HOURLY_SCROLL_STEP = 1  # how many lines to scroll through in a scroll

try:
    with open(HOURLY_SCROLL_INDEX_FILE, "r+") as f:
        HOURLY_SCROLL_INDEX = (
            int(f.read()) if os.path.exists(HOURLY_SCROLL_INDEX_FILE) else 0
        )
except Exception:
    HOURLY_SCROLL_INDEX = 0
    with open(HOURLY_SCROLL_INDEX_FILE, "w") as f:
        f.write(str(HOURLY_SCROLL_INDEX))

# initial variables

LINES, PLACEHOLDERS = "", {}

# section 0

HOUR_RANGE_SKEL = "{:02.0f}:00 - {:02.0f}:00"

PLACEHOLDERS.update(
    {
        "label": f"DAILY TOTAL: {utility.convert_bytes(HOURLY_TOTAL)}",
        "heading": "vnstat",
        "interface": ACTIVE_INTF,
        "n_h_entries": len(DATA_NO_NONE),
        "h_entry_freq": "every hour",
        "h_entries_max_range": HOUR_RANGE_SKEL.format(
            DATA_MAX_ENTRY, DATA_MAX_ENTRY + 1
        ),
        "h_entries_min_range": HOUR_RANGE_SKEL.format(
            DATA_MIN_ENTRY, DATA_MIN_ENTRY + 1
        ),
        "scroll_index": HOURLY_SCROLL_INDEX,
    }
)

HOURLY_SCROLL_SIZE = 10
SEC1_START, SEC1_END = HOURLY_SCROLL_INDEX, HOURLY_SCROLL_INDEX + HOURLY_SCROLL_SIZE
HOURLY_SCROLL_INDEX += HOURLY_SCROLL_STEP
if HOURLY_SCROLL_INDEX >= 24 - HOURLY_SCROLL_SIZE:
    HOURLY_SCROLL_INDEX = 0

with open(HOURLY_SCROLL_INDEX_FILE, "w") as f:
    f.write(str(HOURLY_SCROLL_INDEX))


# section 1

SEC1_PLACEHOLDERS = {
    "h_entries_rx": utility.convert_bytes(HOURLY_TOTAL_RX),
    "h_entries_tx": utility.convert_bytes(HOURLY_TOTAL_TX),
    "h_entries_max": utility.convert_bytes(
        max([x["total"] for x in DATA_NO_NONE.values()])
    )
    if len(DATA_NO_NONE) > 0
    else "0",
    "h_entries_min": utility.convert_bytes(
        min([x["total"] for x in DATA_NO_NONE.values()])
    )
    if len(DATA_NO_NONE) > 0
    else "0",
    "h_entries_avg": utility.convert_bytes(HOURLY_AVG),
    "h_entries_total": utility.convert_bytes(HOURLY_TOTAL),
    "n_h_entries_to_show": str(HOURLY_SCROLL_SIZE),
}

COLORS = utility.color_gradient_generator(
    len(DATA_NO_NONE),
    ["#dddddd", "#eee36f", "#ffe900", "#ffb000", "#ff7700", "#ff3c00"],
)
GROWTH_DATA = {
    h: color
    for h, color in zip(
        map(
            lambda x: x[0],
            sorted(DATA_NO_NONE.items(), key=lambda x: x[1]["total"]),
        ),
        COLORS,
    )
}


SEC1_ROWS = []
for i, (h, ENTRY) in enumerate(DATA.items()):
    color = ""
    if ENTRY is None:
        ENTRY = {"rx": 0, "tx": 0, "total": 0}
        color = ""
    elif ENTRY is not None and i in GROWTH_DATA:
        color = GROWTH_DATA[i]

    flags = {
        "max": h == DATA_MAX_ENTRY,  # the max data transfer hour
        "min": h == DATA_MIN_ENTRY,  # the min data transfer hour
    }

    flags = {
        "RX": ENTRY["rx"] > ENTRY["tx"],  # more rx than tx
        "TX": ENTRY["tx"] > ENTRY["rx"],  # more tx than rx
        "MOR": ENTRY["total"] > HOURLY_AVG and not flags["max"],  # more than avg
        "LES": ENTRY["total"] < HOURLY_AVG and not flags["min"],  # less than avg
        **flags,
    }

    flags_str = ",".join([k for k, v in flags.items() if v])

    row = (
        f"{h:02.0f}",
        utility.convert_bytes(ENTRY["rx"], "02.2f"),
        utility.convert_bytes(ENTRY["tx"], "02.2f"),
        utility.convert_bytes(ENTRY["total"], "02.2f"),
        flags_str,
        color,
    )

    SEC1_ROWS.append(row)


SEC2_ALIGNERS: tuple[Callable[[str, int], str], ...] = (
    lambda x, y: x.ljust(y),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: f"({x.center(y + 2)})" if x != "" else x,
)


SEC2_COLS_MAX_LEN = [0] * len(SEC1_ROWS[0])

for ROW in SEC1_ROWS:
    for i, COL in enumerate(ROW):
        if (x := len(COL)) > SEC2_COLS_MAX_LEN[i]:
            SEC2_COLS_MAX_LEN[i] = x


# monthly data

DATA = [
    trim_entry(x)
    for x in VNSTAT_DATA["traffic"]["day"]
    if x["date"]["month"] == NOW.month and x["date"]["year"] == NOW.year
]

MONTHLY_TOTAL_RX = sum([x["rx"] for x in DATA])
MONTHLY_TOTAL_TX = sum([x["tx"] for x in DATA])

MONTHLY_TOTAL = MONTHLY_TOTAL_RX + MONTHLY_TOTAL_TX

MONTHLY_MAX_ENTRY = max(DATA, key=lambda x: x["rx"] + x["tx"])
MONTHLY_MIN_ENTRY = min(DATA, key=lambda x: x["rx"] + x["tx"])

DATE_RANGE_SKEL = "{year:0004.0f}-{month:02.0f}-{day:02.0f} - {year:0004.0f}-{month:02.0f}-{day_y:02.0f}"

PLACEHOLDERS.update(
    {
        "n_m_entries": len(DATA),
        "m_entries_max_range": DATE_RANGE_SKEL.format(
            **MONTHLY_MAX_ENTRY["date"], day_y=MONTHLY_MAX_ENTRY["date"]["day"] + 1
        ),
        "m_entries_min_range": DATE_RANGE_SKEL.format(
            **MONTHLY_MIN_ENTRY["date"], day_y=MONTHLY_MIN_ENTRY["date"]["day"] + 1
        ),
        "last_update": datetime.datetime.now().strftime("%H:%M:%S"),
    }
)

# section 3

SEC2_PLACEHOLDERS = {
    "m_entries_rx": utility.convert_bytes(MONTHLY_TOTAL_RX),
    "m_entries_tx": utility.convert_bytes(MONTHLY_TOTAL_TX),
    "m_entries_max": utility.convert_bytes(MONTHLY_MAX_ENTRY["total"]),
    "m_entries_min": utility.convert_bytes(MONTHLY_MIN_ENTRY["total"]),
    "m_entries_avg": utility.convert_bytes(MONTHLY_TOTAL / len(DATA)),
    "m_entries_total": utility.convert_bytes(MONTHLY_TOTAL),
}

# section placeholders

SECTIONS = (SEC1_PLACEHOLDERS, SEC2_PLACEHOLDERS)

for i, SEC in enumerate(SECTIONS, 1):
    SEC[f"SEC{i}--max_len"] = max([len(x) for x in SEC.values() if type(x) is str])

    PLACEHOLDERS.update(SEC)

# final print

LINES += """
┌─ < ── {heading} --- {label}
│
└──┬─── interface : {interface}
   │
   ├─┬─ 24 hours  : {n_h_entries} entries ({h_entry_freq}) ~ {n_h_entries_to_show} shown @ {scroll_index}
   │ │
   │ ├─ max       : {h_entries_max:>{SEC1--max_len}} ~ [{h_entries_max_range}]
   │ ├─ min       : {h_entries_min:>{SEC1--max_len}} ~ [{h_entries_min_range}]
   │ ├─ avg       : {h_entries_avg:>{SEC1--max_len}} = ({h_entries_total} / {n_h_entries})
   │ ├─ total     : {h_entries_total:>{SEC1--max_len}} = (TX {h_entries_tx} + RX {h_entries_rx})
   │ │
"""

# printing the hourly data growth

TMP_LINE = " ".join(
    r"${{color " + color + r"}}" + f"H{h:02.0f}" + r"${{color}}"
    for h, color in GROWTH_DATA.items()
)
LINES += "   │ ├─ growth    : " + TMP_LINE

LINES += """
   │ │
"""

# printing the hourly data table

PINNED = [
    SEC1_ROWS[DATA_MAX_ENTRY],
    SEC1_ROWS[NOW.hour],
    SEC1_ROWS[DATA_MIN_ENTRY],
]  # pinning the max, current and min data transfer hours
PINNED_N = len(PINNED)

LINE_DATA = PINNED + SEC1_ROWS[SEC1_START + (PINNED_N - 1) : SEC1_END]
LINE_DATA_N = len(LINE_DATA)

for i, ROW in enumerate(LINE_DATA):
    lf_first, lf_last = i == 0, i == LINE_DATA_N - 1

    pre = "├" if i != HOURLY_SCROLL_SIZE else "└"
    is_pinned = i < PINNED_N

    if i == PINNED_N:
        LINES += "   │ │" + "\n"
        pass

    color = ROW[-1]
    ROW = [a(x, y) for a, (x, y) in zip(SEC2_ALIGNERS, zip(ROW, SEC2_COLS_MAX_LEN))]

    LINES += "   │ {}─ i{:02.0f} h{} <RX{} + TX{} = TOT{}> {} {pin_flag}".format(
        pre,
        i,
        *ROW,
        color=r"${{color " + color + r"}}",
        color_reset=r"${{color}}",
        pin_flag="&" if is_pinned else "",
    )
    LINES += "\n" if not lf_last else ""

LINES += """
   │
   ├─┬─ 31 days   : {n_m_entries} entries (every 24 hours)
   │ │
   │ ├─ max       : {m_entries_max:>{SEC2--max_len}} ~ [{m_entries_max_range}]
   │ ├─ min       : {m_entries_min:>{SEC2--max_len}} ~ [{m_entries_min_range}]
   │ ├─ avg       : {m_entries_avg:>{SEC2--max_len}} = ({m_entries_total} / {n_m_entries})
   │ └─ total     : {m_entries_total:>{SEC2--max_len}} = (TX {m_entries_tx} + RX {m_entries_rx})
   │
   └─── refreshed : {last_update}
"""

# rendering the output

try:
    print(LINES.format(**PLACEHOLDERS))
except KeyError as e:
    print(f"Missing {e} in the format variables")
