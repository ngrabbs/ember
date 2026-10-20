# LTE-M data-rate test TODO

Updated 2026-10-20. Local plan branch: `docs/lte-throughput-plan`, refreshed from
`origin/main` at `06680f3`. Production IHU firmware remains unchanged.

## Current priority

The bench demonstration and initial rate characterization are complete. Real EPS
telemetry reached the dashboard through the full production chain (best paced
result 3.072 kbps). Direct Walter testing delivered 180/180 packets across three
separate 30-second runs at 8.192 kbps, none late. Original Walter firmware and
the production IHU→COMMS→Walter control link are restored and verified.
Ground patch set is versioned as experimental `ember-lte-m-v0.1.0`.

Rate chasing and reliability debugging are parked. Earlier attach/delivery
failures remain unresolved; maximum rate, long-duration reliability and
spacecraft operation are unqualified. No new RF test is part of this closeout.
See [closeout](results/2026-10-20-direct-pacing-closeout.md).

## Next LTE task — production telemetry endurance and recovery (planned)

- [ ] Use production firmware and real EPS packets through receiver and Yamcs;
  record firmware/config/version, power state and antenna spacing.
- [ ] Start with five bounded sessions, each offering one packet/s for 60 seconds,
  with a 10-second drain and the existing 120-second modem-window limit.
  Require sufficient startup/shutdown headroom; stop at the first unknown outcome
  or failed delivery. This is an initial endurance check, not continuous operation.
- [ ] Record attach time, accepted/received/archived counts, missing/late/duplicate
  packets, CAN errors, resets and final OFF. Keep failed sessions in the results.
- [ ] In a separate bounded test, deliberately stop the ground cell and restore
  it. Observe existing production recovery behavior; record whether manual
  reopening is needed and time to the next verified dashboard packet.
- [ ] Any useful recovery feature gets its own implementation PR and version.
  Do not add test-only logic to production IHU firmware.

## Completed characterization checklist

- [x] Prepare/build isolated `firmware/walter_throughput_bench`; actual engine
  ASan/UBSan checks and3Python protocol/receiver/summary tests pass. Source and
  artifact hashes match. Separate receiver staged on ground; port51002 free,
  no service or RF started. [Preparation](results/2026-10-19-direct-bench-preparation.md).
- [x] Move USB to Walter; identify current application and chip; create two
  matching complete16 MiB restore images and verify local copies before writing.
- [x] Upload temporary image; application flash verification and six OFF-state
  checks pass, source digest matches, zero log drops; no RF window opened.
- [x] Run one bounded 128-byte direct delivery check; 10/10 received, 1.024 kbps.
  Record operator/modem release, final OFF and unchanged ground integrity.
  [Result](results/2026-10-19-direct-walter-smoke.md).
- [x] Qualify 512-byte packets at 1 packet/s: 10/10 received, **4.096 kbps**, zero
  missing/duplicate/late/skipped packets. [Result](results/2026-10-19-direct-walter-512.md).
- [x] Attempt 2 packet/s: registration lost after 3 accepted sends, 0 received; 17 slots
  unreached. 5 packet/s not attempted; no retries.
  [Failure record](results/2026-10-20-direct-walter-rate-sweep.md).
- [x] Compare saved removal logs and source: 2 OK / 58 error scheduled-uplink events
  versus 48 OK / 12 error over equal 1.216 s; signaling retry cleanup is a strong lead,
  not a confirmed cause. [Analysis](results/2026-10-20-direct-release-analysis.md).
- [x] Attempt bounded RLC/RRC-debug capture: USB JSON reader failed during
  configuration; no benchmark started. Independent OFF recovery passed.
  [Capture record](results/2026-10-20-direct-rlc-capture-01.md).
- [x] Fix private host reader: buffer partial lines, preserve raw chunks, bound
  cleanup status retries. Fragmentation tests and 12 live OFF-only statuses passed;
  zero additional RF windows.
