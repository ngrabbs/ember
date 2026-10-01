# EMBER simulated command-loop validation

[Checklist](TODO.md) · [Run the lab](../../ground/yamcs/README.md) · [Contract](../protocols/ember_bench_v1.md)

2026-10-01. Yamcs 5.13.0, `feature/ground-station-lab`, m75q x86_64 and
Raspberry Pi 5 / 8 GB ARM64. Both now run `ember` alongside the original
`myproject` instance. The original named archive volume remains in place.

| Check | Result |
|---|---|
| Generated MDB loads | 31 parameters, five containers, four commands |
| Cross-language command encoding | Java postprocessed packets pass Python CRC/header/payload decoding |
| SET_PARAMETER(1, 1000), acceptance + completion | Pass, matching epoch/transaction and applied value |
| Archived heartbeat cadence at 1000 ms | Pi 1002/1002 ms; m75q 1002/1001 ms |
| SET_PARAMETER(1, 2000), acceptance + completion | Pass, matching epoch/transaction and applied value |
| Archived heartbeat cadence at 2000 ms | Pi 2002/2001 ms; m75q 2001/2002 ms |
| PING | Accepted and completed |
| REQUEST_STATUS | Correlated SYSTEM_STATUS before completion |
| REQUEST_TELEMETRY(COMMS) | Correlated COMM_STATUS before completion |
| Invalid telemetry period (99 ms) | Correlated REJECTED / INVALID_PARAMETER; 2000 ms retained |
| Suppressed results for one PING | Acceptance deadline gives TIMEOUT, outcome UNKNOWN; no automatic retry |
| Browser SET_PARAMETER on Pi | Acceptance OK, outcome COMPLETED, completion SUCCESS |
| Upstream reference on Pi after update | Original smoke test passes; archive and simulator delivery remain available |

Automated checks used `ember_smoke.py --fault-test` on each Docker host;
they restored the original 1000 ms period. The subsequent browser command
left the Pi simulator at **2000 ms**. Its command ID was
`1790857348174-192.168.1.22-0`, ground transaction epoch `645934861`, ID `9`,
IHU boot ID `447153467`. Restarting the simulator creates a new boot ID and
restores the default 1000 ms period.

Thirteen standard-library tests pass: fixed wire vectors, CRC/header/length
rejection, integer bounds, invalid arguments, correlated command results,
duplicate suppression without execution, changed-argument transaction
conflict, unknown-command rejection, cache bound and reset behavior.
Duplicate/reset cases are in-process endpoint tests, not a hardware result.

The browser uses native Yamcs command report/history. Sent is transport only;
EMBER_Acceptance comes from the endpoint and CommandComplete comes from a
correlated terminal packet. Unknown outcomes use TIMEOUT rather than NOK.
The `Resend this command` button starts a new transaction; identity-preserving
retry, pending-history recovery after Yamcs restart and late-result
reconciliation still need work.

No SDR/serial devices are mapped into these containers. Pico parser/handlers,
USB framing/bridge, RF, event persistence, flight authentication and UTC are
not tested. The existing full-Pi-reboot result covers the earlier starter;
this milestone validates the expanded stack after service deployment, not
an additional full Pi reboot. Plotting and interactive replay remain open.
