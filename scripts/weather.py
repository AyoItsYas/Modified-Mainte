#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import requests
import time

from core import utility

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# loading environment variables and other constants

OPENWEATHERMAP_API_KEY = utility.getenv("OPENWEATHERMAP_API_KEY", required=True)
OPENWEATHERMAP_LOCATION = utility.getenv("OPENWEATHERMAP_LOCATION", required=True)

CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
CACHE_FILE = os.path.join(CACHE_DIR, "openweathermap-1.json")
CACHE_TIME = 1200

LAST_UPDATE = 0
LAST_UPDATE_FRIENDLY = "never"

TIME_NOW = time.time()
TIME_NOW_FRIENDLY = time.strftime("%H:%M:%S", time.localtime(TIME_NOW))

# loading scroll index

SCROLL_INDEX_FILE = os.path.join(CACHE_DIR, "openweathermap-scroll.index")

try:
    with open(SCROLL_INDEX_FILE, "r+") as f:
        SCROLL_INDEX = int(f.read()) if os.path.exists(SCROLL_INDEX_FILE) else 0
except Exception:
    SCROLL_INDEX = 0

SCROLL_STEP = 1
SCROLL_SIZE = 10
SCROLL_FIXED = 5

# loading openweathermap data and caching it

if os.path.exists(CACHE_FILE):
    LAST_UPDATE = os.path.getmtime(CACHE_FILE)
    LAST_UPDATE_FRIENDLY = time.strftime("%H:%M:%S", time.localtime(LAST_UPDATE))

if TIME_NOW - LAST_UPDATE > CACHE_TIME:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={OPENWEATHERMAP_LOCATION}&appid={OPENWEATHERMAP_API_KEY}&units=metric"

    request = requests.get(url)
    weather_data = request.json()

    if request.status_code != 200:
        utility.error(weather_data)

    url = f"https://api.openweathermap.org/data/2.5/forecast?q={OPENWEATHERMAP_LOCATION}&appid={OPENWEATHERMAP_API_KEY}&units=metric"

    request = requests.get(url)
    forecast_data = request.json()

    if request.status_code != 200:
        utility.error(forecast_data)

    LAST_UPDATE = TIME_NOW
    LAST_UPDATE_FRIENDLY = time.strftime("%H:%M:%S", time.localtime(LAST_UPDATE))

    OPENWEATHERMAP_DATA = {"weather": weather_data, "forecast": forecast_data}

    with open(CACHE_FILE, "w") as f:
        f.write(json.dumps(OPENWEATHERMAP_DATA))
else:
    with open(CACHE_FILE, "r") as f:
        data = json.loads(f.read())

    OPENWEATHERMAP_DATA = data

# structuring placeholders for the output

PLACEHOLDERS = {
    "_": r"¯\_(ツ)_/¯",
    "main": OPENWEATHERMAP_DATA["weather"]["weather"][0]["main"],
    "description": OPENWEATHERMAP_DATA["weather"]["weather"][0]["description"],
    "time_now": TIME_NOW_FRIENDLY,
    "last_update": LAST_UPDATE_FRIENDLY,
    "name": OPENWEATHERMAP_DATA["weather"]["name"],
    "country": OPENWEATHERMAP_DATA["weather"]["sys"]["country"],
    "lat": OPENWEATHERMAP_DATA["weather"]["coord"]["lat"],
    "lon": OPENWEATHERMAP_DATA["weather"]["coord"]["lon"],
    "n_forecast": len(OPENWEATHERMAP_DATA["forecast"]["list"]),
    "scroll_index": SCROLL_INDEX,
    "scroll_size": SCROLL_SIZE,
}

SEC1 = {
    "temp": OPENWEATHERMAP_DATA["weather"]["main"]["temp"],
    "temp_max": OPENWEATHERMAP_DATA["weather"]["main"]["temp_max"],
    "temp_min": OPENWEATHERMAP_DATA["weather"]["main"]["temp_min"],
    "feels_like": OPENWEATHERMAP_DATA["weather"]["main"]["feels_like"],
}

SEC2 = {
    "humidity": OPENWEATHERMAP_DATA["weather"]["main"]["humidity"],
    "wind_speed": OPENWEATHERMAP_DATA["weather"]["wind"]["speed"],
    "wind_direction": OPENWEATHERMAP_DATA["weather"]["wind"]["deg"],
}

