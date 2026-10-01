# IHU EPS to Yamcs bench

The [EPS dashboard](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember__realtime)
is live on the Pi. The overview's **EPS dashboard** button opens it.
`EPS.par` provides all raw registers, engineering values, readout age, conversion
assumptions and transport quality. Native parameter history/plotting is available
from the table. [Packet semantics](../protocols/eps_power_status_v1.md) define
what can be treated as current.

## Hardware and service

Keep the IHU UART adapter attached to the Pi at:
`/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0`.
This is 115200 8N1 on IHU GP0/GP1 with a common ground. The existing direct
USB spare Pico remains on its separate `ember-usb-bridge`. The IHU has USB
CDC disabled; the UART adapter is required for this telemetry path. A second
identical adapter may make this non-unique vendor path ambiguous; identify
and configure its physical path before adding another one.

`ember-eps-bridge` is enabled at boot, owns the UART exclusively, and reconnects
the same configured device. It sends only `eps json`; it does not change
quiet mode, ADC controls, charger configuration, JEITA, or charge thresholds.
Stop the service before using an interactive UART console; restart it afterward.
No additional Pico flash or RF hardware is needed.

The ignored `ground/yamcs/.eps.env` on the Pi contains:

```ini
EMBER_EPS_DEVICE=/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0
EMBER_EPS_CELLS=2
EMBER_EPS_RSNSB_OHMS=0.01
EMBER_EPS_RSNSI_OHMS=0.01
```

Fitted sense resistors still need confirmation. This unit deliberately leaves
`sense_values_verified=0`. With pyserial installed and the existing USB-mode
Yamcs setup, install from `ground/yamcs`:

```sh
python3 prepare.py --transport usb
docker compose up -d --force-recreate yamcs
# Wait until /api/instances/ember responds, then:
python3 install_displays.py --url http://192.168.1.251:8090
sudo install -m 644 ember-eps-bridge.service /etc/systemd/system/ember-eps-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now ember-eps-bridge
```

USB-mode Compose publishes EPS UDP 10017 on loopback only. It does not expose
an EPS uplink port. The persistent Yamcs archive volume survives restart and
source/Maven rebuild. To inspect:

```sh
systemctl status ember-eps-bridge
journalctl -u ember-eps-bridge -n 30 --no-pager
```

## Validation — 2026-10-01

Seven EPS host tests cover captured hardware values, signed currents, bounds,
malformed/duplicate-key JSON, incomplete/oversized/split UART lines, ADC/cell
gating, CRC, wire size, timeout/disconnect/reconnect state, XTCE invalid ranges,
expiration and header provenance. All 23 ground tests pass, including existing
C protocol/framing and simulator tests; six LTC4162 host tests also pass.

Live readings around 18:28 UTC: VIN 10.60 V, battery 8.18 V, power-path output
10.56 V, die temperature 24.54 degC. Provisional input current approximately
86–96 mA and battery current approximately -1.5 to -2.8 mA. Raw charger state
32 (NTC pause), JEITA region 7 and ADC-valid 1 agree with the direct readouts.
No actual battery thermistor is fitted; wiring checks remain deferred.

Failure checks temporarily unbound **only** the Prolific UART driver's identified
`3-2:1.0` interface, then rebound it; no power, IHU firmware or spare Pico change:

- UART loss: link DISCONNECTED, current-readout/conversion flags zero,
  engineering values INVALID and hidden on the display. Last good raw words
  retained with increasing readout age.
- Same adapter reattached: exclusive UART reopens automatically; fresh readout,
  LIVE and ACQUIRED engineering values return without service restart.
- EPS bridge stopped: parameters EXPIRED and dashboard STALE; cached numbers
  hidden. REST cached acquisition status alone is insufficient without an
  active subscription requesting expiration updates. Verify freshness through
  an expiration-aware subscription or the native display.
- Bridge restarted: a new wrapper session is allocated and real readouts return.

[API evidence](evidence/eps-yamcs-quality-20261001.json) records these transitions.
A pre-restart POWER_STATUS packet at 18:20:59.045 UTC remained queryable after
the 18:24 Yamcs restart (VIN wire value 10610 mV). The existing Pico HEARTBEAT
flow and archive remain present; its packet-specific boot/uptime bindings match
that Pico instead of the EPS wrapper. Native dashboard layout, status, voltages,
current signs and all six cards were inspected in the laptop browser.

Retention/backups, sense-resistor verification,
thermistor wiring and flight-native packet transport remain separate TODOs.

The native VIN chart was verified through EPS.par → VIN → Chart. Numeric
unavailable sentinels initially polluted its scale despite INVALID status;
a conversion-invalid XTCE context calibrator now maps them to engineering
NaN and plots gaps. The derived parameter archive was rebuilt from preserved
telemetry packets with the realtime parameter filler temporarily disabled to
avoid interval-lock contention, then normal realtime filling was restored.
The rebuilt 15-minute plot shows VIN around 10.4–10.6 V and gaps instead of
million-volt sentinel spikes. Raw packets and raw sentinel values are retained.
