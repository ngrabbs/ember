#!/bin/sh
# Run on the Pi from a source export with build_identity.json already supplied.
set -eu
cd "$(dirname "$0")"
test "$(id -u)" = 0 || { echo 'Run with sudo'; exit 1; }
test -f build_identity.json || { echo 'Missing exported build_identity.json'; exit 1; }
id ngrabbs >/dev/null
install -d /opt/ember-payload
install -m 644 protocol.py payload.py can_setup.py VERSION build_identity.json /opt/ember-payload/
install -m 644 systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ember-payload-can.service ember-payload.service
systemctl stop ember-payload.service || true
systemctl restart ember-payload-can.service
systemctl start ember-payload.service
systemctl --no-pager status ember-payload.service
