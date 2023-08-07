#!/bin/bash

OUT=$(adb devices -l | grep "model")

if [ -z "$OUT" ]; then
  echo "No device connected"
  exit 0
else
  :
fi

while read -r line; do
  IFS=' ' read -r -a array <<< "$line"

  PRINT="<${array[0]} $(echo "${array[4]}" | tr -d 'model: ')>"
  echo "$PRINT"
  break
done <<< "$OUT"

exit 0
