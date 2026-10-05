# Bench-mode sampling and IHU permission contract

2026-10-04. Disposable sampler and separate receiver/permission study implemented;
source-admission circuitry and carrier integration remain open.
See [sampler evidence](validation/payload_mode_acceptance/README.md).

The historical positive-jumper/Schmitt-only study below is superseded for the
real stage 3 capture by the [source hardware contract](source_hardware.md).
The applied jumper now grounds an active-low sense node; a TPS3700 provides
fixed-threshold sensing and a near-rail Schmitt receiver conditions its output.
Explicit firmware-timed locking preserves the accepted startup-only behavior.

## Startup-only mode

The physical jumper connects AON 3.3 V to a 1 kΩ series resistor, with
10 kΩ pulldown and 100 nF filter. SN74LVC1G17DBVR converts the filtered
signal to a fast edge. SN74LVC1G373DBVR captures that signal when its latch
enable goes low. A SN74LVC1G74DCUR lock flip-flop has D and PRE_N tied high,
CLK directly connected to MCU_MODE_LOCK_CLK and CLR_N connected to the AON
supervisor reset. Q_N drives the mode latch enable. Repeated clock pulses
cannot reopen the latch: they sample the same constant high D.

`BENCH_AUTH = BENCH_LATCHED & MODE_LOCKED & AON_RESET_N`.
Before locking, the mode latch follows the jumper but cannot authorize bench
startup. After locking, changing the jumper cannot change the stored mode.
Only AON reset unlocks sampling. MCU debug/watchdog reset must be separate
from AON_RESET_N. A firmware restart reads existing MODE_LOCKED and
BENCH_LATCHED and preserves them. A brownout may reset the mode; switched
loads must already be disabled, and a full startup sequence follows recovery.
This is not a spacecraft inhibit or single-fault-tolerant interlock.

Startup firmware keeps main request, alive and run arm low; waits for AON
reset release; checks BENCH_SENSE remains stable for a provisional 20 ms;
then sends a 1 ms lock pulse. Wait another 1 ms, read back mode/lock, and
only then select a source and start the converter sequence. Do not move the
jumper during this sampling interval: mechanical activity near latch closure
can violate setup/hold. The latch needs 1.5 ns setup and hold at 3.3 V ±0.3 V,
-40 to 125°C; the firmware waits do not eliminate that asynchronous hazard.

## Electrical budget and qualification

Assuming 1% resistors, candidate AON 3.2505–3.3825 V and buffer input
leakage ±5 µA, filtered steady high is at least 2.945 V; open-jumper low
at most 50.5 mV. See [AON budget](aon_supply_budget.py).
The 5 µA allocation is conservative relative to the buffer input specification.
Filter open discharge time constant is nominal 1 ms; closed charging is
nominal 90.9 µs. Capacitance tolerance, bias, leakage and jumper bounce require
qualification. The RC node must not directly drive the ordinary CMOS latch:
its edge-rate requirement is why the Schmitt buffer is present.

SN74LVC1G17 threshold tables specify individual supply test points (including
3.0 V); this study does not interpolate them into a guaranteed 3.2505–3.3825 V
threshold envelope. Close that guarantee/qualification before system acceptance.
Ioff specifies power-off leakage, not a guaranteed output logic state during
arbitrary supply ramps. Bench authorization is masked by reset and mode lock
within valid logic operation; ramp/partial-power fail-off remains a hardware test.
Jumper/header and passive MPNs/footprints are still conceptual. Each IC needs
local decoupling in PCB layout; schematic drawing distances are not layout proof.

## IHU PAYLOAD_EN contract

User selected the proposed interface on 2026-10-04: **3.3 V push-pull,
default low** on stack H1.50. It is a design contract, not verified IHU hardware.
IHU firmware/hardware must keep it low during startup, reset and an unavailable
output supply. Configure the output low before enabling the GPIO driver.
Normal CAN stop holds it high until verified payload power-down acknowledgement;
low is immediate hardware permission removal.

Follow-up [receiver/permission study](permission_control.md) reduces the proposed
series resistor to 100 Ω to preserve input slew and adds both-source rejection.
Its wired disposable schematic, physical NAND mapping and exported Boolean
topology checks pass; physical timing and carrier integration remain open.

Receiver proposal: payload-side 10 kΩ pulldown, input current limiting and a
partial-power-safe receiver. Require at the payload connector VOH ≥3.0 V,
VOL ≤0.4 V under the selected load, and agree the supply/ground offsets and
edge rate. A 1 kΩ series / 10 kΩ pulldown allocation into a 5 µA input gives
≥2.72 V received high; missing drive gives ≤50.5 mV. Actual receiver selection,
ESD/transient envelope and input/power-off behavior remain open; no unvalidated
pull-up to payload AON may back-power the IHU output.

The complete permission function must select the mode, not blindly OR both
requests:

```
MODE_PERMISSION = MODE_LOCKED & AON_RESET_N &
  !(LAB_SOURCE_SELECTED & STACK_SOURCE_SELECTED) &
  ((BENCH_LATCHED & LAB_SOURCE_SELECTED & LAB_SOURCE_OK) |
   (!BENCH_LATCHED & STACK_SOURCE_SELECTED & STACK_SOURCE_OK & IHU_EN_RX))
```

Selected means exclusive, hardware-controlled source admission, not merely
voltage present. Bench ignores IHU requests; stack ignores lab feeds. Missing
IHU drive removes stack permission independently of firmware. This function
is wired in the separate permission study; upstream source-admission gates
and integration into the sampler/carrier remain open. Fault recovery still cannot
rearm the separate run latch without a fresh qualified arm edge.

## Checks and sources

Run `python3 design/bench_mode_study.py` and
`python3 design/validation/check_mode_study.py`. These check ideal stored-mode
behavior, permission truth tables, DC allocations and exported/library evidence.
They do not validate asynchronous races, source switching or flight operation.

- [TI latch datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g373.pdf), SCES528F, pin map p3, timing p6.
- [TI Schmitt buffer datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf), SCES351Y, pin map p3, threshold table p6, DBV0005A land drawing 4214839/K.
- Existing flip-flop/gate maps: [run-latch acceptance](latch_library_acceptance.md).