- [x] One bounded diagnostic with revised reader: READY16.854s, 20/20 received,
  19 within10s plus1late, **7.7824kbps**. Zero USB parse errors/log drops; OFF and
  all ground integrity checks pass. SRB1 retry event follows OFF; no live failure.
  [Result](results/2026-10-20-direct-rlc-capture-02.md).
- [x] One bounded512-byte5packet/s point:50 accepted,12 received,38 missing;
 4.9152kbps received, no late/skipped/uncertain. OAI crashed during drain on
 `NPRB > 0` / `NPRB == 0` at dci_tools.c:657, radioexit-6. OFF confirmed, ground
 stopped/integrity passed. No retries. [Result](results/2026-10-20-direct-walter-5pps.md).
- [x] Offline crash/source review found reused MPDCCH append pointer across UE
 contexts. Reduced real-header/converter fixture reproduces overwrite/count-hole
 defect; ten cases pass ASan/UBSan. Candidate refreshes pointer before each write,
 saved only—not applied/full-built/RF-tested. Runtime causality remains unconfirmed.
 [Analysis](results/2026-10-20-mpdcch-slot-analysis.md).
- [x] Per user direction, patch/rebuild existing ground checkout. Verified rollback
 snapshot on ground/local; full radio build and3existing MAC/PHY helper tests pass.
 Cache/libraries/prior overlay retained; candidate audit12/12 passed. No RF yet.
 [Build record](results/2026-10-20-mpdcch-slot-build.md).
- [x] Candidate5packet/s comparison:50/50 delivered,29 in10s plus21 late;
 **11.8784kbps**. OAI/EPC both planned124, no crash;12integrity checks pass/OFF.
 Only one completed RRC setup context observed; two-context crash prevention not
 proven. [Result](results/2026-10-20-direct-slot-walter-5pps.md).
- [x] Bounded3packet/s point:30/30 delivered,23 in10s plus7late;9.4208kbps.
 No crash,12integritychecks passed/OFF. Receiver still fell behind offer.
 [Result](results/2026-10-20-direct-slot-walter-3pps.md).
- [x] 512-byte2packet/s30second point:60/60 in window,0late/missing,8.192kbps,
 no crash;12integritychecks passed/OFF. Admission had103.445s remaining versus46s
 required. [Result](results/2026-10-20-direct-slot-walter-2pps30.md).
- [x] Both matching2packet/s30second repeats passed:180/180 across all3points,
 8.192kbps each,0late/missing. No more benchmark RF runs.
 [Closeout](results/2026-10-20-direct-pacing-closeout.md).
- [x] Restore original16MiB Walter image; full verification, original0.3.0
 USB identity and OFF passed. No RF during restoration.
- [x] Read-only production IHU→COMMS→Walter identity/OFF check passed October20 local.
 Renewed stale peer session; final check had unchanged CAN errors/output permissions.
 No flashing or RF command.
 Earlier missing-delivery causes remain open; best ten-second burst11.8784kbps unchanged.
- [x] Original Walter image restored; USB and production IHU path checks complete.

## Setup

- [x] Use split source directories: `firmware/ihu`, `firmware/walter_mcu`,
  `firmware/walter`.
- [x] Console host and ground-station host identified; private addresses retained locally.
  Ground EMBER/OAI have local changes; preserve them.
- [x] Recover IHU USB with targeted USB2 hub reset; backup SSD stayed connected.
  One console cable is currently on IHU; keep other boards powered when moving it.
- [x] Record installed identities: IHU **0.15.0**, clean `701e96c`; Walter MCU
  **0.8.0**, Walter ESP32 **0.3.0**, both clean `9fcb020`.
  Do not downgrade IHU to match main's older version.
