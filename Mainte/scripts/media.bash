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
    ACTIVE_PLAYER_NAME=$PLAYER
    break
  fi
done


if [[ -z "$ACTIVE_PLAYER" ]]; then
  ACTIVE_PLAYER=$(echo "$PLAYERS" | head -n 1)
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
    if [[ $ACTIVE_PLAYER == "vlc" ]]; then
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ xesam:url }}")
    elif [[ $ACTIVE_PLAYER =~ ^(brave|chromium) ]]; then
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }}")
    else
      NAME=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ title }} - {{ artist }}")
    fi

    HASH=$(hash "$ACTIVE_PLAYER")
    MAX_LEN=50

    SCROLL_STEP=1
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

      if [[ $SCROLL -gt ${#NAME} ]]; then
        SCROLL=0
      fi

      SCROLL=$((SCROLL + $SCROLL_STEP))
      echo "$SCROLL" > $SCROLL_INDEX
    fi


    META=$(playerctl -p "$ACTIVE_PLAYER_NAME" metadata --format "$NAME --- {{ duration(position) }} / {{ duration(mpris:length) }}")

    # ART_URL=$(playerctl -p "$ACTIVE_PLAYER" metadata --format "{{ mpris:artUrl }}")
    # ART_URL_HASH=$(hash "$ART_URL")

    # ART_FILE=/tmp/conky-media-art.png

    # if [[ ! -f "$ART_FILE-$ART_URL_HASH" ]]; then
    #   curl -X GET "$ART_URL" --output "$ART_FILE" -s
    # fi

    echo "$META | $PERCENT%" && exit 0
  fi
fi