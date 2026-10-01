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
No voltage is switched: the upstream receiver only counts commands. No hardware
was flashed, attached, or commanded; the containers have no radio/device mounts.

This proves the starter deployment and bidirectional software transport. EMBER
ACK/NACK and completion reports, its mission database, Pico wired/RF paths,
Pi ARM64 deployment and resource budget, operator authentication, archive backup,
and plots/replay remain to be exercised. The starter preprocessor uses current
server time; spacecraft timestamps/time quality remain undefined.

Interim browser address: `http://192.168.1.252:8090`. The selected Pi will replace
this development host after [OS preparation](pi_setup.md).
