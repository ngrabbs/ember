# IHU 0.29.1 bench build

[Download the GROUND_TEST / UHF UF2](ihu-0.29.1-ground-test.uf2) for the EMBER
CAN Feather (RP2040). The image was built from
`f4ffe4b9a3a9484f9d18ed8ad5a7f759c0f8c009` with `IHU_UHF_STARTUP=ON`.
The rebased source contains the same firmware and wire dictionary used for
the bench image. Flash readback passed on IHU `DF641455DB822427` at `ember-ground`.

SHA-256
`d6fbb47f3a773acbaf042a829a250ae9dcb44aba19a4215f7b317be182c1a882`

## EPS and GPS overlap

The standard and UHF startup profiles built successfully. During the November
15, 2026 bench run, repeated GPS requests returned 19 fixes. The sensor task
completed five EPS polls between GPS I²C chunks. The maximum interval between
valid EPS samples was 5,022 ms against a 6,500 ms stale limit. The IHU stayed
in NOMINAL / LINK_ACTIVE with zero recorded faults. Scheduled telemetry was off.

Yamcs `REQUEST_STATUS` completed over UHF and returned `eps_valid=1`,
`eps_age_ms=3318`, and boot ID `4059829306`. Yamcs command ID
`1794757147987-ihu-eps-priority-test-1`.

A simulated I²C test covered valid reads, write and read timeouts, bus errors,
and an invalid PEC checksum. The live overlap run did not produce a stale
sample or an I²C failure.

## Yamcs fault history

The flight instance deployment is recorded as [Yamcs 1.7.0](../../../../ground/releases/yamcs-flight-1.7.0.json).

With scheduled telemetry off, a temporary 0.29.0 bench image recorded one
simulated CAN transmit fault. The USB console and Yamcs displayed the same
record. The temporary image was replaced with stock firmware after the test.

| Observation | Result |
| --- | --- |
| Yamcs command ID | `1794756614297-ihu-fault-populated-test-2` |
| Downlink | `uhf-tm-in` |
| Completion | `OK` / `COMPLETED` |
| Fault | `CAN_TX_ERROR` (3) |
| Boot ID | `2804237639` |
| Fault uptime | `29598 ms` |
| Retained faults | 1 |

The first request after a reboot exposed a Yamcs correlation issue. After
the ground fix, the first request from the restored stock boot
`4159351371` completed over UHF and returned zero faults. Yamcs command ID
`1794756751115-ihu-fault-boot-check-3`.
