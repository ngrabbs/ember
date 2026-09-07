#!/usr/bin/env bash
# Build (and optionally program) the M0 bitstream inside the Vivado container.
#
# Runs ON the Vivado host (m75q). The repository's fpga/ directory is bind
# mounted at /work, so the build writes its output straight back into the tree.
#
#   ./vivado/build.sh              # synthesise, implement, write the bitstream
#   ./vivado/build.sh program      # program the board over USB-JTAG
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # the fpga/ directory
XILINX_TREE="${XILINX_TREE:-$HOME/tools/xilinx}"
IMAGE="${VIVADO_IMAGE:-vivado:2024.2}"
SETTINGS=/tools/Xilinx/Vivado/2024.2/settings64.sh

# Vivado ships its own libudev and the system has another. The Xilinx license
# manager calls udev_enumerate_scan_devices, and mixing the two corrupts the
# heap - Vivado aborts with "realloc(): invalid pointer" at the first
# licence-gated step, which is write_bitstream. Preloading the system libudev
# leaves exactly one implementation in play.
PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1

mkdir -p "$HERE/build/vivado"

if [ "${1:-build}" = "program" ]; then
    INNER="export LD_PRELOAD=$PRELOAD && source $SETTINGS && cd /work && (hw_server >/tmp/hw_server.log 2>&1 &) && sleep 3 &&
           vivado -mode batch -nojournal -log build/vivado/program.log -source vivado/program.tcl"
else
    INNER="export LD_PRELOAD=$PRELOAD && source $SETTINGS && cd /work &&
           vivado -mode batch -nojournal -log build/vivado/vivado.log -source vivado/build.tcl"
fi

exec docker run --rm \
  --name ember-vivado \
  -v "${XILINX_TREE}:/tools/Xilinx:ro" \
  -v "${HERE}:/work" \
  -v /dev/bus/usb:/dev/bus/usb \
  --device-cgroup-rule='c 189:* rmw' \
  "${IMAGE}" bash -lc "${INNER}"
