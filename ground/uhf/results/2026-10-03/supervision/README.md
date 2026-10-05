# Optional supervision — October 3, 2026

[Recomputed result](result.json) separates process-control checks from RF delivery.
The final run delivered two fresh native IHU packets (inner9,10), every20 seconds,
byte-identical at IHU/CAN/socket/RF/Yamcs. SDRB streamed63.59 seconds with zero
RX/TX or UDP errors; the ground receiver captured84.03 seconds with no errors or
dropped decode windows. Eight forwarded samples were limited, no telemetry
samples were clipped, and maximum mixed magnitude was0.2519. No HT/SSB observation
or RF-power qualification was added. The old paused EPS display was not advanced.

Seven Linux tests passed using fake children without opening CAN/UHD: exclusive
ownership, normal stop/restart, component failure without retry, parent death and
stale owner, quota shutdown, retention, and finite post-readiness lease. Ground
unit syntax verification passed; SDRB lacks `systemd-analyze`, but its actual unit
loaded and started. Live checks demonstrated manual restart and shutdown after
deliberately terminating the owned CAN forwarder. See [operation](../../../SERVICES.md).

## Preserve unsuccessful attempts

| Run | Outcome |
| --- | --- |
| 1 | Normal SDRB stop; two packets emitted. Ground captured10.6 seconds and decoded zero. |
| 2 | Manual restart followed by deliberate forwarder SIGTERM; SDRB failed/stopped all owned children without retry. Two packets emitted, ground decoded zero. |
| 3 | Ground logout lifetime corrected. SDRB failed during startup: one TX underflow and144 timing events; no IHU timer arm occurred. Supervisor stopped CAN/forwarder without retry. |
| 4 | CAN/forwarder prepared before RF; two fresh packets passed through Yamcs, with clean counters and normal stop. |

The Pi had `Linger=no`: its user manager stopped ten seconds after the last SSH
logout, before the first20-second telemetry period. The journal in
[logout-diagnosis.txt](logout-diagnosis.txt) establishes that cause for runs1/2.
`loginctl enable-linger ngrabbs` fixes that process lifetime; UHF remains disabled
at boot. SDRB's login policy was not changed; its serial shell remains logged in.

Run3's RF fault is separate and its root cause remains open. Preparing passive
CAN/forwarding before GNU Radio and avoiding repeated console status commands
during startup preceded run4's pass. One pass does not prove that either change
eliminates the fault. Preserve this as a restart-reliability task; no automatic
retry, rate/gain sweep or radio/core/image change was introduced.

The attempted `RuntimeMaxSec` runtime property was rejected on both hosts; it
provided no time limit. Run4 used named, finite fallback stop guards alongside
explicit teardown. Mock tests independently verify the CLI's post-readiness
lease. SDRB's wall clock is wrong (2024 run-directory dates); use ground/client
October3 chronology and monotonic durations, not cross-host wall-clock subtraction.

Initial source snapshots are under `tools` with their hashes. Run3 uses that
initial supervisor and the later receiver metadata change. Run4 uses `tools-final`;
both sets retain manifests. Its orchestration/guard and final seven-test log are
also saved. Raw IQ is deliberately absent from persistent mode; packets and logs
are retained. The finite source/control checks are separate from endurance,
arbitrary fault recovery, production firmware and amateur-service qualification.

## Final state and verification

IHU native timer disabled; both UHF services inactive and disabled at boot;
CAN0/1 down after readers closed; SDRB discovery unclaimed; LibreSDR USB free.
Custom FPGA and SDRB radio/mixer hashes match the previous proof. AMSAT checkout
remains clean. Pi account lingering is enabled; SDRB lingering remains disabled.

```sh
python3 ground/uhf/results/2026-10-03/supervision/verify.py
```
