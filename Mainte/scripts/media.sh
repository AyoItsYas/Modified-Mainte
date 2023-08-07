#!/bin/bash

PLAYERS=$(playerctl -l)

if [[ -z "$PLAYERS" ]]; then
  echo "No media playback"
  exit 0
fi

ACTIVE_PLAYER=""
for PLAYER in $PLAYERS; do
  if [[ $(playerctl -p "$ACTIVE_PLAYER" status) == "Playing" ]]; then
    ACTIVE_PLAYER="$ACTIVE_PLAYER"
    break
  fi
done

if [[ -z "$ACTIVE_PLAYER" ]]; then
  ACTIVE_PLAYER=$(echo "$PLAYERS" | head -n 1)
fi

if [[ $1 == "player" ]]; then
  echo "$ACTIVE_PLAYER" && exit 0
else
  if [[ $(playerctl -p "$ACTIVE_PLAYER" status) != "Playing" ]]; then
    echo "No media playback"
    exit 0
  fi
  LENGTH=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "({{ position }} / {{ mpris:length }})")

  PERCENT=$(echo "scale=2; $LENGTH * 100" | bc -l | awk '{printf "%2.0f", $0}')

  if [[ $1 == "perc" ]]; then
    echo "$PERCENT" && exit 0
  else
    if [[ $ACTIVE_PLAYER == "vlc" ]]; then
      META=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ xesam:url }} --- ({{ duration(position) }} / {{ duration(mpris:length) }})")
    else
      META=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }} - {{ artist }} --- {{ duration(position) }} / {{ duration(mpris:length) }}")
    fi

    echo "$META | $PERCENT%" && exit 0
  fi
fi