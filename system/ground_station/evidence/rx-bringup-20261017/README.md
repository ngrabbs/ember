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
