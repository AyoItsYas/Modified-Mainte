#!/usr/bin/env sh

format_bytes() {
    awk '
        function human(x) {
            if (x<1000) {return x} else {x/=1024}
            s="MGTEPZY";
            while (x>=1000 && length(s)>1)
                {x/=1024; s=substr(s,2)}
            return int(x+0.5) " " substr(s,1,1) "iB"
        }
        {sub(/^[0-9]+/, human($1)); print}'
}

if [ "$1" = "val" ]; then
    OUT=$(df "$2" | tail -n 1)

    PERC=$(echo "$OUT" | tail -n 1 | awk '{printf "%3s", $5}')
    USED=$(echo "$OUT" | tail -n 1 | awk '{printf "%3s", $3}' | format_bytes)
    SIZE=$(echo "$OUT" | tail -n 1 | awk '{printf "%3s", $2}' | format_bytes)

    echo "$USED / $SIZE | $PERC"
    exit 0
elif [ "$1" = "perc" ]; then
    df "$2" | tail -n 1 | awk '{printf "%2.0f", $5/1}'
    exit 0
fi
