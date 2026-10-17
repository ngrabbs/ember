# RX bring-up — 2026-10-17

Installed COMMS 0.25.0 from clean commit 6211d58 after a verified full-flash
backup. Backup copied to local private artifacts; both SHA-256 hashes match.
The first load attempt raced USB re-enumeration after backup and found no
BOOTSEL device; the subsequent load/readback and application identity passed.

The `e` clock-off ADC baseline completed: 4096 samples, mean about 2085.5
counts, range 2077–2090, no >10 us scheduling misses. With an assumed 3.3 V
ADC reference this is approximately 1.68 V DC and 10.5 mV peak-to-peak;
these are uncalibrated ADC estimates, not a scope measurement. Raw samples
and console identity are retained alongside the summary JSON.

Final CLK0/1/2 power-down registers are 80, output-disable register FF,
TX/RX indicators low, CAN A normal. Host fault-injection tests cover the RX
clock plan, TX exclusion, failed lock/readback/I2C, abort and shutdown;
existing startup and TX clock tests pass. Original-Pico Release build passed.

Remaining: confirm scope network and tinySA USB access; measure RX LO;
perform attenuated conducted-tone test and baseband/ADC response; then build
and validate packet reception before any command dispatch. No RX LO has yet
been enabled in hardware, no signal injected, and no uplink packet received.
This record does not qualify receiver sensitivity, LO drive, or packet decoding.

## First conducted tone attempts

User confirmed tinySA RF → 30 dB pad → DC block → J9 and Rigol CH1 at
TP6 with board ground. tinySA ULTRA firmware 1.4-156 accepted the generator
commands; output levels below are nominal settings, not independently calibrated.

- 435.001 MHz, generator −50 dBm, nominal J9 −80 dBm: RX window completed,
  ADC range 2075–2084, AC RMS approximately 0.907 counts.
- 434.973 MHz, generator −30 dBm, nominal J9 −60 dBm: RX window completed,
  ADC range 2057–2099, AC RMS approximately 1.084 counts. The wider extrema
  do not represent a clear sinusoid. Neither capture shows a prominent tone
  above the clock-off baseline in its Hann-windowed FFT.

Both captures had 4096 samples and no >10 us timing misses. First capture's
scope scalar queries occurred after the RX window and cannot characterize its
active response. Second scope acquisition was stopped approximately five seconds
into the RX window; its automatic frequency/Vpp readouts are not accepted as
proof of a recovered tone without waveform verification. Raw instrument replies
and ADC samples are retained.

Both windows reported shutdown_verified=1. tinySA output was turned off in
cleanup. No command packets were decoded. These two frequencies do not exclude
a frequency-offset problem and do not establish a hardware failure. Next check:
probe C7 pad 1 for the actual 145 MHz CLK1 signal, then trace the loaded LO path.

## CLK1 at C7 pad 1

User moved the CH1 10× probe to C7 pad 1 with nearby ground. tinySA output
was explicitly disabled. A bounded RX window completed with verified shutdown.
Scope frozen about four seconds into the window: 2.50 Vpp, 1.821 V average,
1 GS/s acquisition. The 1200-point displayed waveform spans 120 ns and has
17 rising crossings; interpolated crossing spacing gives approximately
144.94 MHz. This short, display-interpolated trace confirms a clock near
145 MHz, not a calibrated frequency-offset measurement. The automatic scope
frequency scalar (147.06 MHz) is too coarse here to establish oscillator error.
Next compare C7 pad 2 under the same probe conditions. No mixer LO drive or
receiver sensitivity qualification follows from this source-side result.

## CLK1 after C7 (pad 2)

With the tip moved to C7 pad 2 and the same nominal scope settings, another
bounded RX window completed and verified shutdown. tinySA remained off.
Scope reports 1.24 Vpp and 1.517 V mean. The displayed waveform has 17 rising
crossings over 120 ns, giving approximately 144.94 MHz by interpolated spacing.
The signal is present on both sides of C7. The separately probed 2.50/1.24 Vpp
values are not a calibrated insertion-loss measurement: the 10× probe changes
loading, and this inter-capacitor node has no intentional DC reference. Its
reported mean is not an established transistor bias voltage. No C7 replacement
is justified by this measurement alone. Next probe C83 pad 1 / R33 pad 1 at
Q4 base to establish the tripler input drive.

