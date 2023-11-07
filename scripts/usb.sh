#!/usr/bin/sh

# leet chars: ┤┤└ └ ┴ ┴ ┐┐│ │┘ ┘┌ ┌ ├ ├ ┬ ┬ ┼ ┼ ┴ ┴ ── ││ ▽▼△▲▵▴▾▿

OUT=$(lsusb)
BUSN=$(echo "$OUT" | awk '{print $2}' | sort -u | wc -l)
DEVICESN=$(echo "$OUT" | wc -l)

USBGUARD_OUTPUT=$(usbguard list-devices)

if [ $DEVICESN -lt 10 ]; then
  FILL=1
elif [ $DEVICESN -lt 100 ]; then
  FILL=2
elif [ $DEVICESN -lt 1000 ]; then
  FILL=3
else
  FILL=4
fi

MAXLEN=0
while read -r line; do
  IFS=' ' read -r -a array <<< "$line"

  DEVICE_NAME=$(echo "$line" | awk '{for(i=7;i<=NF;++i)printf $i""FS;print""}')
  LEN=${#DEVICE_NAME}

  if [ $LEN -gt $MAXLEN ]; then
    MAXLEN=$LEN
  fi
done <<< "$OUT"

i=1
while [ $i -le $BUSN ]; do
  if [ $i -eq 1 ]; then
    :
  else
    echo "│" | awk '{ printf "%109s\n", $0 }'
  fi
  DEVICESN=$(echo "$OUT" | grep "Bus 00$i" | wc -l)

  PRE="┤"
  if [ $i -eq 1 ]; then
    PRE="┬"
  elif [ $i -eq $BUSN ]; then
    PRE="┘"
  fi

  echo "┌── BUS $i ──$PRE" | awk '{ printf "%119s\n", $0 }'

  BUS_DEVICES=$(echo "$OUT" | grep "Bus 00$i")
  DEVICESN=$(echo "$BUS_DEVICES" | wc -l)

  j=1
  while read -r line; do
    IFS=' ' read -r -a array <<< "$line"

    CN_PRE="│"
    if [ $i -eq $BUSN ]; then
      CN_PRE="   "
    fi

    PRE="┤"
    if [ $j -eq $DEVICESN ]; then
      PRE="┘"
    fi

    DEVICE_NAME=$(echo "$line" | awk '{for(i=7;i<=NF;++i)printf $i""FS;print""}')
    DEVICE_NAME="$(printf "%"$MAXLEN"s" "$DEVICE_NAME" | sed -e 's/[[:space:]]*$//')"

    k=$(printf "%0${FILL}d" $j)

    USBGUARD_STATUS=$(echo "$USBGUARD_OUTPUT" | grep "${array[5]}" | awk '{print $2}')

    if [ "$USBGUARD_STATUS" = "allow" ]; then
      USBGUARD_STATUS="allowed"
    else
      USBGUARD_STATUS="blocked"
    fi

    echo "<${array[5]} $DEVICE_NAME $USBGUARD_STATUS> D$k ─$PRE           $CN_PRE" | awk '{ printf "%113s\n", $0 }'
    sleep 0.05

    if [ $j -eq $DEVICESN ]; then
      break
    fi

    j=$((j+1))
  done <<< "$BUS_DEVICES"

  i=$((i+1))
done

exit 0
