#!/bin/sh
# Run on m75q. Builds the standalone USB endpoint; never flashes a device.
set -eu
container=${EMBER_BUILD_CONTAINER:-amsat-dev-x86}
workspace=${EMBER_CONTAINER_WORKSPACE:-/workspace/MSU_Cubesat/ember}
sdk=${EMBER_PICO_SDK_PATH:-/opt/pico-sdk}
jobs=${EMBER_BUILD_JOBS:-4}
docker exec "$container" cmake -S "$workspace/firmware/usb_bench" \
    -B "$workspace/firmware/usb_bench/build" "-DPICO_SDK_PATH=$sdk" \
    -DPICO_BOARD=pico -DCMAKE_BUILD_TYPE=Release
docker exec "$container" cmake --build "$workspace/firmware/usb_bench/build" -j "$jobs"
