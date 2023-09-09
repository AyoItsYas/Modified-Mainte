#!/bin/sh

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
    GATEWAY=$(ip route | grep "default" | awk '{print $3}')
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

if [[ $ACTIVE_INTERFACE == *"wlp"* ]]; then
    INTERFACE_TYPE="wln"
elif [[ $ACTIVE_INTERFACE == *"tun"* ]]; then
    INTERFACE_TYPE="vpn"
else
    INTERFACE_TYPE="lan"
fi

OUTPUT="$ACTIVE_INTERFACE --- $INTERFACE_TYPE"
echo "$OUTPUT"
exit 0