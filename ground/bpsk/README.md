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
