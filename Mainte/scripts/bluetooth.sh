#!/bin/sh
# leet chars: ┤┤└ └ ┴ ┴ ┐┐│ │┘ ┘┌ ┌ ├ ├ ┬ ┬ ┼ ┼ ┴ ┴ ── ││ ▽▼△▲▵▴▾▿

OUT=$(bluetoothctl devices | cut -f2 -d' ' | while read uuid; do bluetoothctl info $uuid; done | grep -e "Device\|Connected\|Name" | awk 'ORS=NR%3?",":RS' | tr -d ',' | grep "yes" | awk '{printf "%s %s\n", $2, $5}')

# if output is empty exit
if [ -z "$OUT" ]; then
  echo "- ┴ -" | awk '{ printf "%57s\n", $0 }'
  exit 0
else
  echo "│" | awk '{ printf "%55s\n", $0 }'
fi

DEVICESN=$(echo "$OUT" | wc -l)

MAXLEN=0
while read -r LINE; do
  IFS=' ' read -r -a LINE_ARRAY <<< "$LINE"
  len=${#LINE_ARRAY[1]}
  if [ $len -gt $MAXLEN ]; then
    MAXLEN=$len
  fi
done <<< "$OUT"

BATTERY_FOUND=0
while read -r LINE; do
  IFS=' ' read -r -a LINE_ARRAY <<< "$LINE"

  BATTERY_LEVEL=$(bluetoothctl info ${LINE_ARRAY[0]} | grep "Battery Percentage" | awk '{printf "%6s", $4}' | tr -d '()')

  if [ -z "$BATTERY_LEVEL" ]; then
    :
  else
    BATTERY_FOUND=1
  fi
done <<< "$OUT"

COUNTER=1
while read -r LINE; do
  IFS=' ' read -r -a LINE_ARRAY <<< "$LINE"

  if [ $BATTERY_FOUND -eq 1 ]; then
    BATTERY_LEVEL=$(bluetoothctl info ${LINE_ARRAY[0]} | grep "Battery Percentage" | awk '{print $4}' | tr -d '()')
    if [ -z "$BATTERY_LEVEL" ]; then
      BATTERY_LEVEL="     "
    else
      BATTERY_LEVEL="$BATTERY_LEVEL"
      BATTERY_LEVEL=" $(printf "%0003.0f" "$BATTERY_LEVEL")%"
    fi
  else
    BATTERY_LEVEL=""
  fi

  PRE="┤"
  if [ $COUNTER -eq $DEVICESN ]; then
    PRE="┘"
  fi
  LINE_ARRAY[1]=$(printf "%${MAXLEN}s" "${LINE_ARRAY[1]}")

  echo "<${LINE_ARRAY[0]}$BATTERY_LEVEL ${LINE_ARRAY[1]}> B$COUNTER ─$PRE" | awk '{ printf "%57s\n", $0 }'

  COUNTER=$((COUNTER+1))
done <<< "$OUT"

exit 0