## Q4 base / C83 pad 1

User confirmed probe positioning at Q4 base. Initial 0.2 V/div acquisition
clipped at the lower display limit; automatic Vavg/Vpp returned 9.9E37 and
are invalid. Repeated at 0.5 V/div without requesting a probe move: scope
reports 2.50 Vpp, mean −0.366 V; exported waveform extrema −1.66/+0.82 V.
A near-145 MHz periodic drive is present. Positive limiting is consistent
with base-emitter conduction, not proof of adequate 435 MHz mixer drive.
Probe loading and separately acquired node amplitudes prevent treating their
ratios as calibrated insertion loss/gain. Both bounded windows completed with
verified shutdown; tinySA output remained off. Next: C86 pad 1 / Q4 collector,
supplied from +5V through L18. The DS1202Z-E bandwidth cannot establish the
absolute 435 MHz LO amplitude with this probe arrangement.

## Q4 collector / C86 pad 1

With the probe at the collector, captured both clock-off and clock-on states
at 2 V/div, 10 ns/div, DC coupling, 10×, bandwidth limit off. Off: 4.964 V
mean and 0.320 Vpp. On: 4.965 V mean and 1.040 Vpp. A short displayed-waveform
FFT shows increased periodic content (largest bin near 291.7 MHz, with content
near 145 MHz); neither that FFT nor the automatic 250 MHz frequency reading
establishes a correct 435 MHz LO. The 200 MHz scope and probe loading prevent
calibrated out-of-band amplitude claims. Collector supply and clock-dependent
activity are demonstrated, not adequate mixer drive. Final clock-disable FF,
CLK0/1/2 power-down 80, RX window completed with verified shutdown; tinySA off.
Next probe C97 pad 2 / U10 pin 6 for clock-dependent signal at the mixer LO input.

## Mixer LO input / C97 pad 2

User positioned the probe at C97 pad 2 (U10 pin 6). Generator remained off.
Clock-off scope: mean 1.06 mV, 16 mVpp. Clock-on: mean 1.31 mV, 104 mVpp.
Short displayed-waveform Hann FFT has its largest bin at 433.33 MHz, adjacent
bins 425/441.67 MHz, consistent with intended ~435 MHz LO activity. Bin spacing
8.33 MHz and the out-of-band scope/probe response preclude a precise frequency
or calibrated power claim. The automatic 22.83 MHz scalar is not accepted as
LO frequency. Signal reaches the mixer LO net, but +7 dBm drive remains unverified.
Window completed and shutdown verified; final registers 3=FF,16/17/18=80.
Next move to TP5 (RX_IF before the narrow LPF) and reapply a weak RF tone to
look for a beat outside the baseband filter passband as well as within it.

## TP5 tone tests — probing validation required

At nominal −60 dBm J9 (generator −30 dBm, external 30 dB pad), tone-off/on
captures did not establish a beat. Raised to nominal −50 dBm J9 and tested
435.001/435.011 MHz, then repeated at 435.011/435.021 MHz. All three RX
windows completed with verified shutdown; generator output disabled in cleanup.
The initial apparent signal increase did not produce a reliably tracking beat.
Repeat scope traces clipped at 10 mV/div. Its concurrent ADC capture was dominated
by ~60 Hz (~36.8 counts AC RMS), not an identified mixer beat.

With RX clock and generator off, TP5 at DC coupling, 0.5 V/div, 5 ms/div showed
1.525 V mean, 3.24 Vpp, 60.24 Hz. This is a substantial mains-frequency signal
or probing artifact; the current setup cannot support an RF reception claim.
User asked to identify the ground spring contact and place both tip and spring
on confirmed board GND before further diagnosis. No component failure assigned.
Earlier brief 145 MHz / LO observations remain observations under the reported
probing setup, not calibrated measurements; grounding must now be checked.

## Corrected ground: first analog receive confirmation

