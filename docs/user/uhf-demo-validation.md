# UHF demonstration validation — November 1, 2026

The demonstrated route is Yamcs `ember/realtime` → LibreSDR uplink → COMMS →
IHU → payload CAN → IHU → COMMS → UHF ground receiver. The serial bench bridge
is disabled. COMMS USB opens a bounded window automatically; it does not carry
the command or response. Services start ready and transmit on command.

Deployed integration: IHU 0.15.3, COMMS 0.34.5, fire_uplink 0.1.4, payload 0.5.0.
The coordinated protocol v2 preserves the 16-byte result and adds explicit
UNKNOWN only in ALGORITHM mode. Selected registration quality gates complete
with UNKNOWN; capture faults, corrupt inputs and processing deadlines fail.
No detector threshold or quality gate was weakened. FIRE/NO_FIRE accuracy is
outside this demonstration. See `system/protocols/payload_result_v2.md`.

The rubric target is 35 seconds from ground dispatch to correlated completion,
including setup and decoding, with at most 16 application result bytes.
Three fixed-scene UHF checks completed in 29.418, 29.588 and 28.807 seconds.
Each returned COMPLETED / ALGORITHM / UNKNOWN, 16 application bytes and a
52-byte native ground packet, independently archived on `uhf-tm-in`.
All nine original images decoded at 1456 × 1088 and matched their SHA-256.
The quality reason was REGISTRATION_WEAK_FIT. Configured exposure was 20 ms,
gain 1.0, auto exposure/AWB off; actual per-frame exposure is not recorded.

After a controlled Pi Linux reboot, all four payload/camera services recovered.
A fresh UHF check completed in 29.565 seconds with a new payload boot identity,
without manual HELLO. This is not full-stack cold-power qualification.

Fixes include a seven-second COMMS payload wait, 25-second bounded RF lease
with three-second reply reserve, 20-second ground capture, 29-second arming
observer and strict correlated failure forwarding. The IF decoder tries 1675 Hz and 1325 Hz early, tracks the last CRC-valid IF,
and searches in 25 Hz steps. An actual
failed capture decoded at 1350 Hz in three candidates. Duplicate caches remain
bounded/non-evicting (256 per boot), with cache-full refusal and no auto retry.

Yamcs reports `ember-analysis-result`, `ember-elapsed-ms`, application and native
packet byte counts, payload boot/check identity and processing mode. A command
outcome UNKNOWN/TIMEOUT still fails; it is distinct from an explicit UNKNOWN
analysis result on a COMPLETED report. Payload result.json stores exact generated
reply bytes and source hashes. Ground reception separately proves delivery.

Evidence lives in the EMBER workspace under
`debug-notes/2026-11-01-evidence/uhf-demo/`. Earlier unsuccessful RF/quality and
post-reboot trials remain retained. Full C&DH startup/command/outage qualification
and EPS instrument tests remain pending or blocked by the operator-guide prerequisites.
