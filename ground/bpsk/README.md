# Y24 bounded BPSK bench link

Separate from the working SDRB 1200-baud FSK path. Not a flight modem: no FEC,
pulse shaping, retransmission, uplink decoder, or continuous telemetry service.

The original Pico's `transceiver_bringup` v11 accepts a single byte `b` (no
newline). It prepares one **native COMMS HEARTBEAT**, with actual random boot ID,
monotonic uptime and sequence, COMMISSIONING/GROUND_TEST, telemetry period zero
(manual). No EPS measurements or ADC values are fabricated. It prints the exact
38 packet bytes before RF so reception can be compared byte-for-byte.

Framing: 32×55 preamble, sync1ACFFC1D, version3 byte, sequence32 BE, length16 BE,
native packet, CRC32 over version through payload, 16 zero guard bytes. MSB first.
Differential BPSK: initial phase0, bit1 toggles GP16, bit0 retains phase; 1200 baud.
The XOR applies phase modulation before the odd-harmonic tripler. Actual phase
quality and decoding over this physical circuit remain unverified.

One frame is101 bytes /808 symbols, about673.3ms. Absolute software symbol
deadlines abort on >150us lateness or any console input. IRQs remain enabled.
The clock plan is the existing437MHz target. An independent SDK alarm mutes
GP10 after2 seconds; timer-allocation failure prevents transmission. Clock lock
and output-mask readback are checked before/after the frame. I2C is deliberately
not polled during symbols; loss of lock during a frame is not continuously
monitored. The bounded frame/timer and final checks limit this experiment.
Cleanup mutes GP10 before resetting GP16 and disabling CLK0. Startup never
transmits. This is not a crash-proof hardware RF inhibit.

## Validation before RF

```
python3 firmware/transceiver_bringup/tests/check.py
cc -std=c11 -Wall -Wextra -Werror -Ifirmware/transceiver_bringup firmware/transceiver_bringup/tests/clock.c -o /tmp/clock-test
/tmp/clock-test
python3 ground/bpsk/test_modem.py -v
```

The Python test needs NumPy and a C compiler. It cross-checks exact C/Python
frame bytes and native CRC16, then tests DBPSK timing, phase/conjugation, noisy
carrier offsets±10kHz, packet/window boundaries, malformed data and noise-only
rejection. Software tests do not establish RF performance or a false-alarm rate.

## Receive-only capture

On the ground Pi, check no LTE/UHF service owns LibreSDR. Retain the existing
custom FPGA image; the capture verifies its SHA256. Use channel0/RX2 only if it
matches the actual antenna connector. Minimum gain0 is the starting point for
the reported antennas approximately three feet apart. This is not a calibrated
link budget. Do not substitute a direct coax TX→RX connection without reviewing
attenuation. C1/C2 are open and C6 was replaced with0Ω on this prototype.

```
python3 ground/bpsk/capture.py --seconds 8 --gain 0 --output /path/to/new-run
```

Wait for `BPSK_RX_READY`; then send one `b` to the identified transceiver Pico.
No automatic TX is provided by the capture helper. The receiver takes192kS/s,
low-pass filters and decimates to48kS/s. Decoder carrier search covers±12kHz
about tuning; default437MHz is intended for the current measured carrier.
It retains full-rate IQ, derived IQ and JSON. Any streaming error prevents
forwarding. A new output directory is required for each capture.

Use `--forward` only for the actual RF acceptance run: recovered original native
telemetry bytes go to localhost UDP10019 (`ember-uhf`). There is no fake packet
fallback. Check `result.json` against the Pico's packet_hex and a **new** Yamcs
archive entry; a displayed cached value is not proof. The first packet is a
COMMS heartbeat, not IHU EPS data, so use packet archive/heartbeat parameters,
not the old EPS proof display.

Offline repeat: `python3 ground/bpsk/modem.py /path/to/baseband-48k.npy`.
Maximum capture15s. Stop tests on timing/stream faults and investigate saved
records. Leave periodic IHU telemetry and unrelated radio services unchanged.

## First hardware result — October15

v11 (`cec4c38`) built/flashed with verification. One burst completed and shut
 down correctly, with no LibreSDR stream errors at gain0. The standard DBPSK
decoder returned no packet. Inspection of saved IQ suggested transitions near
90 degrees rather than the intended180; cause remains unconfirmed.

An explicitly selected offline `--phase-diagnostic` uses a45-degree transition
threshold and recovered the exact native heartbeat with both CRCs valid.
Those actual RF-recovered bytes were independently compared with the Pico
console and forwarded unchanged to Yamcs, which archived `/ember/HEARTBEAT`
at2026-10-15T22:51:17.695Z. This is a diagnostic RF telemetry success, **not a
standard BPSK qualification**. The normal decoder/capture path remains strict;
there is no automatic diagnostic fallback or synthetic packet injection.
Next: measure the actual phase states/drive path and resolve the discrepancy.

## Native IHU telemetry (v18)

The `f` bridge supports the existing HEARTBEAT, SYSTEM_STATUS, POWER_STATUS,
and COMM_STATUS layouts unchanged. POWER_STATUS is 128 native bytes /191 RF
bytes (1.273 seconds); decoding now uses four-second windows with one-second
stride. Use a 15-second capture and `--forward` to pass strictly decoded
telemetry to Yamcs after capture. See the firmware README for the per-packet
HELLO/arm/command sequence and the intentional absence of application ACKs.

Timed IHU runs can be checked with a finite capture up to180 seconds. For the
120-second run, use `--seconds 135` and start the producer after BPSK_RX_READY.
IQ remains retained; decoding and optional Yamcs forwarding happen after the
capture ends. This does not start a permanent receiver service.

## Live UHF demo receiver

On the ground Pi, with other LibreSDR captures stopped:

