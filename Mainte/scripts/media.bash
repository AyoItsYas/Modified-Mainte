#!/usr/bin/sh

PLAYERS=$(playerctl -l)

if [[ -z "$PLAYERS" ]]; then
  echo "No media playback"
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
    echo "na"
    exit 0
  fi
  LENGTH=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "({{ position }} / {{ mpris:length }})")

  PERCENT=$(echo "scale=2; $LENGTH * 100" | bc -l | awk '{printf "%2.0f", $0}')

  if [[ $1 == "perc" ]]; then
    echo "$PERCENT" && exit 0
  else
    if [[ $ACTIVE_PLAYER == "vlc" ]]; then
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ xesam:url }}")
    else
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }} - {{ artist }}")
    fi

    HASH=$(hash "$NAME")
    MAX_LEN=50
    STEP=1
    SCROLL_INDEX=/tmp/scroll-$HASH

    if [[ ! -f "$SCROLL_INDEX" ]]; then
      echo "0" > $SCROLL_INDEX
    fi

    if [[ ${#NAME} -gt $MAX_LEN ]]; then
      SCROLL=$(cat $SCROLL_INDEX)

      if [[ $SCROLL -gt ${#NAME} ]]; then
        SCROLL=0
      fi

      NAME=$(echo "$NAME" | cut -c "$SCROLL-$((SCROLL + $MAX_LEN))")

      if [[ ${#NAME} -lt $MAX_LEN ]]; then
        NAME=$(printf "%-$MAX_LENs" "$NAME")
      fi

      SCROLL=$((SCROLL + $STEP))
      echo "$SCROLL" > $SCROLL_INDEX
    fi

    META=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "[$NAME] --- {{ duration(position) }} / {{ duration(mpris:length) }}")

    echo "$META | $PERCENT%" && exit 0
  fi
fi