- [x] Record LibreSDR/UHD/FPGA and binary hashes in lab-log entry 005 setup file.
- [x] Confirm RF: stock LibreSDR antennas all fitted; Walter full-band LTE
  698–960 / 1710–2690 MHz antenna; **1 m separation, over the air**.
  Band 13 DL 751/UL 782 MHz, 50 PRB; `enb.band13.emtc.ce300tx20diag.conf`.
  Config TX/RX gains 90/110, attenuation 20/30; not calibrated RF power.
- [x] EPS responds; **battery disconnected**. Near-zero VBAT is expected.
- [x] Use existing receiver and Yamcs `ember` / `lte-tm-in`; no second listener.
- [x] Read actual Sequans radio release with `AT+CGMR`: `UE8.2.1.0`.
  Registered operator reply: `+COPS: 1,2,"99970",7`.

## Tests

- [x] Baseline: one fresh 128-byte EPS packet, exact bytes in receiver and Yamcs.
- [x] First full-path point: EPS → IHU → CAN → Walter MCU → UART → Walter →
  LTE-M → LibreSDR → receiver/Yamcs. **30/30 packets in a 30-second 1 packet/s
  run: 1.024 kbps**. Zero missing, duplicate, late or skipped packets/slots.
  This is one paced result, not maximum throughput.
- [x] Repeat 1 packet/s twice: all three runs passed, 90/90 received,
  zero missing/duplicates/skips; 1.024 kbps in every 30-second run.
- [x] Try 2 and 5 packet/s. Two complete runs at each rate delivered 60/60 and
  84/84 packets respectively: **2.048 / 2.8672 kbps**. At requested 5 packet/s,
  each working run skipped 66 slots while waiting for prior command completion.
- [ ] Finish the remaining complete repeats after fixing session bring-up:
  one 2 packet/s attempt and one 5 packet/s attempt accepted 45 and 60 packets
  respectively, but delivered **zero**, with registration loss / Walter NOT_READY. Root cause open.
  All ten attempts (including one local SENSOR_BUSY interruption) are in lab-log.
- [x] Run four one-packet fresh-session probes: 4/4 receiver/Yamcs matches and
  no registration drop during 35 seconds of observations per session.
- [x] Compare earlier failed/working active intervals: failures had no decoded
  scheduled uplink or uplink data-channel messages; working reference did.
- [ ] Diagnose the UE/eNodeB scheduled uplink path; exact RF/scheduling cause
  remains open. Add a delivery gate before future rate measurements.
- [x] Reconnect HackRF and qualify receive-only acquisition with zero overruns.
- [x] Record three valid receive-only RF observations: 205/205 telemetry packets
  received; zero RX overruns/clipping. Retune control 782→781 MHz recorded.
- [x] Establish a working RF reference at 780.38 MHz: HackRF 2 MS/s, 1.75 MHz
  filter, LNA 24 / VGA 16 dB, amplifier/antenna power off. The first higher-gain
  working run showed data-band p99 power −38.99 dBFS during sends versus −48.43
  after shutdown, with zero overruns/clipping. Relative power only; no LTE decode
  or demonstrated individual grant alignment.
- [ ] Capture the earlier accepted-but-undelivered failure with the same observer
  settings and compare it with a working reference. Its cause remains unresolved.
- [x] Three narrow-band runs delivered 60/60, 87/87 and 81/81 packets to receiver
  and Yamcs (228/228); zero duplicates/loss/late arrivals, overruns or clipping.
  The higher-gain repeat also showed activity above the quiet reference. No
  accepted-but-undelivered failure reproduced in the first ten follow-up sessions;
  root cause remains open. Best completed result now **3.072 kbps**; this host path is still
  paced by one request at a time, not a modem maximum.
- [x] Fresh-session repeat: 90/90 packets in 30 seconds (**3.072 kbps**), followed
  by a registration timeout with zero telemetry attempted. Stopped after two of
  three planned sessions; both captures have zero overruns/clipping.
