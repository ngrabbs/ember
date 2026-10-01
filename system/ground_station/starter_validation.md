# Yamcs starter validation

[Ground station checklist](TODO.md) · [Run the starter](../../ground/yamcs/README.md)

2026-10-01, m75q x86_64, Docker Compose 5.2.0. Baseline `main` was `ebeec2f`;
starter work is on `feature/ground-station-lab`. Both hosts pulled the merged
baseline and exchange subsequent work through that branch.

| Check | Result |
|---|---|
| Yamcs 5.13.0 starts and instance is available | Pass |
| Laptop browser connects to m75q:8090 | Pass; realtime Home shows recognized `/myproject/Spacecraft` packets at 1 packet/s |
| Telemetry receive count grows | Pass |
| Packet archive returns received packets | Pass |
| Example command is encoded and transmitted | Pass; outbound link count increments |
| Software simulator actually receives command | Pass; its receive counter increments |
| Server restart preserves archive | Pass; a previously recorded packet remains retrievable with the same generation time and sequence number |
| Telemetry and command path recover after server restart | Pass; repeated smoke check succeeds |

The sample test is `SwitchVoltageOn(Battery=1)` in the upstream dictionary.
No voltage is switched: the upstream receiver only counts commands. No spacecraft hardware
was flashed, attached, or commanded; the containers have no radio/device mounts.

This proves the starter deployment and bidirectional software transport. EMBER
ACK/NACK and completion reports, its mission database, Pico wired/RF paths,
full modem resource budget, operator authentication, archive backup,
and plots/replay remain to be exercised. The starter preprocessor uses current
server time; spacecraft timestamps/time quality remain undefined.

Primary browser address: `http://192.168.1.251:8090`. The m75q starter at
`http://192.168.1.252:8090` remains an independent reference instance.

## Dedicated Pi validation

2026-10-01: [Pi 5 / 8 GB inventory](lab_inventory.md), Docker Engine 29.8.2,
Compose 5.5.1, native ARM64 images. `sudo -n id` returns root. The same smoke
checks pass on `192.168.1.251:8090`, including actual simulator command receipt.
The laptop browser opens the Pi's realtime console.

A full Pi reboot was performed. `ember-ground-starter.service` came up without
manual intervention, both containers restarted, the previously recorded packet
remained retrievable with the same timestamp/sequence identity, and the command
and telemetry checks passed again. The service's `active (exited)` state is
expected for the Compose oneshot unit.

After restart, an illustrative idle/simulator snapshot showed 754 MiB host RAM
used and 7.1 GiB available, approximately 418 MiB combined Java RSS (Maven and
Yamcs), temperature 49.4°C and `get_throttled=0x0`. Docker reports memory and swap
limit support unavailable on this OS configuration, so its zero memory counters
are not usable measurements; host memory/RSS were used instead. This is not an
SDR modem load or long-duration cooling/storage benchmark.

Starter source and runtime keys remain local; archive data is in the dedicated
Docker volume. Pi reboot recovery is verified; off-device archive backup,
retention policy, plotting and interactive replay remain open.