```bash
python3 ~/work/ember-y24-bpsk/ground/bpsk/live.py \
  --seconds 600 --gain 0 --forward \
  --output ~/work/ember-y24-bpsk/runs/live-$(date +%Y%m%d-%H%M%S)
```

Wait for `BPSK_RX_READY`. With COMMS v22 / IHU v7, CAN is ready at boot:
issue IHU `hello` and wait for `CAN_HELLO_CONFIRMED`, then press COMMS `a`
(one byte, no Enter). IHU `uhf run 120 10` starts the
finite two-minute heartbeat/system/EPS cycle. The receiver can stay running
between runs; renew COMMS `a` and explicitly start another IHU run as needed.
COMMS `x` stops its service; IHU `uhf stop` stops future telemetry production.
Receiver Ctrl-C saves results and closes reception. No receiver command starts TX.

Open the existing EPS or health dashboards with `c=ember__realtime`, not
`ember__realtime`. Each `BPSK_RX_PACKET` line names a validated packet forwarded
immediately to local Yamcs UDP10019. Four-second overlapping windows advance
once per second; this introduces a few seconds of decoding latency, not a
whole-capture delay. No diagnostic phase fallback is used. Duplicate detections
of the same RF sequence and native bytes are forwarded only once per session.

The receive loop writes `raw-192k.cf32` (little-endian complex64,192000 samples/s).
`session.json` describes the capture; `packets.jsonl` records validated original
packets before forwarding; `result.json` summarizes shutdown. UDP send success
is not itself an archive acknowledgment. Previously forwarded packets remain
valid evidence if a later stream or decoder error stops the session. A four-job
queue bounds DSP backlog; overflow stops rather than silently dropping windows.
Recording uses approximately92 MB/minute (922 MB for ten minutes). Session
length is bounded at1–3600 seconds; default600 seconds. It does not auto-start
on boot or enable transmissions. `capture.py` retains the older offline workflow.

### Hardware regression, October 16

With COMMS v21 / IHU v7, a30-second run (three heartbeat/system/EPS cycles)
delivered9/9 byte-identical packets live into Yamcs. Archive inspection at ten
seconds verified arrival during the run. The repeat's55-second receive session
had no stream/decoder errors, and HELLO/discovery worked after RF stopped.
An initial capture also delivered9/9 packets but then stopped on a sample-stream
overflow; its cause remains unresolved. Do not treat the clean repeat as a
long-duration reliability qualification. See lab-log entry003 for both records.

Receiver pipeline v2 moves raw IQ storage and window construction off the USB
receive loop into a64-chunk bounded queue (about2.7 seconds at8192 samples per
chunk). Overlap windows use preallocated storage. The existing four-window DSP
queue remains bounded. Any stream error or exhausted queue still stops the
session; no sample gap is silently bridged. Result JSON records queue peaks,
maximum receive-loop scheduling gap and longest storage-chunk processing time.
This mitigates synchronous disk delays; it does not prove the earlier overflow's
cause. `Comms-Firmware.opi` shows the received release and full source commit.

### Team demo checklist

Use the UHF Yamcs instance (`c=ember__realtime`):

- `EPS.opi`: live readout/conversion status and power measurements. Current
  calibration still depends on confirming the fitted sense resistors.
- `System.par`: HEARTBEAT and SYSTEM_STATUS values, generation times and uptime.
- `Comms-Firmware.opi`: received COMMS release, dirty flag and full source SHA.

Overview's endpoint counters and command-report panels are not produced by this
bounded UHF telemetry cycle; blank panels there do not diagnose packet loss.

For a 10–15-minute rehearsal, start a 690-second receiver session. After READY,
perform five explicitly bounded `uhf run 120 10` runs. For each run: obtain a
fresh IHU HELLO, enable COMMS with `a`, start the IHU run, and wait for
`UHF_RUN EXPIRED submitted=36 cycles=12`. Stop COMMS with `x` and inspect status
before starting the next run. Never increase the firmware RF limits to make
this demo continuous. COMMS v22 contributes one identity packet per admitted
session, for 185 expected packets across five successful runs.

Keep receiver stdout drained (a normal terminal or redirected file is fine).
During the run, check advancing generation times as well as ACQUIRED status;
some system parameters retain their last value without an expiry. Stop if the
receiver reports an error, the IHU reports a run fault, or a queued RF request
has an unknown outcome. At the end issue IHU `uhf stop` and COMMS `x`, verify
TX/RX inactive, and confirm a new HELLO works. Compare original native packet
bytes with the Yamcs archive; UDP send success alone is not delivery proof.

### Controlled storage-stall test, October 17

A receive-only comparison injected a single 1.8-second raw-file write delay
at approximately eight seconds. The pre-pipeline receiver (`52c0b3e`) stopped
with `ERROR_CODE_OVERFLOW`. Pipeline v2 completed all 25 seconds without errors:
its input queue peaked at42/64 chunks, longest storage operation was1.806 seconds,
and maximum measured receive-call gap was0.710 ms. Neither trial transmitted or
forwarded packets. This establishes a reproducible failure mechanism and tests
the mitigation under that load; it does not prove the original incident was
caused by a disk stall or guarantee tolerance of arbitrarily long stalls.

The subsequent 690-second live rehearsal delivered185/185 packets (60 each of
HEARTBEAT, SYSTEM_STATUS and POWER_STATUS plus five COMMS identities), with
exact Yamcs archive matches and no receiver errors. Five-second freshness
samples remained ACQUIRED; maximum observed EPS age14.58 s. EPS/System displays
were visually checked across the run. Final RF-off status and CAN HELLO passed.
See lab-log entry003 for evidence and remaining hardware qualification limits.

Version comparison and deployment checks: [ground release identities](../releases/README.md).
