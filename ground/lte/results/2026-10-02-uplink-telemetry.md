# First Walter LTE-M UDP delivery — 2026-10-02

Walter delivered ten numbered 128-byte UDP packets over the LibreSDR/OAI cell
and srsEPC to the ground receiver. Matching run ID and sequences 0–9 were
independently observed inside GTP-U and on SGi. This is a bench demonstration;
connection stability and repeatability remain outstanding.

## Setup

- Reported antenna separation: six to eight feet; Thingy powered down.
- Pi OAI base: `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f` plus six ordered
  [experimental patches](../patches/README.md).
- Profile: `enb.band13.emtc.ce300tx20diag.conf`, band 13, DL 751 MHz / UL 782 MHz,
  50 PRB, single-thread scheduler; logged UHD TX gain 69.75, RX gain 35.
  These are driver settings, not calibrated radiated power.
- Same Walter firmware and serial passthrough; no flashing. PDP context 1,
  APN `srsapn`; UDP 172.16.0.2:51001 → 172.16.0.1:51000.
- `tcpdump` installed on the Pi. Capture began before cell startup, filtering
  UDP ports 2152 and 51000 on all interfaces. Raw logs/pcaps remain private.

## Diagnosis and change

The earlier TX20 trial removed Walter's radio context at 11:20:55.632 UTC,
before its first modem-accepted UDP send at 11:20:57.337. Registration/IP state
therefore did not establish a functioning radio bearer at send time.

The pre-change trace `udp-trace2-20261002` again completed Attach Complete and
RRC Reconfiguration Complete, at 11:32:21.641–642, then removed the context at
11:32:22.124. Walter accepted sequence 0 at 11:32:24.628; the subsequent socket
status query returned `operation not supported`, stopping that trial. The
capture recorded zero matching packets, and the receiver recorded zero.
This trial sent only one packet; missing requested sequences are not a measured
ten-packet loss rate. A preceding `udp-trace-20261002` cell/capture window expired
without the Walter helper running and is excluded from UE comparisons.

Source inspection found a MAC bookkeeping mismatch: the dedicated BL/CE
uplink scheduler and PHY receiver use HARQ process 0, but `rx_sdu` recomputed
the legacy index. Live logs showed process-0 grants followed by process-1/5
receive updates. The sixth patch selects process 0 for known BL/CE templates.
The sender also now treats a completed error from an optional socket-status
query as diagnostic output; pending responses still stop all further commands.

## Telemetry trial: `udp-harq0-20261002`

OAI binary SHA-256:
`9e0e6663013cb5130c03146d23a8f212a50ec037c5e39aa3fab5d6d9253eb977`.

| UTC event | Observation |
| --- | --- |
| 11:35:48.282 | Radio steady-state |
| 11:36:33.614–615 | RRC Reconfiguration Complete; Attach Complete |
| 11:36:34.972 | Initial radio context removed |
| 11:36:36.349 | Modem accepts sequence 0 |
| 11:36:37.315 | Service Request restores bearer; Initial Context Setup Response / Modify Bearer |
| 11:36:37.493 | Ground receives sequence 0 |
| 11:36:50.693 | Ground receives sequence 9 |
| 11:36:51.178 | Sender reports ten accepted sends and socket close |
| 11:36:52.152 | Uplink failure reported after sends / during recovery interval |
| 11:37:04.386 | Walter full standard bands restored; CFUN 0 confirmed |
| 11:38:03.044 / 11:38:07.992 | OAI / EPC exit 124 at bounded deadlines |

Receiver: ten unique packets, sequences 0–9, each 128 bytes, source 172.16.0.2,
zero missing sequences, zero duplicates, zero out-of-order arrivals; receive
span 13.2 seconds. The requested one-second pause plus command/diagnostic time
produced about 1.6-second send spacing. The receiver stops at the tenth unique
packet, so duplicates after that point are not observed. No latency, RTT,
maximum throughput, or long-duration loss measurement is claimed.

Packet capture: 40 recorded packets, zero kernel drops. Thirty GTP-U G-PDUs
included ten matching telemetry payloads; ten SGi packets carried the same
run ID and sequences. The other G-PDUs are not counted as telemetry. There
were no host-generated test sends to the receiver. This confirms the path
Walter → RF → OAI → GTP-U → srsEPC → SGi → ground UDP receiver.

Optional `SQNSS?` worked before the first send, then returned completed
`operation not supported` responses after each send. All ten send commands
still succeeded and their payloads arrived. That status-query error alone
cannot be used as evidence that the socket has failed.

OAI: 38 BR responses, 11 CCCH decodes, two Msg4 ACKs, two RRC Setup Completes,
nine bounded CCCH timeouts; no ULSCH/DLSCH pool exhaustion, missing-dedicated-
config assertion, or other assertion. The initial context release and a later
uplink failure remain unresolved. Recovery reopens the existing passthrough
and resets the modem before CFUN 0; therefore its interval is not a clean
idle-link stability experiment. The result does not isolate the HARQ patch's
effect from variable RF acquisition and timing.

## Validation and next work

The rebuilt target completed. Two MAC CTests completed successfully, including
the production HARQ selector. All six patches reverse/reapply in order and
reconstruct the same candidate files. The older PHY simulator regression is
still unresolved; this MAC change does not qualify the existing PHY patches.

Next: repeat from cold boot without status-query overhead, retain the radio
connection after the packet burst, trace the initial release cause, and test
ground restart/reconnect. Then add downlink acknowledgment and EMBER firmware.
Satellite delay/Doppler and flight qualification remain later work.

Private evidence: Pi `~/work/ember-lte/logs/udp-harq0-20261002-*` and
`~/work/ember-lte/private/udp-harq0-20261002.pcap`; M75q
`~/work/ember-lte/logs/udp-harq0-20261002-walter.log`. The pre-change trial uses
the corresponding `udp-trace2-20261002` names. No subscriber credentials or raw
captures are committed.
