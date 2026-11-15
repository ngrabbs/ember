#!/bin/sh
# Install the USB-activated bridge on the provisioned Ground Pi after Yamcs starts.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo on the Ground Pi." >&2
  exit 1
fi
pi_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
ihu_serial=${1:?supply the IHU ID_SERIAL_SHORT from udevadm}
case "$ihu_serial" in
  *[![:alnum:]]*) echo "Invalid IHU USB serial number" >&2; exit 1 ;;
esac
yamcs_network=${2:-ember-ground-starter_default}
bind=$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')
command_network=$(docker network inspect "$yamcs_network" --format '{{(index .IPAM.Config 0).Subnet}}')
python3 -c 'from ipaddress import IPv4Address, IPv4Network; import sys; IPv4Address(sys.argv[1]); IPv4Network(sys.argv[2]); import serial' "$bind" "$command_network"

install -d -m 0755 /opt/ember-bench/ember
for name in payload_bridge.py codec.py dictionary.json eps_bridge.py ltc4162_decode.py ltc4162.json; do
  install -m 0644 "$pi_dir/../ember/$name" "/opt/ember-bench/ember/$name"
done
install -m 0644 "$pi_dir/ember-bench-bridge@.service" /etc/systemd/system/
printf 'BENCH_BIND=%s\nBENCH_COMMAND_NETWORK=%s\nBENCH_DEVICE=%s\n' \
  "$bind" "$command_network" "/dev/serial/by-id/usb-Raspberry_Pi_Pico_${ihu_serial}-if00" \
  > /etc/ember-bench-bridge.conf
printf 'SUBSYSTEM=="tty", KERNEL=="ttyACM[0-9]*", ENV{ID_SERIAL_SHORT}=="%s", TAG+="systemd", ENV{SYSTEMD_WANTS}+="ember-bench-bridge@%%k.service"\n' \
  "$ihu_serial" > /etc/udev/rules.d/99-ember-bench-bridge.rules

systemctl daemon-reload
udevadm control --reload
# Devices already active will not trigger a newly installed SYSTEMD_WANTS.
for device in /dev/ttyACM[0-9]*; do
  [ -c "$device" ] || continue
  if udevadm info -q property -n "$device" | grep -Fxq "ID_SERIAL_SHORT=$ihu_serial"; then
    systemctl restart "ember-bench-bridge@${device##*/}.service"
  fi
done
