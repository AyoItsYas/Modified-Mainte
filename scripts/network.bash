#!/usr/bin/bash

if [ -f /tmp/ifstat.pid ]; then
  PID=$(cat /tmp/ifstat.pid)

  if [ ! -d /proc/$PID ]; then
    rm /tmp/ifstat.log
    rm /tmp/ifstat.pid
    exit 1
  fi
fi

if [ ! -f /tmp/ifstat.log ]; then
  ifstat > /tmp/ifstat.log &

  echo $! > /tmp/ifstat.pid

  while [ ! -f /tmp/ifstat.log ]; do
    sleep 0.1
  done
fi

IP_OUTPUT=$(ip route get "1.1.1.1" 2>&1)

if [[ $IP_OUTPUT == *"unreachable"* ]]; then
    echo "na"
    exit 0
fi

if [[ $1 == "dns" ]]; then
    DNS=$(cat /etc/resolv.conf | grep "nameserver" | awk '{print $2}')
    echo "$DNS"
    exit 0
fi

if [[ $1 == "gtw" ]]; then
    GATEWAY=$(ip route | grep "default" | awk '{print $3}' | tr "\n" " ")
    GATEWAY=${GATEWAY%?}

    echo "$GATEWAY"
    exit 0
fi

ACTIVE_INTERFACE=$(echo "$IP_OUTPUT" | grep -oP '(?<=dev\s)\w+')

if [[ $1 == "ip" ]]; then
    IFCONFIG_OUTPUT=$(ifconfig "$ACTIVE_INTERFACE")
    PVT_IP=$(echo "$IFCONFIG_OUTPUT" | grep "inet " | awk '{print $2}')
    echo "$PVT_IP"
    exit 0
fi

if [[ $1 == "proxy" ]]; then
    DATA=$(set | grep -i proxy)
    HTTPS_PROXY=$(echo "$DATA" | grep -i HTTPS_PROXY | head -n 1)
    # split the string by '='
    IFS='=' read -ra HTTPS_PROXY <<< "$HTTPS_PROXY"

    if [ ${#HTTPS_PROXY[@]} -ne 2 ]; then
        echo "na"
        exit 0
    fi

    echo "${HTTPS_PROXY[1]}"
    exit 0
fi

INTERFACE_TYPE="eth"
if [[ $ACTIVE_INTERFACE == "wl"* ]]; then
    INTERFACE_TYPE="wlan"
fi

OUTPUT="$ACTIVE_INTERFACE --- $INTERFACE_TYPE"
echo "$OUTPUT"
exit 0