User confirmed tip remained on TP5 and corrected its ground contact. With both
sources off, TP5 now read 1.670 V DC, ~20 mVpp at coarse 0.5 V/div, no valid
frequency. This supersedes the earlier 3.24 Vpp/60 Hz observation as evidence
of receiver behavior; the previous probing setup was not reliable.

At nominal −50 dBm into J9 (tinySA −20 dBm plus external 30 dB pad), a corrected
frequency-step test produced low-frequency spectral peaks near 8.33 kHz for
435.001 MHz and 18.33 kHz for 435.011 MHz. The 10 kHz beat shift matches the
commanded source shift. These are short-scope-FFT estimates, not calibrated RF
frequencies. Tuning the source to 434.994 MHz brought the beat into the analog
passband and produced a strong ~1.391 kHz tone in the Pico ADC.

Confirmation with 4096 software-paced samples per capture, 8 kS/s nominal,
no >10 us timing misses:

| Source at J9 (nominal) | ADC AC RMS (counts) | Fitted tone peak (counts) |
|---|---:|---:|
| −50 dBm | 8.669 | 11.074 |
| −60 dBm | 2.755 | 3.294 |
| Source off, LO on | 0.829 | 0.072 maximum in searched band |

The fitted tone dropped 10.53 dB for a commanded 10 dB source reduction and
was absent above the baseline with source off. Sine/cosine/DC least-squares
fit searched 1385–1397 Hz in 0.05 Hz steps, choosing largest fitted amplitude;
frequency drift across captures is possible. Assuming a 3.3 V ADC reference,
the fitted tones are ~17.8 and 5.3 mVpp; those are ADC-derived estimates.
Raw captures, instrument replies, and analysis JSON are retained here.

This establishes a CW receive response from the shared antenna connection
through the analog chain into the Pico ADC. It does not qualify sensitivity,
absolute LO power, calibrated gain/noise, or packet/command reception. Relative
source/LO frequency offset must be handled before uplink packet tests; it must
not be assigned solely to either instrument without a frequency reference.
All windows completed with verified shutdown. Final clock registers 3=FF,
16/17/18=80, generator off, CAN A normal. No component changes were made.

## LibreSDR uplink preparation and first carrier

Installed clean COMMS 0.26.0 from 114c1b8 after full-flash backup/readback.
Uppercase R provides 32768 samples in the existing bounded RX window. Host
startup/RX fault tests and 17 BPSK tests pass; real-IF simulations decode native
bench fixtures offline, including LPF and noise. No onboard packet parser or
command execution has been added.

User connected TXRA → 30+20+10 dB pads → DC block → J9 and lifted the scope
probe. Existing custom FPGA hash verified. A one-second LibreSDR CW burst at
requested 434.994 MHz, channel0 TX/RX, gain70, amplitude0.05 completed with full
sample count and burst acknowledgment, no streaming errors. Gain is a device
setting, not measured dBm. Digital carrier offset20 kHz separates the intended
signal from center-frequency leakage. Source waits for an explicit GO and sends
only a finite waveform, with an end-of-burst cleanup; no continuous RF enabled.

The 32768-sample ADC capture completed with no >10 us timing misses and verified
shutdown. Two half-second regions during the burst show ~654–658 Hz with peak
amplitude ~0.6 count, compared with ~0.9 count broadband RMS noise. This is
weak, time-correlated carrier evidence, insufficient for packet qualification.
User had anticipated excessive attenuation. Requested removal of only the20 dB
pad, leaving40 dB for the next test; no automatic assumption that rewiring occurred.
Relative frequency differs from tinySA and must be checked before packet testing.
Final CAN A normal, clock outputs disabled/powered down. No uplink packet sent yet.

## First captured BPSK uplink: 3/3 exact payload matches

User confirmed TXRA → 30+10 dB pads → DC block → J9, scope lifted,
tinySA disconnected, IHU telemetry stopped. Removing the 20 dB pad produced a
clear ADC carrier. The packet tests used requested 434.994550 MHz, channel 0
TX/RX, gain setting 70 and amplitude 0.05. Absolute input power is uncalibrated.
Firmware remains clean COMMS 0.26.0 (114c1b8).

