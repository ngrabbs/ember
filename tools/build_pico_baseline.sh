#!/bin/sh
# Run on m75q, where the source and SDK are bind-mounted into amsat-dev-x86.
set -eu
container=${EMBER_BUILD_CONTAINER:-amsat-dev-x86}
workspace=${EMBER_CONTAINER_WORKSPACE:-/workspace/MSU_Cubesat/ember}
sdk=${EMBER_PICO_SDK_PATH:-/opt/pico-sdk}
jobs=${EMBER_BUILD_JOBS:-4}

for target in comms ihu; do
    docker exec "$container" cmake \
        -S "$workspace/firmware/$target" \
        -B "$workspace/firmware/$target/build-baseline" \
        "-DPICO_SDK_PATH=$sdk" -DCMAKE_BUILD_TYPE=Release
    docker exec "$container" cmake --build \
        "$workspace/firmware/$target/build-baseline" -j "$jobs"
done
docker exec "$container" python3 "$workspace/test/firmware/test_si5351_probe.py"