- [ ] Investigate the captured registration failure: CEREG 2/searching after 90 s;
  eNodeB had 40 unsuccessful Msg3 events and no successful Msg3; core no attach
  request. RF bursts are present near the inferred Msg3 allocation, but waveform,
  transmitter identity and subframe alignment are unverified. Keep this distinct
  from the original accepted-but-undelivered failures.
- [x] Qualify capped receive-only IQ capture and cyclic-prefix analysis. Two
  fresh sessions delivered 114/114 accepted packets; six additional offers were
  refused locally with SENSOR_BUSY. IQ retained: 0.8 / 6.0 MB; zero overruns or
  clipping. Both ended OFF with unchanged IHU firmware/boot, outputs and CAN.
- [x] Run 2 logged 16 unsuccessful Msg3 events before one nonempty Msg3 CCCH
  indication and eventual READY. Bursts show normal-CP consistency; no payload
  decode, transmitter identification or verified eNodeB subframe alignment.
- [x] Check source: “No signal in Msg3” tests missing/all-zero decoded bytes,
  not measured RF absence. Do not use that label as an RF detector.
- [ ] Match PRACH/RAR/Msg3 events against IQ; include the preamble band if needed.
  Lower the recording trigger for weaker successful bursts without changing TX
  settings or removing the file-size cap. No timing/decoder fix is established.
- [x] Capture PRACH (~778.4 MHz) and 2-PRB Msg3 (~780.02 MHz) together:
  HackRF 779.1 MHz / 5 MS/s / 2.5 MHz filter; LNA/VGA 16/8 and 24/0 dB.
  Both runs delivered 60/60 packets at 2.048 kbps, zero overruns/clipping.
  First run logged 18 Msg3 errors before success; four qualified temporal pairs
  were 12.9–13.0 ms apart on the same sample clock. Weak successful-access
  template fit gives ~13.1 ms conditionally; no absolute SFN alignment or fix.
  Details: local lab-log entry 006, linked from entry 005.
- [ ] Match preamble/RAR/Msg3 identity and receive context; inspect eNodeB
  samples/frequency correction/DMRS/decode settings for failed versus good Msg3.
- [x] Join 20 saved generated RARs to MAC callbacks: temporary identities and
  +6-subframe scheduled Msg3 targets match; all use NB 2 / two RBs / MCS 7.
  Failed Msg3 PHY contexts are missing from those older logs; no fix established.
- [x] Capture one successful Msg3 PHY reference using a copied PHY-debug profile:
  matching identity/target, HARQ 0, RB 13 + two RBs, QPSK, TBS 224 bits, RV 0.
  One config-only failed launch opened no cell/modem window and was corrected.
- [x] Preserve subsequent zero-delivery session: 45 accepted, 0 receiver/Yamcs,
  five local refusals, one explicit NOT_READY rejection, no unknown send outcomes.
  CEREG 4 / one registration drop; incomplete window, no rate result. Stopped
  repeats. Verbose logging affects real-time load; common cause remains unproven.
- [ ] Inspect saved post-attach PUSCH decode failures/retransmissions and grant/
  DMRS context before another RF run. Use selective logging if new evidence is
  needed; keep the original profile as default and preserve dirty OAI sources.
- [x] Compare saved working and three zero-delivery sessions: all failed sessions
  completed RRC reconfiguration before telemetry offers; no UL-DTCH markers in
  their telemetry intervals. Working references continued logging data traffic.
- [x] Join 1,373 PHY-debug transmit grants to receiver setup/demod records: no
  checked NDI/RV/HARQ/allocation/TBS mismatch. One interval-boundary grant has no
  receive record inside the selection. This does not verify UE grant receipt or
  over-air timing; older working sessions lack comparable PHY fields.
- [ ] Trace the active-UE context release ~247 ms after the first offer in the
  earlier 2 packet/s failure. Other failures kept scheduling; common cause open.
- [x] Prepare bounded native eNodeB RX capture using existing trace hooks in an
  isolated build that preserves the exact dirty source. RF qualification and
  working/failed comparison remain pending below; avoid full PHY text debug.
