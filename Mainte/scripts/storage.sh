#!/bin/sh

df "$1" | grep "dev" | awk '{printf "%4s", $5}'
exit 0
