#!/bin/bash

if [ "$1" = "stop" ]; then
    while read -r pid; do
        kill -STOP "$pid" > /dev/null 2>&1
    done < /tmp/conky.pid
fi

if [ "$1" = "continue" ]; then
    while read -r pid; do
        kill -CONT "$pid" > /dev/null 2>&1
    done < /tmp/conky.pid
fi

if [ "$1" = "end" ]; then
    while read -r pid; do
        kill -TERM "$pid" > /dev/null 2>&1
    done < /tmp/conky.pid
fi

if [ "$1" = "kill" ]; then
    while read -r pid; do
        kill -9 "$pid" > /dev/null 2>&1
    done < /tmp/conky.pid
    echo > /tmp/conky.pid
fi

if [ "$1" = "start" ]; then
    killall conky > /dev/null 2>&1
    echo > /tmp/conky.pid
    cd "$HOME/.config/conky/Mainte"
    for file in "$HOME/.config/conky/Mainte/conkyrc-"*; do
        conky -c "$file" > /dev/null 2>&1 & echo $! >> /tmp/conky.pid
    done
fi

if [ "$1" = "restart" ]; then
    bash "$HOME/.config/conky/Mainte/control.sh" kill > /dev/null 2>&1
    bash "$HOME/.config/conky/Mainte/control.sh" start > /dev/null 2>&1
fi

exit 0