SEC3 = {
    "sunset": time.strftime(
        "%H:%M:%S", time.localtime(OPENWEATHERMAP_DATA["weather"]["sys"]["sunset"])
    ),
    "sunrise": time.strftime(
        "%H:%M:%S", time.localtime(OPENWEATHERMAP_DATA["weather"]["sys"]["sunrise"])
    ),
}

SECTIONS = (SEC1, SEC2, SEC3)

for i, SEC in enumerate(SECTIONS, 1):
    sec_max = max(x for x in SEC.values())
    sec_min = min(x for x in SEC.values())

    SEC[f"sec_{i}_max_len"] = len(str(sec_max))
    SEC[f"sec_{i}_min_len"] = len(str(sec_min))

    PLACEHOLDERS.update(SEC)

# structuring the output

LINES = ""
TMP_LINES = """
┌─ < ── api.openweathermap.org --- {main} ~ {description}
│
└──┬─── location    : {name} {country} ({lat:.2f}, {lon:.2f})
   │
   ├─┬─ temp        : {temp:02.1f}°C
   │ │
   │ ├─ max         : {temp_max:02.1f}°C
   │ ├─ min         : {temp_min:02.1f}°C
   │ └─ feels       : {feels_like:02.1f}°C
   │
   ├─── humidity    : {humidity:>{sec_2_max_len}}%
   ├─── wind speed  : {wind_speed:>{sec_2_max_len}}m/s {wind_direction}°
   │
   ├─── sunset      : {sunset}
   ├─── sunrise     : {sunrise}
   │
   ├─┬─ forecast    : {n_forecast} entries (every 3 hours) ~ {scroll_size} shown @ {scroll_index}
   │ │
"""
LINES += TMP_LINES[1:]  # remove the first newline and add to output

TMP_LINES = ""

items = OPENWEATHERMAP_DATA["forecast"]["list"]
n_items = len(items)

N_COLS = 5
ROWS, COLS_MAX_LEN = [], [0] * N_COLS

for w, forecast in enumerate(items):
    ROW = [
        f"w{w:02.0f}",
        f"{forecast['main']['temp']:02.2f}°C",
        forecast["weather"][0]["main"],
        forecast["weather"][0]["description"],
        forecast["dt_txt"],
    ]
    ROWS.append(ROW)

    for i, (COL, COL_MAX_LEN) in enumerate(zip(ROW, COLS_MAX_LEN)):
        if (x := len(COL)) > COL_MAX_LEN:
            COLS_MAX_LEN[i] = x

SCROLL_INDEX += SCROLL_STEP

if SCROLL_INDEX >= n_items:
    SCROLL_INDEX = 0

items = (
    ROWS[:SCROLL_FIXED] + ROWS[SCROLL_INDEX + SCROLL_FIXED : SCROLL_INDEX + SCROLL_SIZE]
)

if len(items) < SCROLL_SIZE:
    items += ROWS[SCROLL_FIXED : SCROLL_FIXED + (SCROLL_SIZE - len(items))]

n_items = len(items)
for i, ROW in enumerate(items):
    is_first, is_last, is_fixed = i == 0, i == n_items - 1, i < SCROLL_FIXED

    if i == SCROLL_FIXED:
        TMP_LINES += "   │ │\n"

    connector = "├" if not is_last else "└"

    TMP_LINES += f"   │ {connector}─ i{i:02.0f} {ROW[0]:>{COLS_MAX_LEN[0]}} <{ROW[1]:<{COLS_MAX_LEN[1]}} {ROW[2]:<{COLS_MAX_LEN[2]}} {ROW[3]:>{COLS_MAX_LEN[3]}} @ {ROW[4]}>{' &' if is_fixed else ''}\n"


LINES += TMP_LINES  # add the lines to output

TMP_LINES = """
   │
   └─── refreshed   : {time_now} ~ fetched @ {last_update}
"""
LINES += TMP_LINES[1:-1]  # remove the first and last newline and add to output

# rendering the output

print(LINES.format(**PLACEHOLDERS))

# saving the scroll index

with open(SCROLL_INDEX_FILE, "w") as f:
    f.write(str(SCROLL_INDEX))