- [x] Trace source cleanup: unsuccessful SRB RLC indication can set release flag 4,
  complete release/delete tunnels and advance the removal timer. Other paths also
  set that flag. Historical trigger remains unconfirmed; relevant logs were hidden.
- [x] Try one RLC/RRC-debug single-packet probe, PHY info and RF unchanged:
  registration timeout/CEREG 2, zero telemetry attempted; 36 RAR / 36 Msg3 error
  log events and no nonempty Msg3 CCCH. Intended release-path test not reached.
- [x] Snapshot exact dirty OAI source into an isolated diagnostic worktree/build;
  enable existing T tracer, build eNodeB and runtime modules without replacing
  active source/binary. Prepared ground helper defaults to trace OFF.
- [x] Qualify native transport/parser/recorder with synthetic data: 456 input/
  ACK-NACK pairs, byte-exact extraction/filtering, truncated-input rejection,
  time stop and hard byte cap. Default observer 1 second / 128 MiB; RF unqualified.
- [x] Fix native helper argument ordering after one config-only failed launch:
  move tracer flags before `-O`, keep `WORKER_DISABLE` last. Config pre-parser
  otherwise treats the next flag as a filename. No cell/modem window opened.
- [x] Qualify isolated build with trace OFF and ON: each delivered one EPS packet
  byte-for-byte to receiver/Yamcs; 35 seconds registered with zero drop events.
  Production firmware/boot unchanged. No throughput claim from single packets.
- [x] Capture native working reference: 64,120,248 bytes under 128 MiB cap,
  1,012 input buffers and 52 input/decode matches. Connected UE: 51 ACKs;
  one different-identity NACK excluded. Observer gate checks passed without RF.
- [x] Check 51 ACK buffers at 15.36 MS/s: normal-prefix correlation 0.755–0.923,
  configured two-slot DMRS 0.840–0.888 versus controls below 0.269; no checked
  int16 clipping. Supports working waveform match; no independent payload/CRC
  decode or absolute SFN validation, and whole-frame lag ambiguity remains.
- [x] Fresh native repeat: READY 21.913 s; one EPS packet byte-matched receiver
  and Yamcs. Registration lost between 10.386 and 15.383 s after acceptance,
  still down at 35.244 s. Stop repeats on this stability failure. Initial capture
  has 47 ACK / 4 NACK for connected identity; two other-identity NACKs excluded.
  Four connected NACK input records precede telemetry offer; no packet-loss claim.
- [x] Compare four NACK buffers with adjacent ACKs: six-RB receive context and
  narrowband-2 allocation logs agree; conditional DMRS 0.990–0.994 versus
  ACK 0.987–0.994, controls below 0.284. No checked clipping. Strong pilot
  match does not explain payload failure or the later registration loss.
- [x] Delayed capture: start 12 s after acceptance observed, record 3 s /
  256 MiB cap. READY 38.124 s; EPS 1/1/1; registered through 35.379 s, zero
  drops. 190,520,616 bytes, 3,014 input buffers, 150 ACK / zero NACK. Loss
  did not recur; this is a working reference, no throughput/fix claim.
- [x] Build/qualify host-only triggered observer: connected-identity four-NACK
  trigger or registration marker; up to6s history plus1s after,384MiB ring,
  512MiB output,45s hard runtime. Software checks cover filtering/ACK reset,
  ring eviction, both triggers, malformed input and no-trigger deadline.
- [x] First triggered bench run: READY27.192s,EPS1/1/1,registered through35.380s,
  no drops. Capture205,517,876bytes,2.338s before/1.000s after trigger;
  connected151ACK/16NACK, other identities1ACK/1NACK excluded. Ring cap not hit.
- [x] Join all16 NACKs to six-RB/MCS4 schedule records; four new allocation logs
  identify NB2, twelve retransmission records retained. Six conditional weak-
  pilot NACK buffers (<0.3 both slots), ten strong (>0.95); ACK0.980–0.999,
  no checked clipping. No radio-packet-loss or registration-cause claim.
