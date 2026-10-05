# EMBER and SDRB integration work

Updated October 3, 2026. Two workstreams share an optional, narrow interface.
Keep AMSAT SDRB testing independently usable and record its evidence separately.
[Interface and bench procedure](../interfaces/sdrb_adapter.md)

## Shared baseline and ownership

- [x] Identify the current CAN/UHD source candidate and record reviewed adapter source hashes.
- [x] Define ownership and reuse the existing EMBER bench CAN contract.
- [x] Keep the initial adapter in EMBER; no SDRB startup, FPGA, firmware or radio changes.
- [x] Default to monitoring without application replies; require explicit opt-in for replacing COMMS.
- [x] Capture running SDRB kernel/boot-file hashes and reported physical setup; source mapping remains open.
- [x] Match running SDRB boot files to the original developer-image baseline and verify the saved CAN candidate hashes.
- [x] Recover IHU from positively identified BOOTSEL, confirm its installed CAN bench image, and obtain status plus read-only EPS data.
- [x] Back up and verify the entire current SD card, recover its dirty filesystems, and apply/remount-verify the matched CAN boot/module update while preserving the newer UHD library and existing rootfs.
- [x] Stage the optional EMBER monitor in its own manually started directory; no startup service added.
- [x] Capture updated SDRB boot, verify candidate hashes, both CAN controllers and native UHD discovery.
- [x] Operator confirmed CAN1 H7/L8; enabled normal controller reception with adapter replies suppressed for one bounded trial, then returned CAN1 down. Driver does not support listen-only.
- [x] Restore the existing IHU–COMMS CAN baseline: COMMS was in configuration mode; normal mode restored HELLO and a byte-matched 16-byte echo with zero errors.
- [x] Repeat HELLO on the working IHU–COMMS bus with SDRB CAN1 enabled for a bounded capture: HELLO passed, SDRB received zero frames, CAN1 returned down.
- [x] Operator corrected SDRB J11 H/L using the [exported pinout](evidence/j11-pinout-20261003/j11-pinout.svg). First corrected test still received zero SDRB frames; IHU–COMMS HELLO, echo and 128-byte EPS return passed.
- [x] Recover SDRB storage access after operator power-off/card reseat: writable root and matched boot hashes; capture recovered CAN traffic.
- [ ] Check SD filesystems offline at the next coordinated card removal; boot FAT reports an unclean unmount following storage fault recovery.
- [ ] Capture baseline CAN counters and existing SDRB test results before integration.

## Stream 1 EMBER UHF channel

- [x] Reuse the existing versioned POWER_STATUS dictionary and real EPS hardware packet.
- [x] Implement CAN reassembly, envelope/inner CRC validation, producer checks and correlated local-record acknowledgment.
- [x] Verify C/Python transport interoperability across all payload lengths and replay real EPS bytes.
- [x] Demonstrate one fresh 128-byte EPS POWER_STATUS packet across physical IHU–SDRB CAN1; recorded bytes match the IHU return exactly.
- [x] Stop the optional monitor, return both CAN interfaces down, and verify native UHD discovery after the physical CAN check.
- [ ] Independently rerun the broader AMSAT SDRB qualification baseline before promoting integration changes.
- [x] Add optional native POWER_STATUS admission with observable rejection, duplicate, queue-full and local TX outcomes; original binary bytes remain unchanged.
- [ ] Define bounded scheduling, stale packet handling and unavailable-radio behavior.
- [ ] Connect EMBER permissions to bounded transmission requests and safe stop behavior.
- [ ] Agree initial modulation, bitrate, framing, coding/FEC and ground decoding.
- [x] Decode one antenna/UHF packet on LibreSDR and prove original IHU/CAN/RF/Yamcs archive byte identity.
- [ ] Repeat under a controlled conducted RF path; qualify reliability and receiver limits.
- [ ] Define and test uplink validation, acknowledgments and duplicate handling.
- [ ] Verify the future EMBER radio can replace SDRB without changing telemetry producers or ground packet definitions.

## Stream 2 reusable SDRB development

- [x] Add a separate optional binary packet bench application while preserving the text demo.
- [x] Add a bounded EMBER CAN-record forwarding queue beside the generic binary sender; three fresh packets automatically reached Yamcs.
- [x] Define bench queue limits and status for admission, rejection, samples emitted and radio errors; queue capacity is two waiting packets.
- [ ] Keep EMBER packet fields opaque and CAN adaptation outside SDRB core operation.
- [x] Establish bounded614.4kS/s packet/transponder profiles with zero reported U/O; gain-only conducted tone/telemetry checks retain250ms priming. Longer operation and heavier DSP workloads remain unqualified.
- [ ] Verify application replies and qualify CAN0 separately if needed.
- [ ] Verify startup, stop, restart and single radio ownership.
- [ ] Package reusable changes separately with sources, hashes, test evidence and AMSAT review notes.