Three separately triggered, finite DBPSK bursts (sequences 1901, 1902, 1903)
were captured through the board RX chain at 8 kS/s, 32768 samples each. Offline
strict DBPSK decoding recovered exactly one packet per capture; all 38 bytes
matched each independently recorded transmitted synthetic HEARTBEAT fixture.
The decoder validates outer CRC32 and native CRC16. Carrier estimates were
1209.343, 1210.442 and 1208.748 Hz. See libre-packet-40db-proof.json and the raw
console captures. Each waveform lasted 0.773333 s including zero guards, with
148480 samples sent and no reported transmitter errors.

All captures completed without >10 us sample timing misses, ADC rail clipping,
or shutdown failures. Final clock mask FF and controls 80/80/80 confirm clocks
disabled; CAN A returned to normal. Transmitter finite bursts ended; no ongoing
RF test was left running.

This demonstrates packet-bearing RF reception through the analog path into the
Pico ADC and successful host decoding. It is not onboard decoding, command
execution, sensitivity qualification, or a statistically meaningful reliability
test. No fixtures were forwarded to Yamcs. Next: onboard demodulation and frame
validation, followed by a bounded read-only command test. Frequency acquisition
and tolerance remain open; these tests used a manually selected source offset.

## Onboard decoder: initial timeout and search-order correction

COMMS 0.27.0 (e4c0eba, clean) was installed after verified full-flash backup.
The first live sequence 1911 capture was timing-valid with verified shutdown,
but the ascending 400 Hz search exhausted its three-second decode budget
(found=0, elapsed 3.011220 s). CAN A returned to normal. The exact saved capture
subsequently decoded byte-for-byte on the host using the C decoder at 1200 Hz.
This was a runtime acquisition-budget failure, not evidence of a failed RF path.

0.27.1 prioritizes the deliberately selected 1200 Hz IF, then expands outward
in 25 Hz steps, preserving the time limit and capture-only/no-dispatch behavior.
Host tests pass three earlier hardware captures, twelve synthetic timing/frequency
cases, bad outer/native CRCs, command rejection, silence, noise and clipping.
The decoder also checks invalid size and cancellation; address/undefined-behavior
sanitizers report no errors. Pico build uses warnings as errors. Actual hardware
runtime of the corrected search is checked separately below.

## Onboard decode verified: COMMS 0.27.1

Installed clean 728f537d360c6918631504712c61df338edf0518, version 0.27.1,
boot 2510462400. Flash readback verified. ELF reports text 75848 bytes and
BSS 80420 bytes; decoder workspace is static rather than on the Pico stack.
Same 40 dB conducted chain, requested 434.994550 MHz, gain setting 70,
amplitude 0.05. No rewiring or component changes.

| RF sequence | Pico decode time | Payload comparison |
|---|---:|---|
| 1912 | 119554 us | all 38 bytes exact |
| 1913 | 116240 us | all 38 bytes exact |

The Pico itself prints the decoded bytes after verifying outer CRC32, native
CRC16 and framing. These are synthetic telemetry fixtures, not commands.
Both use mixer search setting 1200 Hz; that is not a carrier estimate. Proof
JSON compares each console result with its independent transmitter result.
Each transmitter sent exactly 148480 samples and reported no errors.

A following source-off capture returned found=0 after 3011194 us, exercising
the search deadline. This is a bounded negative check, not a complete scan of
every frequency or sensitivity qualification. All three captures had zero
>10 us sample misses and verified clock shutdown. Final registers 3=FF and
16/17/18=80, CAN A NORMAL, no ongoing RF burst. No command dispatch, RF reply,
CAN forwarding or Yamcs forwarding occurred.

Next: define and validate a narrowly scoped read-only uplink command path.
Continuous reception, broad frequency acquisition, sensitivity and packet-loss
qualification remain open. Current R mode is a manually triggered capture and
post-capture decode; CAN service pauses during that diagnostic.

## PING-only ingress verified: COMMS 0.28.0

Installed clean b479c6445036b09d8f4adf4b15890a46cae2b137, version 0.28.0,
boot 462500884, after verified full-flash backup and verified load. Same
conducted 40 dB chain and LibreSDR settings as the previous tests. The native
command contract remains ground→IHU; COMMS validates ingress and prints status,
but does not forward, execute, or produce a response.