- [x] Offline MAC/adjacent-ACK comparison:167 joined attempts,155 new blocks,
  151 first-attempt ACKs; four failed blocks each rounds0/1/2/3, zero successful
  retries. AllHARQ0/MCS4/sixRB/newTBS51bytes;155 new NDIs alternate correctly.
  Groups:992 allweak;0 allstrong;20 weak/weak/strong/strong;66 allstrong.
- [x] Correct schedule timestamp byte offset in new derived export; preserve
  original exports and document invalid old schedule.timestamp_ns fields.
  Waveform fits/counts/input timestamps unchanged; corrected time-bounded joins pass.
- [x] Review retry source: expectedRV0,2,3,1, same grant/receiver mapping;
  runtimeNDI/RV/reset not recorded. Existing PHY DCI trace HARQ field uses legacy
  calculated ID/TODO, round=-1, though actual grant uses rel13 HARQ. Do not treat
  that diagnostic field as an on-air HARQ error.
- [x] Isolated harqstate build: five scalar stages (packed grant, RX setup,
  rate-unmatching clear/combine, segment decoder return, transport completion).
  Additions-only diff; original source/binary and working rxtrace build preserved.
  Reviewed task-completion lifetime and VCD event-tail ordering before qualification.
- [x] Offline qualification: full executable/modules/ulsim built; dynamic libs
  resolve; VCD checker0;1,150 C-tracer events exact, truncation rejected; both
  recorder triggers/state masks pass; malformed lengths/schema counts rejected.
  CTest reports 10MHz LTE ulsim test3/test4 passed (53.26/60.41s). Not RF proof.
- [x] New-build bench: traceOFF READY56.023s/EPS1/1/1/35s registered; firstON
  READY26.818s but recorder parent missing, gate stopped all telemetry. Parent
  creation fixed/tested; freshON READY22.263s/EPS1/0/0 despite35s registered.
- [x] TraceON missing delivery: initial RRCcomplete21:33:51.846UTC, context
  removed52.309, telemetry offered52.858, accepted53.168; later connection
  setup58.118/reconfiguration complete58.406. Clock audit bound about±0.18s
  supports ordering (no clock step assumed); release precedes offer about0.55s.
- [x] Later-context full scalar stream:1576 complete chains with MAC matches,
  1542ACK/34NACK, no checked grant/RX/NDI/RV/round/buffer/decoder mismatch.
  Initial-context events absent. Static first-RNTI trigger missed changed context;
  final1s IQ fallback is not the initial release. No root cause/fix/rate claim.
- [x] Start scalar capture before IHU/RF admission, all identities, 16 MiB/140s.
  Socket fixtures pass idle metadata startup, identities, signed fields, stop,
  deadline, byte cap and bad schema. No IQ/payload; firmware unchanged.
- [x] Startup bench READY33.844s, EPS1/1/1, registered35s, zero drops.
  1,198,282bytes/71.98s;1918 complete MAC/state chains,1860ACK/58NACK,
  no checked mismatches. Early removal did not recur. Release cause21 follows
  commanded OFF by about25s; subsequent SRB1 max-retry is a shutdown reference.
- [x] Same-settings startup repeat READY66.087s;EPS1/1/1,registered35.364s,
  zero drops;1,212,686bytes/104.41s,1929 complete chains,1773ACK/156NACK,
  no checked mismatches. No early-release failure or release marker captured.
  Two-RB RX snapshots across both runs have identical checked configuration;
  outcomes differ, but this is not an independent access decode or root cause.
- [x] Bounded startup batch (max3,stop at first unsuccessful session): run03
  READY21.810s/EPS1/1/1,registered35.259s;run04 registration timeout90s,
  CEREG4,zero telemetry attempted. No third run. 1891 complete chains onrun03,
  one partial boundary chain excluded,no checked mismatches. run04 recorder
  metadata144,306bytes/93.98s,no selected PHY/MAC events;logs zeroRAR/CCCH.