## Integration acceptance

- [x] Software checks for missing/duplicate fragments, timeout, session changes, conflicting requests, bad CRC and recording failure.
- [ ] Test physical CAN loss, bus saturation, either board resetting and any future queue filling.
- [ ] Keep AMSAT baseline evidence and EMBER route evidence separate.
- [ ] Confirm disabling EMBER integration restores independent SDRB operation.
- [ ] Keep candidates separate from the published SDRB image until reviewed.

Current milestone: incremental RX and optional automatic forwarding demonstrated.
Two correctly timed antenna series delivered 9/10 packets; three fresh native IHU
packets automatically passed CAN→RF→Yamcs with exact byte identity. Response mode,
flight reliability, stale queue handling and physical fault recovery remain open.
[Repeatability and automatic-flow evidence](../../ground/uhf/results/2026-10-03/reliability/result.json).
[Bench preflight](evidence/bench-preflight-20261003/result.json): both SDRB CAN
controllers are disabled in its live device tree. Its boot files match the
original developer-image baseline. The IHU was subsequently found in BOOTSEL;
its exact flash ID and installed program were verified before booting that
existing image. Status and read-only EPS acquisition now respond normally.
COMMS is also on the bus, so first reception must suppress application replies.
The updated boot subsequently verified CAN support, but its Xilinx driver rejects
listen-only. Keep CAN1 down until H7/L8 wiring is confirmed, then use normal
controller reception and an application monitor with no replies.
The [prepared update plan](evidence/bench-preflight-20261003/can-update-plan.json)
records verified candidate hashes and the current UHD library to preserve.
[Card update evidence](evidence/card-update-20261003/update-result.json): 177
runtime/account entries and 184 old module files remain unchanged; candidate
boot files and all 184 matching new module files pass remounted readback.
Full 15,523,119,104-byte card backup was decompressed and hash-verified.
Both filesystems pass after journal/dirty-bit recovery and after the update;
reader safely powered off. [Updated boot evidence](evidence/updated-boot-20261003/result.json)
now confirms both CAN controllers and native UHD discovery. The subsequent [first CAN1 monitor trial](evidence/can1-monitor-20261003/result.json)
ran after operator H7/L8 confirmation. It received zero frames; the IHU's first
HELLO fragment failed (TEC 0→8, TX failure 1). No EPS packet was attempted.
Both SDRB interfaces were left down; no RF started. Cause is not yet isolated.
[Software evidence](evidence/software-20261003/result.json) records 43 passing
ground tests and the byte-preserved EPS replay. Seven adapter checks also pass
on the Linux development host with mocked CAN syscalls. Prepared host copy:
`/home/ngrabbs/work/ember-sdrb-adapter-20261003`; it is not installed on SDRB.

[Baseline repeat](evidence/can1-monitor-20261003/baseline-result.json): existing
IHU–COMMS traffic now passes with zero errors, including HELLO while SDRB CAN1
was enabled. SDRB still received zero frames. Its CAN1 controller is down;
polarity/transceiver path remains unresolved. Offline PCB exports identify J11
pin 7 as the fourth outer-row contact from the microSD end, and pin 8 directly
inward toward JTAG. No live KiCad project was opened or changed.

[Corrected-wiring check](evidence/can1-corrected-20261003/result.json): IHU–COMMS
returned a CRC-valid POWER_STATUS packet, but SDRB received zero frames. User
then reported poorly seated CAN contacts and reseated them. The
[retry](evidence/can1-corrected-20261003/seated-retry-result.json) stopped before
CAN enable or test traffic because SDRB executables now fail with storage I/O
errors and the root filesystem is read-only. Contact correction remains untested.

[Physical EPS monitor PASS](evidence/recovered-can1-20261003/result.json):
corrected polarity, reseated contacts and storage recovery were followed by
88 received frames with zero CAN receive errors. The optional adapter initially
missed them because CAN_ERR_FLAG in its receive mask selected error frames.
The EMBER-only mask fix passed eight Linux adapter checks, including a real
virtual SocketCAN filtering test. The next physical capture validated/recorded
one fresh POWER_STATUS packet, exactly matching the IHU returned 128 bytes,
with zero reassembly errors/timeouts and no application replies or RF. Both
SDRB interfaces were returned down. The SD boot FAT unclean-unmount warning
remains recorded for an offline filesystem check.

[UHF ground section](../../ground/uhf/README.md) documents the Pi/LibreSDR
setup, isolated ember-uhf input, optional binary waveform applications and the
first 128-byte IHU→SDRB→UHF→LibreSDR→Yamcs success. No AMSAT core source or
existing text demo was changed. First two bursts failed decoding; third passed
with multiple settings changed. Scheduling, runtime packet admission, uplink and
reliability remain future work.

