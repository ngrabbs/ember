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

Wait for `BPSK_RX_READY`. On IHU issue `normal`; on COMMS press `a` (no Enter);
then IHU `hello` and wait for confirmation. IHU `uhf run 120 10` starts the
finite two-minute heartbeat/system/EPS cycle. The receiver can stay running
between runs; renew COMMS `a` and explicitly start another IHU run as needed.
COMMS `x` stops its service; IHU `uhf stop` stops future telemetry production.
Receiver Ctrl-C saves results and closes reception. No receiver command starts TX.

Open the existing EPS or health dashboards with `c=ember-uhf__realtime`, not
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
