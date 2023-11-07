#!/usr/bin/bash

PLAYERS=$(playerctl -l)

if [[ -z "$PLAYERS" ]]; then
  echo "na"
  exit 0
fi

hash() {
  echo "$1" | md5sum | awk '{print $1}'
}

PLAYERS=$(echo "$PLAYERS" | grep -v "GSConnect")

ACTIVE_PLAYER=""
for PLAYER in $PLAYERS; do
  STATUS=$(playerctl -p "$PLAYER" status)

  if [[ $STATUS == "Playing" ]]; then
    ACTIVE_PLAYER=$PLAYER
    ACTIVE_PLAYER_NAME=$PLAYER
    break
  fi
done

if [[ -z "$ACTIVE_PLAYER" ]]; then
  echo na && exit 0
fi

if [[ $1 == "player" ]]; then
  if [[ $ACTIVE_PLAYER =~ ^(brave) ]]; then
    NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }}")
    WINDOW_ID=$(xdotool search --name "$NAME" | head -n 1)

    if [[ -z "$WINDOW_ID" ]]; then
      ACTIVE_PLAYER_NAME="brave"
    else
      ACTIVE_PLAYER_NAME=$(xdotool getwindowname "$WINDOW_ID" | awk -F ' - ' '{print $1}')
    fi
  fi
  echo "$ACTIVE_PLAYER_NAME" && exit 0
else
  LENGTH=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "({{ position }} / {{ mpris:length }})")

  PERCENT=$(echo "scale=2; $LENGTH * 100" | bc -l | awk '{printf "%2.0f", $0}')

  if [[ $1 == "perc" ]]; then
    echo "$PERCENT" && exit 0
  else
    if [[ $ACTIVE_PLAYER =~ ^(brave|chromium|vlc) ]]; then
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }}")
    else
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }} - {{ artist }}")
    fi

    if [[ -z "$NAME" ]]; then
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ xesam:url }}")
    fi


    HASH=$(hash "$ACTIVE_PLAYER")
    MAX_LEN=50

    if [[ ! -f "/tmp/conky-media-scroll-step" ]]; then
      echo "1" > /tmp/conky-media-scroll-step
    fi

    SCROLL_STEP=$(cat /tmp/conky-media-scroll-step)
    SCROLL_SEP="....."
    SCROLL_INDEX="/tmp/conky-media-scroll-index-$HASH"

    if [[ ! -f "$SCROLL_INDEX" ]]; then
      echo "0" > $SCROLL_INDEX
    fi

    if [[ ${#NAME} -gt $MAX_LEN ]]; then
      SCROLL=$(cat $SCROLL_INDEX)

      NAME="$NAME $SCROLL_SEP $NAME"
      NAME="${NAME:$SCROLL:$MAX_LEN}"
      NAME="[${NAME:0:$MAX_LEN}]"

      STATUS=$(playerctl -p "$ACTIVE_PLAYER" status)
      if [[ $STATUS == "Paused" ]]; then
        SCROLL=$SCROLL
      else
        SCROLL=$((SCROLL + SCROLL_STEP))
      fi

      if [[ $SCROLL -gt ${#NAME} ]]; then
        echo "-1" > /tmp/conky-media-scroll-step
      fi

      if [[ $SCROLL -lt "1" ]]; then
        echo "+1" > /tmp/conky-media-scroll-step
      fi

      echo "$SCROLL" > $SCROLL_INDEX
    fi

    META=$(playerctl -p "$ACTIVE_PLAYER_NAME" metadata --format "$NAME --- {{ duration(position) }} / {{ duration(mpris:length) }}")

    echo "$META | $PERCENT%" && exit 0
  fi
fi