- [x] Verify incremental receiver stop/restart across bounded bench sessions; Ctrl-C drains the decoder and preserves evidence.
- [x] Add a persistent optional GNU Radio owner with a binary packet side command and EMBER CAN socket adapter; three fresh packets reached Yamcs at750kS/s in transponder mode.
- [x] Establish a bounded614.4kS/s profile with automatic clock selection, timed TX startup, larger local transport frames and faster packet preparation: zero reported U/O/UDP errors and6/6 fresh packets through Yamcs.
- [ ] Qualify longer operation and additional CPU loads within that profile; higher1.5/4.608MS/s rates remain unqualified.
- [x] Demonstrate conducted435.1→434.2MHz uplink tone forwarding alongside fresh telemetry through Yamcs; final gain-only application passed3/3; limiter candidates remain unqualified.
- [x] Observe all-antenna HT uplink forwarding during repeated fresh telemetry using the external RTL-SDR; preserve the operator report separately from packet verification.
- [ ] Qualify representative SSB/voice quality, distortion and continuity with recorded RF evidence; HT visual observation does not qualify these.

[Persistent radio/side-command evidence](../../ground/uhf/results/2026-10-03/persistent/result.json): telemetry preparation2.71..2.87seconds, one UHD owner, three fresh packet identities verified through Yamcs, and clean control-command stop. No AMSAT core changes.

[Clock investigation and source trace](../../ground/uhf/CLOCKING.md) and
[corrected-profile evidence](../../ground/uhf/results/2026-10-03/clock-review/result.json):
93.24second integrated transponder check, six fresh packet identities verified,
no reported native stream errors, and0.178..0.194second waveform preparation.
LibreSDR automatically selects32MHz/÷16 for2MS/s. The preceding clean111.58second
sample-stream run decoded only3/6 live; two missing packets were recovered offline.
The final receiver threshold/link-margin adjustment passed6/6 live with unchanged
CRC validation. AMSAT checkout stays clean; no core, boot or FPGA changes.

- [x] Add finite configurable host USB triggers for real IHU EPS telemetry;16/16 fresh packets verified at IHU/CAN/socket/RF/Yamcs in two separate~94second streams, zero reported U/O/UDP errors.
- [x] Add opt-in native IHU bench EPS cadence and prove it over UHF without USB telemetry triggers, including a closed USB console period.
- [ ] Integrate the scheduler into production IHU firmware and define command/restart policy separately.
- [x] Verify conducted LibreSDR TXA → SDRB antenna_in/RX1: both known uplink tones detected at approximately37dB spectral SNR. Cause of the earlier antenna receive failure remains unisolated.
- [x] Verify finite integrated teardown waits for CAN monitoring before taking CAN down; subsequent conducted runs report no ENETDOWN.
- [ ] Qualify interruption, restart and physical fault recovery beyond normal finite teardown.

[Cadence and RF-isolation evidence](../../ground/uhf/results/2026-10-03/repeater-proof/result.json) preserves the telemetry success and the unresolved repeater gate separately.

[Subsequent conducted proof](../../ground/uhf/results/2026-10-03/conducted-proof/result.json):
scale16 gain-only forwarding delivered both translated tones and3/3 fresh
telemetry packets. The active application retains250ms priming and adds explicit
RX/TX error monitoring. Python limiters and instrumented IQ graphs failed timing;
the native limiter candidate delivered packets/tones but reported six RX overflows
and28UDP receive drops and was removed from the active sample path. AMSAT
core/FPGA/boot stayed unchanged.

- [x] Qualify one bounded digital headroom check using an optional fused compiled mixer:60.58 seconds,0 RX/TX/UDP errors,3/3 fresh byte-identical packets archived by Yamcs; forwarded peak1.417 → 0.25, sum≤0.37.
- [ ] Pass the all-antenna LibreSDR known-tone uplink gate; HT forwarding is observed below, but the LibreSDR source failure remains unisolated.
- [ ] Qualify linear input-level control/AGC, multi-signal/SSB distortion, spectral products, calibrated RF/analog headroom, link isolation and longer operation before enabling amateur service.

[Native headroom evidence](../../ground/uhf/results/2026-10-03/headroom/result.json)
is separate from the earlier unsuccessful multi-block limiter. The optional
compiled mixer replaces Add with one work block and leaves weak samples unchanged
in software checks. It has no EMBER packet knowledge or radio image dependency.
The stress run limited approximately 76.5% of forwarded samples, so it does not
establish RF linearity or assign clipping to individual stimulus slots. Default
operation retains the original adder. AMSAT sources, boot, FPGA and rootfs
libraries are unchanged; radios were released and CAN0/1 returned down.