| Sequence | Test | Pico result | Decode time |
|---|---|---|---:|
| 1921 | Valid PING | PING_ACCEPTED | 111766 us |
| 1922 | Same transaction, new sequence | PING_DUPLICATE | 114445 us |
| 1923 | Wrong destination (COMMS instead of IHU) | REJECT_ROUTE | 113321 us |
| 1924 | Damaged native CRC, valid outer CRC | No valid packet | 3266545 us |

The negative CRC search finishes its current frequency candidate before checking
the three-second deadline, explaining the measured 3.267 s duration. RF clocks
were already shut down during decoding. This is not a strict three-second
wall-clock bound. CAN service returned to normal after all tests.

Offline forensic recovery validates each outer CRC32 and compares its payload
byte-for-byte against the independent transmitter log, including the two negative
cases. The strict native codec separately rejects the wrong route and damaged
CRC. The audit script intentionally bypasses native validation only in its own
process to expose malformed outer payloads; it has no forwarding path and is
not deployed as a production decoder. Both valid PINGs passed strict native
validation. See ping-028-proof.json and ping-028-outer-audit.json.

Host C tests with address/undefined-behavior sanitizers passed route, CRC, shape,
identity, duplicate/conflict, cache-full fail-closed, recorded ADC regression,
synthetic waveform and negative cases. Startup tests and 14 selected Python
waveform/ADC/modem tests passed; Pico build used warnings as errors. Cache stores
16 transactions until COMMS reboot, without eviction; it is not authentication
or persistent anti-replay protection.

Final clocks mask FF, controls 80/80/80, CAN A NORMAL; finite RF bursts ended.
No IHU command execution, CAN forwarding, RF reply or Yamcs forwarding occurred.
Next: connect the validated PING to the IHU command/response path, then verify
its genuine response over RF. Continuous RX and broader qualification remain open.

## RF PING forwarded to the real IHU command engine

Installed COMMS 0.29.0 and IHU 0.10.0, both clean firmware source 08b3620,
after full-flash backups and readback verification. IHU boot 2786831095;
COMMS boot 3644629636. The initial IHU load attempt immediately after backup
found no accessible device during USB re-enumeration; a subsequent load verified
successfully. LTE firmware was not changed.

Conducted uplink sequence 1931, native epoch 1381519409 / transaction 1, decoded
on COMMS and forwarded once on dedicated CAN 0x730. IHU generated a native
COMMAND_RESPONSE (kind 2, message 49), PING COMPLETED, reason NONE, and returned
it on 0x731. COMMS validated and held exactly the same 43 bytes. Independent
native codec validation confirms IHU source/boot and transaction identity.
Both endpoints report normal CAN; IHU counters show no TX failures/timeouts,
RX errors or fragment failures. No RF return was automatically transmitted.

Host integration exercises actual IHU command engine, fragmentation, duplicate
caching, response correlation and malformed-route/unsupported-command rejection.
Startup tests passed. Both Pico builds passed warnings-as-errors. The isolated
ground test receiver is now 2.3.0 with native response decoding; 15 waveform,
ADC and modem tests pass. Production live receiver service remains unchanged.

User selected OTA for the return test. Requested removal of the conducted link,
UHF antennas on COMMS J9 and LibreSDR RXA approximately three feet apart, TXRA
unconnected, scope probe lifted. RF return awaits physical setup confirmation.

## Genuine IHU completion returned OTA and archived in Yamcs

User confirmed replacing coax with UHF antennas on COMMS J9 and LibreSDR RXA,
about three feet apart, TXRA disconnected and scope lifted. Started an eight-second
receive-only capture at 437 MHz, channel 0 RX2 (RXA), gain 0, using isolated
receiver 2.3.0 (content SHA256
540142e45bb255c627713d445ce643a33eb828bd1bc8af1db80b948a2c591632).
Only after receiver readiness, explicitly triggered COMMS console V once.

