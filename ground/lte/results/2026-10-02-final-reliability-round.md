# Two further reliability trials — 2026-10-02

Two additional identical bounded trials did not complete Walter registration
or submit UDP telemetry. LTE-M integration is being shelved at the user's
request after this round so application telemetry work can proceed. Earlier
ten-of-ten and nine-of-ten received bursts remain demonstrated capabilities;
repeatability remains unresolved.

## Fixed setup

Both runs used the restored, uninstrumented seven-candidate OAI build, SHA-256
`13ab09bf176773e213dd02f950b96577c6369e9be54723e7a1db1281c14b6d8a`, srsEPC,
and `enb.band13.emtc.ce300tx20diag.conf`. Settings stayed Band 13, DL 751 MHz,
UL 782 MHz, 50 PRB, calculated TX gain 69.75 / RX gain 35, single-thread mode,
and the previously reported six-to-eight-foot antenna separation. No firmware,
source, or physical RF changes were made.

For each run, the receiver requested ten packets with a 180-second deadline;
the cell/EPC deadlines were 170/175 seconds. Walter started after the cell's
steady-state report, used a 120-second enable window, requested ten 128-byte
UDP packets, and enabled three bounded pre-prompt retries and a 15-second
settling window. Neither send option was exercised because registration never
triggered socket opening. Serial startup resets the existing ESP/modem
passthrough; these were not verified hardware power-cycle tests.

| Run ID | RAR responses / released contexts | CCCH decodes | Msg4 retries / ACKs | RRC Setup Complete | Modem-accepted / ground-received UDP |
| --- | --- | --- | --- | --- | --- |
| `reliability-a-20261002` | 83 / 83 | 2 | 2 / 2 | 0 | 0 / 0 |
| `reliability-b-20261002` | 59 / 59 | 3 | 1 / 3 | 1 | 0 / 0 |

Walter stayed in searching state (`CEREG: 2,2`) during the polling windows.
Run B decoded RRC Setup Complete at 12:28:44.832 UTC and the EPC received NAS
Security Mode Complete at 12:28:45.271. Neither run logged Attach Complete or
RRC Reconfiguration Complete. No pool-exhaustion, Msg4, or dedicated-config
assertion was observed. Info-level RLC logging does not establish the precise
retry failure checkpoint in these runs; the earlier metadata trace remains
the evidence for missing acknowledgment at the RRC Security Mode Command.

Both receivers recorded zero packets. The ten missing requested sequences are
unsent, not a measured ten-packet radio loss. These two attempts do not provide
a statistically qualified attach success rate or a new telemetry success.

## Shutdown and retained work

Walter restored its full standard band list and confirmed CFUN 0 at
12:27:28.397 UTC (A) and 12:30:44.577 UTC (B). Both eNodeB/EPC pairs exited 124
at their bounded deadlines; B exited at 12:30:47.492 / 12:30:52.459 UTC.
Receivers also completed. No eNodeB or EPC process remained afterward.
No additional reliability changes were made.

Private evidence is retained under `~/work/ember-lte/logs/<run>-oai.log`,
`<run>-epc.log`, and `<run>-receiver.log` on the Pi and `<run>-walter.log` on
the M75q. Configs, source candidates, diagnostics, and the TODO list preserve
the restart point. No packet capture was taken for these two trials.

## Next telemetry milestones

Use the existing EMBER dictionary/codec and Yamcs ingestion as the application
interface. A first useful milestone is decoded, sequenced housekeeping with
visible source provenance and receive time, followed by an archived/replayed
session. Keep simulated, USB hardware, and LTE observations distinguishable.
Then adapt the Walter sender to those shared packets rather than the current
numbered JSON bench payloads, with bounded startup/reconnect behavior. These
are planned milestones, not completed capabilities from this reliability round.

When returning to LTE, resume at the dedicated MPDCCH/PDSCH/HARQ correlation
and clean pinned PHY simulator baseline recorded in the
[RLC trace](2026-10-02-rlc-status.md). Do not treat the earlier short UDP bursts
as sustained-link qualification.