[Antenna follow-up](../../ground/uhf/results/2026-10-03/antenna-proof/result.json):
59.88 seconds with zero RX/TX/UDP errors and 3/3 fresh packets archived, but no
translated-tone on/off detection. Receiver-only SDRB shows a weak 4.2 kHz
candidate consistent with the 5 kHz uplink offset; this does not isolate duplex
self-interference. Operator reports stock LibreSDR antennas, a tiny Wi-Fi/900 MHz
SDRB antenna and approximately 12 inches of spacing. Controlled UHF antenna
repeats are recorded below. SSB is held until forwarding passes.

[UHF receive antenna repeat](../../ground/uhf/results/2026-10-03/antenna-uhf-swap/result.json):
operator fitted SDRB's UHF receive antenna; gains, frequencies, LibreSDR stock
antennas and spacing stayed unchanged. Another 3/3 packets match through Yamcs,
59.55 seconds with zero RX/TX/UDP errors and zero clipping. Tone contrast improved
to 1.18/2.09 dB but still failed forwarding. The subsequent repeat with UHF antennas on both radios is recorded below. The inactive limiter does not explain this failure.


[Both UHF antennas repeat](../../ground/uhf/results/2026-10-03/both-uhf-antennas/result.json):
60.76 seconds, 3/3 fresh packets (inner 83..85) byte-identical through Yamcs,
zero RX/TX/UDP errors. Forwarded-tone contrast remained 0.86/0.94 dB and failed
the forwarding gate. Five forwarded samples were limited; telemetry was not
clipped. The [source routing review](../../ground/uhf/results/2026-10-03/both-uhf-antennas/routing_review.json)
found no documented channel/receive-route mismatch; no core or route change
is justified yet. Radios are stopped, CAN0/1 down, AMSAT checkout clean.

- [x] Repeat the finite antenna check with operator-confirmed UHF antennas on both radios; record telemetry success and forwarding failure separately.
- [ ] Measure LibreSDR TXA output at 435.1 MHz with available RF equipment; then select a bounded check of receive link margin and duplex isolation. No further automatic gain/rate sweeps.
- [ ] Resolve the LibreSDR antenna tone gate and qualify recorded SSB/voice performance before amateur service.


[HT/RTL-SDR test](../../ground/uhf/results/2026-10-03/handheld-proof/README.md):
operator observed 435.1→434.2 MHz retransmission continuing with telemetry at
434.1 MHz. The unchanged SDRB profile streamed 203.27 seconds with zero RX/TX/UDP
errors; 9/9 fresh packets (inner 86..94), generated every20 seconds, match through
Yamcs. Forwarded limiting affected7.45% of samples; telemetry was not clipped.
Radios were released, CAN0/1 down and AMSAT checkout clean. The ground receiver
ended before the advertised observer window because setup used its lifetime;
that orchestration failure is retained separately from the successful radio and
packet checks. No exact180-second observer-window or SSB qualification claim.

- [x] Run a user-directed HT/transponder test with repeated fresh telemetry; retain original packet identity, stream counters and operator observation independently.
- [ ] Establish a shared post-readiness deadline and explicit receiver stop for future exact-duration observer sessions; keep setup independently bounded.


[Native automatic IHU proof](../../ground/uhf/results/2026-10-03/native-autotelem/result.json):
4/4 fresh packets at CAN/socket/RF/Yamcs, with three IHU returned-byte identities
and a fourth produced during a25-second closed USB console period. Native
cadence19.999/20.000 seconds; SDRB118.24 seconds with zero RX/TX/UDP errors or
clipping. Timer boot-off, invalid periods and manual readout passed; disabling
left submitted count4 unchanged for more than one period. Firmware controls are
`telem on [seconds]`, `telem off`, `telem status`; no SDRB awareness or new packet
layout. Only IHU was flashed, with full backup and verified readback. COMMS,
Walter and AMSAT image/core stay unchanged. Final timer/radios off, CAN0/1 down.

- [x] Preserve the installed IHU image and verify the new opt-in timer firmware; timer defaults off at boot and retains manual telemetry.
- [x] Verify native cadence with no USB packet triggers and one closed-console period; compare CAN bytes against UHF/Yamcs.
- [x] Add explicit opt-in application startup/stop supervision and bounded evidence storage for SDRB and ground reception; no AMSAT core edits or unattended RF at boot. See [operation](../../ground/uhf/SERVICES.md).
- [ ] Resolve intermittent TX startup underrun/timing errors before claiming reliable restart or unattended operation. Preserve the failed supervised startup; preparing passive CAN/forwarding before RF passed one subsequent short check, which does not establish a root cause or durable fix.
- [ ] Qualify production cadence, outage/restart handling and longer autonomous operation separately from this finite bench proof.
