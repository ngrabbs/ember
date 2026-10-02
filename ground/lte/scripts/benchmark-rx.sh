#!/bin/sh
# Receive-only host/USB transport benchmark. Does not transmit samples.
set -eu
image_dir=${LTE_IMAGE_DIR:-"$HOME/work/ember-lte/images"}
fpga="$image_dir/usrp_b210_fpga.bin"
expected=7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99
actual=$(sha256sum "$fpga" | cut -d ' ' -f 1)
[ "$actual" = "$expected" ] || { echo 'Custom FPGA checksum mismatch' >&2; exit 1; }
export UHD_IMAGES_DIR="$image_dir"
exec /usr/libexec/uhd/examples/benchmark_rate \
    --args "type=b200,fpga=$fpga" --duration 10 --rx_rate 15360000 \
    --channels 0 --overrun-threshold 0 --drop-threshold 0 --seq-threshold 0
