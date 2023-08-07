#!/bin/bash

#leet chars: ┤┤└ └ ┴ ┴ ┐┐│ │┘ ┘┌ ┌ ├ ├ ┬ ┬ ┼ ┼ ┴ ┴ ── ││ ▽▼△▲▵▴▾▿

OUT=$(playerctl -l)
LENGTH="0"
POSITION="0"

if [[ -z "$OUT" ]]; then
  META="No media playback"
else
  FOUND=0
  for PLAYER in $OUT; do
    if [[ $(playerctl -p "$PLAYER" status) == "Playing" ]]; then
      FOUND=1

      META=$(playerctl -p "$PLAYER" metadata --format "{{ artist }} - {{ title }}")
      break
    fi
  done

  if [[ $FOUND == 0 ]]; then
    META=$(playerctl -p "$PLAYER" metadata --format "{{ artist }} - {{ title }}")
  fi
fi

if [[ $1 == "perc" ]]; then
  LENGTH=$(playerctl -p "$PLAYER" metadata --format "{{ mpris:length }}" | awk '{print $1/1000000}')
  POSITION=$(playerctl -p "$PLAYER" metadata --format "{{ position }}" | awk '{print $1/1000000}')

  PERCENT=$(echo "scale=2; $POSITION / $LENGTH * 100" | bc -l | awk '{printf "%2.0f", $0}')

  echo "$PERCENT"
elif [[ $1 == "player" ]]; then
  echo "$PLAYER"
else
  if [[ -z "$META" ]]; then
    echo "No media playback"
  else
    LENGTH=$(playerctl -p "$PLAYER" metadata --format "{{ mpris:length }}" | awk '{print $1/1000000}')
    POSITION=$(playerctl -p "$PLAYER" metadata --format "{{ position }}" | awk '{print $1/1000000}')

    PERCENT=$(echo "scale=2; $POSITION / $LENGTH * 100" | bc -l | awk '{printf "%2.0f", $0}')

    DURATION=$(playerctl -p "$PLAYER" metadata --format "{{ duration(position) }} / {{ duration(mpris:length) }}")

    echo "$META --- $PERCENT% $DURATION"
  fi
fi

exit 0