COMMS transmitted the held IHU response, reported response_RF_complete=1 and
verified TX shutdown. Receiver recovered exactly one strict DBPSK frame with
valid CRCs and no streaming errors. All 43 bytes equal the IHU-generated response
and COMMS CAN-held copy. Estimated carrier offset -6672.752 Hz; this is a decoder
estimate, not calibrated transmitter frequency. No automatic repeat occurred.

After byte comparison, forwarded that single real response via UDP to ember-uhf.
Yamcs archive contains exactly the same bytes as /ember/COMMAND_RESPONSE,
reception 2026-10-17T14:14:49.129Z. Parameters acquired: command_id=1 (PING),
stage=COMPLETED, reason=NONE. See ihu-ping-return-ota-01-yamcs-proof.json.
The receiver capture's forwarded=0 records its original receive-only phase;
proof.forwarded_verified_response=1 records the subsequent verified forwarding.

This demonstrates conducted RF uplink → COMMS → CAN → IHU command engine → CAN
→ COMMS → OTA downlink → ground decoder → Yamcs. It is one manually staged
transaction, not continuous receive, automatic turnaround, full OTA round-trip,
or reliability qualification. Reply is consumed; sources are idle and CAN A is
normal. Production continuous receiver remains unchanged; version 2.3.0 was
used in the isolated test directory. Next: continuous/bounded listening and an
explicitly bounded automatic half-duplex reply path, then repeated OTA trials.

## Automatic reply preparation and initial OTA uplink failures

Installed clean COMMS 0.30.0, aff7509, boot 458828362, after verified backup/load.
IHU remains 0.10.0, boot 2786831095. User clarified all LibreSDR ports have
antennas; OTA trial uses TXRA uplink then RXA receive, with transmit burst
acknowledged complete before starting the ground receiver. No cable move required.

Host lease tests cover no boot authorization, one-shot consumption, expiry,
cancellation, missing response and unhealthy state; startup tests pass. Sixteen
selected Python tests pass, including response transaction/boot correlation.

Two explicitly triggered automatic trials, sequences 2001/2002 with transaction
20, at TX gain settings 55/65 and amplitude 0.05, produced no valid uplink decode
and no RF reply. Both ground captures had no receiver errors and no packets.
Both COMMS windows ended reply_attempted=0, armed=0, clocks shut down and CAN A
normal. Failed attempts are retained; these are not successful round trips.

A separate one-second CW burst with the previously proven transmit-only helper,
gain70/amplitude0.05 at 434.994550 MHz, produced a weak ~1218–1220 Hz beat in the
ADC only during the source burst. Half-second Hann FFT peak amplitudes were
approximately 0.60 and 0.79 ADC counts in burst bins, versus ~6 counts in the
successful conducted carrier test. Broadband RMS rose from ~0.78 to ~0.97–0.99
counts. A ~2650 Hz background component is present outside the burst too.
This supports a weak OTA uplink rather than simply failed automatic turnaround;
absolute RF power and receiver sensitivity remain uncalibrated.

Requested actual antenna separation and a one-foot, parallel-antenna trial
before further RF testing. No continuing transmission or automatic retry.

## User-requested OTA repeat: automatic trial 03

Repeated one bounded PING after the user requested another attempt; actual
antenna separation was not reconfirmed. Same firmware boots as above, IHU
telemetry stopped. Sequence 2003, fresh transaction 21, gain65/amplitude0.05.
Ground reports transmitted=true, errors=[], no received packets. COMMS captured
32768 samples with no timing overruns, min2061/max2097, but found no valid frame.
Independent offline decoding of the same ADC capture also returned no packets.
No CAN PING was forwarded and no RF reply was attempted. Automatic authorization
ended disarmed; clocks disabled, CAN A normal. This remains an unsuccessful
full OTA round-trip, not a demonstrated automatic reply. Raw console, filtered
summary, ground output and offline result are preserved with prefix
auto-ota-030-03. No additional RF retries were started.

## Gain70 OTA attempt and command-aware offline comparison

