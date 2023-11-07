#!/usr/bin/sh

if [ -f /tmp/radeontop.pid ]; then
  PID=$(cat /tmp/radeontop.pid)

  if [ ! -d /proc/$PID ]; then
    rm /tmp/radeontop.log
    rm /tmp/radeontop.pid
    exit 0
  fi
fi

if [ ! -f /tmp/radeontop.log ]; then
  radeontop -d /tmp/radeontop.log -i 5 &

  echo $! > /tmp/radeontop.pid

  while [ ! -f /tmp/radeontop.log ]; do
    sleep 0.1
  done
fi

if [ $(cat /tmp/radeontop.log | wc -l) -gt 1000 ]; then
  echo "GT"
  echo "" > /tmp/radeontop.log

  while [ ! -f /tmp/radeontop.log ]; do
    sleep 0.1
  done
fi

RADEONTOP_OUTPUT=$(cat /tmp/radeontop.log | tail -n 1)
RADEONTOP_OUTPUT=$(echo $RADEONTOP_OUTPUT | tr "," "\n")

if [ "$1" = "vram" ]; then
  VRAM_DATA=$(echo "$RADEONTOP_OUTPUT" | grep "vram")

  VRAM_USED=$(echo "$VRAM_DATA" | cut -d " " -f 4 )
  VRAM_USAGE=$(echo "$VRAM_DATA" | cut -d " " -f 3)

  VRAM_CLOCK=$(echo "$RADEONTOP_OUTPUT" | grep "mclk" | cut -d " " -f 4)

  echo "$VRAM_CLOCK --- $VRAM_USED / 1024mb - $VRAM_USAGE"
fi

if [ "$1" = "vramperc" ]; then
  VRAM_DATA=$(echo "$RADEONTOP_OUTPUT" | grep "vram")

  VRAM_USAGE=$(echo "$VRAM_DATA" | cut -d " " -f 3 | tr -d "%")

  echo "$VRAM_USAGE"
fi

if [ "$1" = "clock" ]; then
  VRAM_CLOCK=$(echo "$RADEONTOP_OUTPUT" | grep "sclk" | cut -d " " -f 4)

  echo "$VRAM_CLOCK"
fi


if [ "$1" = "temp" ]; then
  SENSOR_DATA=$(sensors)

  LINE=$(echo "$SENSOR_DATA" | grep -n "radeon" | cut -d ":" -f 1)
  LINE=$((LINE + 2))
  LINE=$(echo "$SENSOR_DATA" | sed "${LINE}q;d")

  TEMP=$(echo "$LINE" | cut -d "+" -f 2 | cut -d " " -f 1)
  echo "$TEMP"
fi


exit 0