#!/bin/sh
# Run on ember-ground after UHD installation and image staging.
set -eu
image_dir=${LTE_IMAGE_DIR:-"$HOME/work/ember-lte/images"}
fpga="$image_dir/usrp_b210_fpga.bin"
expected=7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99
actual=$(sha256sum "$fpga" | cut -d ' ' -f 1)
if [ "$actual" != "$expected" ]; then
    echo "Custom FPGA checksum mismatch: $fpga" >&2
    exit 1
fi
if [ ! -f "$image_dir/usrp_b200_fw.hex" ]; then
    echo "Missing USB-controller firmware: $image_dir/usrp_b200_fw.hex" >&2
    exit 1
fi
export UHD_IMAGES_DIR="$image_dir"
exec uhd_usrp_probe --args "type=b200,fpga=$fpga"