User confirmed antenna placement unchanged and requested higher LibreSDR power.
Trial04 aborted before RF: GO timeout, transmitted=false. The local orchestration
script used select() around buffered text readline(), which could delay READY
processing; replaced readiness handling with a dedicated readline thread/queue.
Trial05 transmitted one finite PING, sequence2005/transaction23, gain70 and
amplitude0.05 at434.994550MHz. User independently saw its burst on RTL-SDR/SDR++.
COMMS captured without timing overruns but decoded no frame; no reply attempted,
lease disarmed and clocks disabled. Ground reported no errors and no reply.

Correction to trial03 analysis: adc_capture.py uses the telemetry/response modem
which filters native command kind0. Its empty result alone could not establish
failure to recover a PING. analyze_ota.py is an OFFLINE forensic tool: it retains
outer CRC32 checking, permits recovery regardless of native kind, and separately
validates the recovered native packet. It does not forward or execute anything.
It additionally searches400..2600Hz in25Hz steps with8 timing phases. This method
recovers the known-good conducted PING1921 and no frames from OTA trials03 or05.
Production receive filtering was not changed.

Overlapping0.5s windows show a burst at roughly1.0..2.0s in trial05. Maximum-window
RMS is1.586ADC counts versus background~0.8, compared with5.081counts in the
successful conducted PING. Windowed400..2600Hz peak band power is1.910 versus
25.692 counts squared (background~0.35): approximately12dB less signal after
rough noise subtraction. These are relative ADC observations, not calibrated
antenna input power or a sensitivity measurement. Burst squared-spectrum
candidate frequencies are1285.4Hz for trial05,1238.9Hz for trial03 and1209.7Hz
for the known-good capture; weak-signal candidates are not precise carrier
measurements. All are inside the searched frequency range.

Evidence supports inadequate OTA signal margin as a working hypothesis; it does
not isolate transmitter output, antenna path or receiver gain/noise. Gain70
still uses digital amplitude0.05, so it must not be described as full transmitter
power. No further transmissions during this analysis. Next establish actual
LibreSDR output level with tinySA and compare a controlled conducted input.

## LibreSDR conducted output measurement

User connected TXRA through DC block and confirmed external30dB pad to tinySA RF
input. tinySA4_v1.4-156-g4eb315d HW V0.4.5.1.1, generator off, input mode, LNA off,
external gain correction set0. Two finite1s tones at434.994550MHz, gain70,
amplitude0.05, completed with burst acknowledgment, gain reset0 afterward.
First max-hold/data read was ambiguous/no distinct tone and is NOT a power
measurement. Second used synchronized direct100-point scans434.9..435.1MHz,
RBW10kHz, internal attenuation10dB. Scans2..5 measured -48.47..-47.97dBm near
434.992929MHz (scan bin, not precision frequency). Before/after peaks~ -100dBm.
Nominal external30dB correction gives approximately -18dBm (~16uW) at source,
excluding uncalibrated DC-block/cable loss and pad/analyzer uncertainty. Internal
attenuation is already corrected by analyzer; do not add it again. No evidence
of overload at this level. Production code unchanged. This measures CW at the
packet test's settings; it is not a calibrated packet power or RX sensitivity
test. Connection remains conducted to tinySA, no ongoing source transmission.

## Controlled amplitude steps with external30dB pad

With unchanged TXRA → DC block →30dB pad →tinySA RF IN, measured two further
1-second tones at434.994550MHz and gain70. A separate power_tone_probe.py permits
up to0.20 amplitude for tone ONLY, retaining0.05 packet limit; existing production
and packet tools unchanged. Direct synchronized scans use10kHz RBW and10dB
internal attenuation. Both bursts acknowledged complete with no TX errors,
then gain reset0. No COMMS receive/reply was armed during these measurements.

Nominal source estimates after external30dB correction:
- amplitude0.05 (previous): approximately -18dBm (~16uW).
- amplitude0.10, trial03: -12.47dBm (~57uW), input -42.47dBm.
- amplitude0.20, trial04: -5.94dBm (~255uW), input -35.94dBm.

The approximately6dB increase per amplitude doubling is consistent with linear
output scaling at these settings. This does not measure spectral purity, packet
quality, or receiver sensitivity. Same uncalibrated cable/block/pad/analyzer
uncertainties apply. No full-power claim. Recommend next finite OTA PING at
amplitude0.20 after the user restores TXRA antenna; no OTA transmission yet.
