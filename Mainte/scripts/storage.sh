#!/bin/sh

df "$1" | tail -n 1 | awk '{printf "%4s", $5}'
exit 0
