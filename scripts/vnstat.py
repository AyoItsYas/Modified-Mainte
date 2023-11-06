#!/usr/bin/env python3

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys

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
        print("Error: Unable to get active interface!")
        sys.exit(1)

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
        print("Error: Unable to parse vnstat output!")
        sys.exit(1)


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

HOURLY_TOTAL_RX = sum([x["rx"] for x in DATA_NO_NONE.values()])
HOURLY_TOTAL_TX = sum([x["tx"] for x in DATA_NO_NONE.values()])

HOURLY_TOTAL = HOURLY_TOTAL_RX + HOURLY_TOTAL_TX
HOURLY_AVG = HOURLY_TOTAL / len(DATA_NO_NONE)

DATA_MAX_ENTRY = max(DATA_NO_NONE, key=lambda x: DATA[x]["total"])
DATA_MIN_ENTRY = min(DATA_NO_NONE, key=lambda x: DATA[x]["total"])


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
        "label": f"DAILY TOTAL: {convert_bytes(HOURLY_TOTAL)}",
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

# section 1

SEC1_PLACEHOLDERS = {
    "h_entries_rx": convert_bytes(HOURLY_TOTAL_RX),
    "h_entries_tx": convert_bytes(HOURLY_TOTAL_TX),
    "h_entries_total": convert_bytes(HOURLY_TOTAL),
}

HOURLY_ENTRIES_TO_SHOW = 6
SEC2_START, SEC2_END = HOURLY_SCROLL_INDEX, HOURLY_SCROLL_INDEX + HOURLY_ENTRIES_TO_SHOW

HOURLY_SCROLL_INDEX += HOURLY_SCROLL_STEP
if HOURLY_SCROLL_INDEX >= 24 - HOURLY_ENTRIES_TO_SHOW:
    HOURLY_SCROLL_INDEX = 0

with open(HOURLY_SCROLL_INDEX_FILE, "w") as f:
    f.write(str(HOURLY_SCROLL_INDEX))


# section 2

SEC2_PLACEHOLDERS = {
    "h_entries_avg": convert_bytes(HOURLY_AVG),
    "h_entries_max": convert_bytes(max([x["total"] for x in DATA_NO_NONE.values()])),
    "h_entries_min": convert_bytes(min([x["total"] for x in DATA_NO_NONE.values()])),
    "n_h_entries_to_show": str(HOURLY_ENTRIES_TO_SHOW),
}

SEC2_ROWS = []
for i, (h, ENTRY) in enumerate(DATA.items()):
    if ENTRY is None:
        ENTRY = {"rx": 0, "tx": 0, "total": 0}

    flags = {
        "max": h == DATA_MAX_ENTRY,  # the max data transfer hour
        "min": h == DATA_MIN_ENTRY,  # the min data transfer hour
        "now": h == NOW.hour,  # the current hour
    }

    flags = {
        "MOR": ENTRY["total"] > HOURLY_AVG and not flags["max"],  # more than avg
        "LES": ENTRY["total"] < HOURLY_AVG and not flags["min"],  # less than avg
        **flags,
    }

    flags_str = " ".join([k for k, v in flags.items() if v])

    row = (
        f"{h:02.0f}",
        convert_bytes(ENTRY["rx"], "02.2f"),
        convert_bytes(ENTRY["tx"], "02.2f"),
        convert_bytes(ENTRY["total"], "02.2f"),
        flags_str,
    )

    SEC2_ROWS.append(row)


SEC2_ALIGNERS: tuple[Callable[[str, int], str], ...] = (
    lambda x, y: x.ljust(y),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: f"[{x.center(y + 2)}]" if x != "" else x,
)

if len(SEC2_ALIGNERS) != len(SEC2_ROWS[0]):
    print("SEC2_ALIGNERS and SEC2_ROWS have different lengths!")
    sys.exit(1)


SEC2_COLS_ALIGNMENT_OFFSETS = [0] * len(SEC2_ROWS[0])

for ROW in SEC2_ROWS:
    for i, COL in enumerate(ROW):
        SEC2_COLS_ALIGNMENT_OFFSETS[i] = (
            x
            if (x := len(COL)) > SEC2_COLS_ALIGNMENT_OFFSETS[i]
            else SEC2_COLS_ALIGNMENT_OFFSETS[i]
        )


TMP_LINES = """
┌─ < ── {heading} --- {label}
│
└──┬─── interface : {interface}
   │
   ├─┬─ tx        : {h_entries_tx:>{SEC1--max_len}} ({h_entries_total} / {n_h_entries})
   │ ├─ rx        : {h_entries_rx:>{SEC1--max_len}}
   │ └─ total     : {h_entries_total:>{SEC1--max_len}}
   │
   ├─┬─ 24 hours  : {n_h_entries} entries ({h_entry_freq}) ~ {n_h_entries_to_show} shown @ {scroll_index}
   │ │
   │ ├─ avg       : {h_entries_avg:>{SEC2--max_len}}
   │ ├─ max       : {h_entries_max:>{SEC2--max_len}} ~ [{h_entries_max_range}]
   │ ├─ min       : {h_entries_min:>{SEC2--max_len}} ~ [{h_entries_min_range}]
   │ │
"""
LINES += TMP_LINES[1:]

for i, ROW in enumerate(SEC2_ROWS[SEC2_START : SEC2_END + 1]):
    pre = "├" if i != HOURLY_ENTRIES_TO_SHOW else "└"

    ROW = [
        a(x, y)
        for a, (x, y) in zip(SEC2_ALIGNERS, zip(ROW, SEC2_COLS_ALIGNMENT_OFFSETS))
    ]

    LINES += "   │ {}─ i{:02.0f} h{} <R{} S{} T{}> {}\n".format(pre, i, *ROW)

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
        "m_entries_max": convert_bytes(MONTHLY_MAX_ENTRY["total"]),
        "m_entries_min": convert_bytes(MONTHLY_MIN_ENTRY["total"]),
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

SEC3_PLACEHOLDERS = {
    "weekly_rx": convert_bytes(MONTHLY_TOTAL_RX),
    "weekly_tx": convert_bytes(MONTHLY_TOTAL_TX),
    "weekly_total": convert_bytes(MONTHLY_TOTAL),
}


TMP_LINES = """
   │
   ├─┬─ 31 days   : {n_m_entries} entries (every 24 hours)
   │ │
   │ ├─ max       : {m_entries_max:>{SEC3--max_len}} ~ [{m_entries_max_range}]
   │ └─ min       : {m_entries_min:>{SEC3--max_len}} ~ [{m_entries_min_range}]
   │
   └─── refreshed : {last_update}
"""
LINES += TMP_LINES[1:-1]

SECTIONS = (SEC1_PLACEHOLDERS, SEC2_PLACEHOLDERS, SEC3_PLACEHOLDERS)

for i, SEC in enumerate(SECTIONS, 1):
    # each sections values max len for alignment
    SEC[f"SEC{i}--max_len"] = max([len(x) for x in SEC.values()])

    PLACEHOLDERS.update(SEC)

# final print

try:
    print(LINES.format(**PLACEHOLDERS))
except KeyError as e:
    print(f"missing {e} in the format variables")