- [x] Independent RF check: low-receiver-gain DL contrast2.58dB stopped before
  Walter admission; LNA16/VGA8 qualification15.06dB. One attach run then had
  DLcontrast12.55dB before RF admission,90s timeout,CEREG4,zero telemetry.
  HackRF150s/750M samples:zero access-band bins above first5s p99+6dB,
  no overruns/clipping;groundzeroRAR/CCCH,scalar metadataonly.
  Sequential DL/UL checks; no continuous/post-timeout DL proof, weaker or
  off-frequency access remains possible. Acquisition/selection is a lead,
  not a fix or explanation of all earlier failure paths.
- [x] Park reliability debugging after this bounded diagnostic; return to direct
  Walter throughput work. No firmware/radio changes or further cell runs.
- [ ] **Parked:** repeat startup recording to catch missing delivery/early release; cause
  of the original pre-telemetry context removal remains unconfirmed.
- [ ] Arm before telemetry and follow configured context changes or missing-
  delivery/release events, rather than watching only the first RNTI. Preserve
  current raw/state artifacts and avoid full PHY debug or production MCU edits.
- [ ] Capture around the later registration-loss transition with bounded native
  recording; initial one-second capture does not cover that drop.
- [ ] Capture a failed Walter session with the same bounded native observer and
  compare against this working reference. Keep other RNTIs separate; no fix or
  reliability qualification established. Operator notes: ignored
  `.runtime/throughput/RXTRACE_NEXT.md`.
- [ ] Defer 10/20/50 packet/s on this path while the one-in-flight pacer limits it.
- [x] Direct Walter test completed: save original image first, then use separate
  temporary ESP32 benchmark firmware and a separate UDP port/file. Read live
  operator/modem status before changing selection. Start at 128 bytes;
  try 512/1024 bytes only after checking modem/MTU limits.
- [x] Restored original Walter image and verified USB and IHU-chain identity/OFF.

For each point: wait for registered READY, offer for 30 seconds, drain 10 seconds.
Keep the modem window ≤120 seconds, with startup/shutdown headroom. Record offered,
refused, skipped, modem-accepted and unique-received counts, duplicates, late
arrivals, command timing and errors. Goodput = unique received bytes × 8 / 30 / 1000
kbps; use a fixed receiver window starting at its first matching packet. Command
completion time is not one-way radio latency. Do not retry unknown telemetry sends.

## Keep production clean

- Use existing IHU commands and the temporary host driver; no test-only IHU code.
- Temporary firmware goes in separate branches/builds, with production backups
  and restoration. Useful features get their own PR and version increment.
- Use current commands; retired `lte queue` / `eps enqueue` examples are historical.
- Run one cell at a time. The host lock/process guard prevents overlapping runs.
  Wait/retry explicit local control refusals (`SENSOR_BUSY`, `BUSY_TARGET_SWITCH`).
- [x] After all thirty-six rate/probe/RF attempts (plus two config-only failed launches): Walter OFF, original outputs restored, IHU firmware
  and boot unchanged, CAN errors zero, no cell/EPC left running.

## Results

- [x] Save setup, baseline, seven complete windows and three interrupted
  attempts locally in lab-log entry 005:
  `entries/005-walter-lte-m-data-rates/README.md`, with counts and packet receipts.
- [x] Record completed repeats and restoration; retain failures and measurement limits.
- [x] Prepare tools/results for publication; privacy and local checks pass.
  Push the characterization branches after committing; no new RF run.

Temporary driver/captures: `ground/lte/.runtime/throughput/` (ignored).
CPU-only checks covered normal completion and lost RF-admission reply cleanup.
Public results destination: [lab-log](https://github.com/ngrabbs/lab-log), entry 005.
