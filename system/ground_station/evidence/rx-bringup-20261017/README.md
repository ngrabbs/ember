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
