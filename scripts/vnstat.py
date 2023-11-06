#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import json
import subprocess
import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

SCROLL_STEP = 1
SCROLL_INDEX_FILE = os.path.join(CACHE_DIR, "vnstat-scroll.index")

try:
    with open(SCROLL_INDEX_FILE, "r+") as f:
        SCROLL_INDEX = int(f.read()) if os.path.exists(SCROLL_INDEX_FILE) else 0
except Exception:
    SCROLL_INDEX = 0
    with open(SCROLL_INDEX_FILE, "w") as f:
        f.write(str(SCROLL_INDEX))


NOW = datetime.datetime.now()


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


ACTIVE_INTF = get_active_interface()
VNSTAT_DATA = get_data(ACTIVE_INTF)


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


def check_entry(entry: dict) -> bool:
    checks = (
        entry["rx"] > 0 or entry["tx"] > 0,
        entry["date"]["year"] == NOW.year,
        entry["date"]["month"] == NOW.month,
        entry["date"]["day"] == NOW.day,
    )

    return all(checks)


INTF_TRAFFIC_HOURLY: list[dict] = list(
    filter(check_entry, VNSTAT_DATA["traffic"]["hour"])
)


def trim_entry(entry: dict) -> dict:
    return {
        "rx": entry["rx"],
        "tx": entry["tx"],
        "date": entry["date"],
        "total": entry["rx"] + entry["tx"],
    }


DATA = {
    i: trim_entry(x[0])
    if len((x := tuple(filter(lambda x: x["time"]["hour"] == i, INTF_TRAFFIC_HOURLY))))
    > 0
    else None
    for i in range(24)
}
DATA_NO_NONE = {k: v for k, v in DATA.items() if v is not None}

DAILY_TOTAL_RX = sum([x["rx"] for x in DATA.values() if x is not None])
DAILY_TOTAL_TX = sum([x["tx"] for x in DATA.values() if x is not None])

DAILY_TOTAL = DAILY_TOTAL_RX + DAILY_TOTAL_TX

DATA_MAX_ENTRY = max(DATA_NO_NONE, key=lambda x: DATA[x]["total"])
DATA_MIN_ENTRY = min(DATA_NO_NONE, key=lambda x: DATA[x]["total"])


SEC1 = {
    "daily_rx": convert_bytes(DAILY_TOTAL_RX),
    "daily_tx": convert_bytes(DAILY_TOTAL_TX),
    "daily_total": convert_bytes(DAILY_TOTAL),
}

SEC2_SIZE = 6
SEC2_START = SCROLL_INDEX
SEC2_END = SCROLL_INDEX + SEC2_SIZE

SEC2 = {
    "SEC2--size": str(SEC2_SIZE),
    "entries_max": convert_bytes(max([x["total"] for x in DATA_NO_NONE.values()])),
    "entries_min": convert_bytes(min([x["total"] for x in DATA_NO_NONE.values()])),
}


KWARG = {
    "label": f"DAILY TOTAL: {convert_bytes(DAILY_TOTAL)}",
    "heading": "vnstat",
    "interface": ACTIVE_INTF,
    "n_entries": len(INTF_TRAFFIC_HOURLY),
    "entry_freq": "every hour",
    "entries_max_range": "{}:00 - {}:00".format(DATA_MAX_ENTRY, DATA_MAX_ENTRY + 1),
    "entries_min_range": "{}:00 - {}:00".format(DATA_MIN_ENTRY, DATA_MIN_ENTRY + 1),
    "scroll_index": SCROLL_INDEX,
}


LINES = ""
TMP_LINES = """
┌─ < ── {heading} --- {label}
│
└──┬─── interface : {interface}
   │
   ├─┬─ tx        : {daily_tx:>{SEC1--max_len}}
   │ ├─ rx        : {daily_rx:>{SEC1--max_len}}
   │ └─ total     : {daily_total:>{SEC1--max_len}}
   │
   ├─┬─ 24 hour   : {n_entries} entries ({entry_freq}) ~ {SEC2--size} shown @ {scroll_index}
   │ │
   │ ├─ max       : {entries_max:>{SEC2--max_len}} ~ [{entries_max_range}]
   │ ├─ min       : {entries_min:>{SEC2--max_len}} ~ [{entries_min_range}]
   │ │
"""

LINES += TMP_LINES[1:]


SEC2_ROWS = []
for i, (h, ENTRY) in enumerate(DATA.items()):
    if ENTRY is None:
        ENTRY = {"rx": 0, "tx": 0, "total": 0}

    flags = {
        "max": h == DATA_MAX_ENTRY,
        "min": h == DATA_MIN_ENTRY,
        "now": h == NOW.hour,
    }

    flags_str = " ".join([k for k, v in flags.items() if v])

    SEC2_ROWS.append(
        (
            # f"{h:02.0f}:00 - {h+1:02.0f}:00",
            f"{h:02.0f}",
            convert_bytes(ENTRY["rx"], "02.2f"),
            convert_bytes(ENTRY["tx"], "02.2f"),
            convert_bytes(ENTRY["total"], "02.2f"),
            flags_str,
        )
    )


