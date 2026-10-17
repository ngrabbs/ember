# EMBER operator displays

Each environment has four operator pages, with the same navigation:

| Page | Purpose |
|---|---|
| `Overview.opi` | Flight: last heartbeat producer, IHU system report and power summary. Bench: serial EPS readout, payload reply and power summary. |
| `EPS.opi` (Power) | Voltages, provisional currents, charger die temperature, readout/ADC quality, raw charger state and JEITA region. |
| `Payload.opi` | Last payload status/heartbeat and ping result; bench-only command/history navigation. |
| `Devices.opi` (Devices & firmware) | IHU discovery snapshot and one fleet firmware table: COMMS, LTE CAN MCU, Walter MCU and payload Pi. |

`Ground-Build.opi` is a separate dated deployment audit, not another operational
dashboard. Native parameter tables keep the detailed diagnostics and plotting
fields: `System.par`, `EPS.par`, `Payload.par`, `Devices.par`, `Firmware.par`,
`Comms.par`, `LTE-Firmware.par` and `Command-reports.par`.

The flight bucket is `ember_displays`; the bench bucket is
`ember_bench_displays`. Navigation retains the selected instance. Both use
`/ember` packet parameters, but current values and archives are independent.
Flight pages have no command actions. The bench Send payload command button
opens the four-command editor; navigation never issues a command itself.

## What a value means

- **NO OBSERVATION / No identity:** no received packet supports the field. Missing
  firmware is not rendered as release `0.0.0` or an all-zero source commit.
- **LAST RECEIVED · CHECK TIME:** heartbeat/system definitions have no expiry.
  A cached ACQUIRED value does not establish current liveness; inspect its
  explicit receive timestamp. This display change does not invent an expiry.
- **PACKET CURRENT:** an observed parameter is still acquired under its existing
  MDB expiry policy. This is packet freshness, not a general device-health verdict.
- **EXPIRED / UNAVAILABLE:** the packet is expired or invalid. Status/measurement
  fields are hidden. Discovery snapshot expiry does not mean every device failed.
- **Firmware expired:** retain the last known release and source commit for
  identification, explicitly mark its release expired, and use `Firmware.par`
  for packet receive timestamps and device boot/observation fields. Identity
  acquisition is not continuous attestation of the currently powered device.

Heartbeat boot ID belongs to that packet's producer (IHU or COMMS), not always
IHU. System mode/configuration are last reported bench states; SAFE and
GROUND_TEST do not prove a flight mode manager is active. Ground-wrapped EPS
header boot identity belongs to the wrapper session, not an IHU reset.

POWER_STATUS measurements are shown only when packet and conversion quality are
valid. EPS readout age is age at packet creation, not ADC conversion age or
current wall-clock age. Current-sense values remain provisional. Charger die
temperature is not battery temperature; no thermistor is fitted on this bench.
The pages send no charger writes. Raw charger-state bits and JEITA region are
available for diagnostics, without inventing a charge-health interpretation.

Device states/ages were sampled by IHU. Planned EPS_NEXT may legitimately be
NOT_SEEN. A payload-ready flag means ready at the last reply; payload status is
requested, not continuously polled. Per-command history owns correlated
outcomes; a last packet on a dashboard cannot establish a command completed.

Times currently represent ground reception. Replay uses the selected processor's
historical time/expiry; the scripts do not compare against laptop wall time.

## Install, retire duplicate pages, and recover

From a clean source checkout:

```sh
python3 ground/yamcs/install_displays.py --url http://192.168.1.251:8090
```

The installer creates both buckets if needed, verifies uploads, and backs up
replaced objects privately under `ground/yamcs/.runtime/display-backups/TIMESTAMP/INSTANCE/`.
After replacement uploads succeed it backs up and removes only the named old
generated pages: `Telemetry.opi`, `LTE.opi`, `Comms-Firmware.opi`,
`LTE-CAN-Firmware.opi`, `LTE-Modem-Firmware.opi` and the duplicate payload build
audit/manifest. Unknown/user-authored objects and telemetry archives are preserved.

Update old bookmarks to Overview, Power or Devices. No compatibility duplicate
pages remain in the display listing. To recover an old page, upload its saved
backup to its original bucket/object path; the verified backup bytes remain
local even after the old object is removed from Yamcs.

`generate_displays.py` builds only the four operator pages and parameter tables.
Its canvas fits beside the Yamcs sidebar at a laptop viewport of 1280×720.
All table parameters derive from the dictionary. Tests verify known bindings,
page bounds, context-preserving navigation, missing identity and stale-value
semantics. Browser inspection verifies actual rendered text and layout.

Publish separate new audits with `build_identity.py --instance ember` and
`--instance ember-bench` after installing the pages. Previous manifests remain
dated evidence; a dashboard cleanup deliberately changes their display hashes.
See [environment deployment and rollback](OPERATIONAL.md).
