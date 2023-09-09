#!/bin/sh

radeontop -d /tmp/radeontop.log -l 1 > /dev/null 2>&1

data=$(cat /tmp/radeontop.log | tr ',' '\n')

if [ "$1" = "vram" ]; then
  echo "$data" | grep "vram" | awk '{print $3}' | awk '{printf "%-4s", $0}'
  exit 0
fi

echo "$data"

rm -f /tmp/radeontop.log
exit 0