SEC_2_ALIGNERS = (
    lambda x, y: x.ljust(y),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: x.rjust(y + 1),
    lambda x, y: x.rjust(y + 1),
    lambda x, _: x,
)

if len(SEC_2_ALIGNERS) != len(SEC2_ROWS[0]):
    print("SEC_2_ALIGNERS and SEC2_ROWS have different lengths!")
    sys.exit(1)


SEC2_COLS_ALIGNMENT_OFFSETS = [0] * len(SEC2_ROWS[0])

for ROW in SEC2_ROWS:
    for i, ENTRY in enumerate(ROW):
        SEC2_COLS_ALIGNMENT_OFFSETS[i] = max(SEC2_COLS_ALIGNMENT_OFFSETS[i], len(ENTRY))

for i, ROW in enumerate(SEC2_ROWS[SEC2_START : SEC2_END + 1]):
    pre = "├" if i != SEC2_SIZE else "└"

    ROW = [
        a(x, y)
        for a, (x, y) in zip(SEC_2_ALIGNERS, zip(ROW, SEC2_COLS_ALIGNMENT_OFFSETS))
    ]

    LINES += "   │ {}─ i{:02.0f} h{} <R{} S{} T{}> {}\n".format(pre, i, *ROW)

DATA = [trim_entry(x) for x in VNSTAT_DATA["traffic"]["day"][-31:]]

WEEKLY_TOTAL_RX = sum([x["rx"] for x in DATA])
WEEKLY_TOTAL_TX = sum([x["tx"] for x in DATA])

WEEKLY_TOTAL = WEEKLY_TOTAL_RX + WEEKLY_TOTAL_TX

WEEKLY_MAX_ENTRY = max(DATA, key=lambda x: x["rx"] + x["tx"])
WEEKLY_MIN_ENTRY = min(DATA, key=lambda x: x["rx"] + x["tx"])

SEC3 = {
    "weekly_rx": convert_bytes(WEEKLY_TOTAL_RX),
    "weekly_tx": convert_bytes(WEEKLY_TOTAL_TX),
    "weekly_total": convert_bytes(WEEKLY_TOTAL),
}


KWARG.update(
    {
        "n_w_entries": len(DATA),
        "w_entries_max": convert_bytes(WEEKLY_MAX_ENTRY["total"]),
        "w_entries_min": convert_bytes(WEEKLY_MIN_ENTRY["total"]),
        "w_entries_max_range": "{year:0004.0f}-{month:02.0f}-{day:02.0f} - {year:0004.0f}-{month:02.0f}-{day_p:02.0f}".format(
            **WEEKLY_MAX_ENTRY["date"], day_p=WEEKLY_MAX_ENTRY["date"]["day"] + 1
        ),
        "w_entries_min_range": "{year:0004.0f}-{month:02.0f}-{day:02.0f} - {year:0004.0f}-{month:02.0f}-{day_p:02.0f}".format(
            **WEEKLY_MIN_ENTRY["date"], day_p=WEEKLY_MIN_ENTRY["date"]["day"] + 1
        ),
    }
)


TMP_LINES = """
   │
   ├─┬─ 24 HOUR   : {n_w_entries} entries (every 24 hours)
   │ │
   │ ├─ max       : {w_entries_max:>{SEC3--max_len}} ~ [{w_entries_max_range}]
   │ └─ min       : {w_entries_min:>{SEC3--max_len}} ~ [{w_entries_min_range}]
"""

LINES += TMP_LINES[1:-1]

SECTIONS = (SEC1, SEC2, SEC3)

for i, SEC in enumerate(SECTIONS):
    i += 1
    SEC[f"SEC{i}--max_len"] = max([len(x) for x in SEC.values()])

for SEC in SECTIONS:
    KWARG.update(SEC)


KWARG["last_update"] = datetime.datetime.now().strftime("%H:%M:%S")

TMP_LINES = """
   │
   └─── refreshed : {last_update}
"""

LINES += TMP_LINES[:-1]

try:
    print(LINES.format(**KWARG))
except KeyError:
    for LINE in LINES.splitlines():
        try:
            print(LINE.format(**KWARG))
        except KeyError as e:
            print(LINE, f"missing {e}")


SCROLL_INDEX += SCROLL_STEP

if SCROLL_INDEX >= 24 - SEC2_SIZE:
    SCROLL_INDEX = 0

with open(SCROLL_INDEX_FILE, "w") as f:
    f.write(str(SCROLL_INDEX))
