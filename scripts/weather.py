#!/usr/bin/env python3

import json
import os
import requests
import sys
import time


API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

if not API_KEY:
    print("'OPENWEATHERMAP_API_KEY' environment variable not set")
    exit(0)

CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
CACHE_FILE = os.path.join(CACHE_DIR, "weather.json")
CACHE_TIME = 1200

SCROLL_STEP = 1
SCROLL_FIXED = 5
SCROLL_CHUNK_SIZE = 10
SCROLL_INDEX_FILE = os.path.join(CACHE_DIR, "weather-scroll.index")

LAST_UPDATE = 0
LAST_UPDATE_FRIENDLY = "never"

TIME_NOW = time.time()
TIME_NOW_FRIENDLY = time.strftime("%H:%M:%S", time.localtime(TIME_NOW))


LOCATION = sys.argv[1]

try:
    with open(SCROLL_INDEX_FILE, "r+") as f:
        SCROLE_INDEX = int(f.read()) if os.path.exists(SCROLL_INDEX_FILE) else 0
except FileNotFoundError:
    SCROLE_INDEX = 0
    with open(SCROLL_INDEX_FILE, "w") as f:
        f.write(str(SCROLE_INDEX))


if os.path.exists(CACHE_FILE):
    LAST_UPDATE = os.path.getmtime(CACHE_FILE)
    LAST_UPDATE_FRIENDLY = time.strftime("%H:%M:%S", time.localtime(LAST_UPDATE))


def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={API_KEY}&units=metric"

    request = requests.get(url)
    data = request.json()

    if request.status_code != 200:
        raise Exception(data)

    return data


def get_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={LOCATION}&appid={API_KEY}&units=metric"

    request = requests.get(url)
    data = request.json()

    if request.status_code != 200:
        raise Exception(data)

    return data


if time.time() - LAST_UPDATE > CACHE_TIME:
    data = {"weather": get_weather(), "forecast": get_forecast()}

    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
else:
    with open(CACHE_FILE) as f:
        data = json.load(f)

WEATHER_DATA, FORECAST_DATA = data["weather"], data["forecast"]


def print_data():
    print_array = []

    FORECAST_DATA["list"] = [{"w": w, **x} for w, x in enumerate(FORECAST_DATA["list"])]

    for forecast in FORECAST_DATA["list"]:
        line = (
            f"{forecast['w']:02.0f}",
            f"{forecast['main']['temp']:02.2f}°C",
            forecast["weather"][0]["main"],
            forecast["weather"][0]["description"],
            # time.strftime("%H:%M", time.localtime(forecast["dt"])),
            forecast["dt_txt"],
        )
        line = [str(x) if type(x) is not str else x for x in line]
        print_array.append(line)

    max_len_per_col = [0] * len(print_array[0])

    for line in print_array:
        for i, x in enumerate(line):
            if len(str(x)) > max_len_per_col[i]:
                max_len_per_col[i] = len(str(x))

    print_array_copy = print_array.copy()

    print_array = print_array[:SCROLL_FIXED]
    print_array += print_array_copy[
        SCROLE_INDEX + SCROLL_FIXED : (SCROLE_INDEX + SCROLL_CHUNK_SIZE)
    ]

    if len(print_array) < SCROLL_CHUNK_SIZE:
        print_array += [
            [*x] for x in print_array_copy[: SCROLL_CHUNK_SIZE - len(print_array)]
        ]

    print(
        f"┌─ < ── api.openweathermap.org --- {WEATHER_DATA['weather'][0]['main']} ~ {WEATHER_DATA['weather'][0]['description']}"
        f"\n│"
        f"\n└──┬─── location    : {WEATHER_DATA['name']} {WEATHER_DATA['sys']['country']} ({WEATHER_DATA['coord']['lat']:.2f}, {WEATHER_DATA['coord']['lon']:.2f})"
        f"\n   │"
        f"\n   ├─┬─ temp        : {WEATHER_DATA['main']['temp']:.1f}°C"
        f"\n   │ │"
        f"\n   │ ├─ max         : {WEATHER_DATA['main']['temp_max']:.1f}°C"
        f"\n   │ ├─ min         : {WEATHER_DATA['main']['temp_min']:.1f}°C"
        f"\n   │ └─ feels       : {WEATHER_DATA['main']['feels_like']:.1f}°C"
        f"\n   │"
        f"\n   ├─── humidity    : {WEATHER_DATA['main']['humidity']}%"
        f"\n   ├─── wind speed  : {WEATHER_DATA['wind']['speed']}m/s {WEATHER_DATA['wind']['deg']}°"
        f"\n   │"
        f"\n   ├─── sunset      : {time.strftime('%H:%M:%S', time.localtime(WEATHER_DATA['sys']['sunset' ]))}"
        f"\n   ├─── sunrise     : {time.strftime('%H:%M:%S', time.localtime(WEATHER_DATA['sys']['sunrise']))}"
        f"\n   │"
        f"\n   ├─┬─ forecast    : {len(FORECAST_DATA['list'])} entries (every 3 hours) ~ {SCROLL_CHUNK_SIZE} shown @ {SCROLE_INDEX}"
        f"\n   │ │"
    )

    aligners = (
        lambda x, _: x,  # blank aligner
        lambda x, y: x.ljust(y),  # left alignment for second column
    )

    if len(aligners) < len(max_len_per_col):
        aligners += (lambda x, y: x.rjust(y),) * (len(max_len_per_col) - len(aligners))

    max_len_per_col.pop(0)  # remove index column

    for i, line in enumerate(print_array):
        w = line.pop(0)  # remove index column
        pinned = i < SCROLL_FIXED

        pre = "   │ ├─" if i != SCROLL_CHUNK_SIZE - 1 else "   │ └─"

        if i == SCROLL_FIXED:  # end of fixed section
            print("   │ │")

        info = " ".join(
            [m(x, y) for m, (x, y) in zip(aligners, zip(line, max_len_per_col))]
        )

        print(f"{pre} i{i:02.0f} w{w} <{info}>{' &' if pinned else ''}")

    print(
        f"   │"
        f"\n   ├─── refreshed   : {LAST_UPDATE_FRIENDLY}"
        f"\n   └─── last update : {TIME_NOW_FRIENDLY}"
    )


print_data()

SCROLE_INDEX += SCROLL_STEP

if SCROLE_INDEX >= len(FORECAST_DATA["list"]):
    SCROLE_INDEX = 0

with open(SCROLL_INDEX_FILE, "w") as f:
    f.write(str(SCROLE_INDEX))
