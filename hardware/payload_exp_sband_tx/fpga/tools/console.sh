#!/usr/bin/env bash
# Talk to the M0 console on the Arty Z7-20. No dependencies beyond coreutils.
#
#   ./tools/console.sh                 # interactive: type commands, see replies
#   ./tools/console.sh s               # send one command, print the reply
#   ./tools/console.sh -d /dev/ttyUSB1 s
#
# Commands: s=status  p0-3=pattern  r0-3=rate  e/d=enable  z=zero  ?=help
set -euo pipefail

DEV=/dev/ttyUSB0
if [ "${1:-}" = "-d" ]; then DEV="$2"; shift 2; fi
[ -c "$DEV" ] || { echo "no such serial device: $DEV" >&2; exit 1; }

stty -F "$DEV" 115200 cs8 -cstopb -parenb raw -echo -crtscts min 0 time 5

if [ $# -eq 0 ]; then
    echo "connected to $DEV at 115200 8N1 - ctrl-c to quit"
    cat "$DEV" &
    trap 'kill %1 2>/dev/null || true' EXIT
    while IFS= read -r line; do printf '%s' "$line" > "$DEV"; done
else
    exec 3<>"$DEV"
    printf '%s' "$*" >&3
    timeout 2 cat <&3 || true
fi
