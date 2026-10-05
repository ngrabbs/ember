# Run latch and startup qualification

> 2026-10-05: this accepted core is now captured in the separate
> [real prototype stage](../kicad/payload_compute_rev_next/README.md).
> The standalone evidence below remains the original study record.

2026-10-04. Bounded circuit proposal, not integrated into the carrier.
See the [rendered circuit and evidence](validation/payload_latch_acceptance/README.md)
and [physical pin-map acceptance](latch_library_acceptance.md).

## Circuit

TPS3808G33DBVR supervises the always-on 3.3 V supply. Three
SN74LVC1G11DBVR AND gates form:

```
POWER_PERMISSION = AON_RESET_N & SOURCE_OK_AON & MODE_PERMISSION
MAIN_BUCK_EN = POWER_PERMISSION & MCU_MAIN_REQ & MCU_ALIVE
RUN_CLEAR_N = MAIN_BUCK_EN & 5V_WINDOW_OK & SHUTDOWN_OK_AON
```

SN74LVC1G74DCUR has PRE_N tied high and CLR_N driven by RUN_CLEAR_N.
D is MCU_ARM_QUAL; CLK is a direct, ungated MCU_ARM_CLK.
A rising clock samples D only while clear is released. Fault recovery does
not create a clock edge. Fault clear wins in the ideal model; actual recovery,
setup/hold timing and asynchronous edge races require electrical validation.
Pin 5 is Q; pin 3 is inverted Q and is intentionally unused here.

Five 100 nF decouplers and eight 10 kΩ bias resistors are study values;
exact passive MPNs and placement remain open. MCU request, alive, qualification
and clock default low with external resistors. MCU_ALIVE falling clears the
latch, but a stuck-high GPIO is not an independent watchdog.

## AON reset budget

The G33 threshold is nominally 3.07 V. Use the guaranteed full-temperature
±1.5% accuracy, rather than the advertised typical 0.5% figure. Falling
threshold is 3.02395–3.11605 V. With maximum 2.5% nominal-threshold
hysteresis, maximum release threshold is 3.1928 V. The candidate
LMR36506R3RPER auto-mode DC allocation is 3.2505–3.3825 V, leaving 57.7 mV
of static release margin before additional noise/drop. This replaces the
earlier ±2% allocation and 41.2 mV margin. The regulator system-accuracy table
has specified operating conditions; this calculation does not prove actual
startup, ripple or transient performance. See [AON budget](aon_supply_budget.py).

CT is intentionally open: guaranteed release delay is 12–28 ms, typical
20 ms. This delay qualifies AON reset only; it does not establish source,
reference, main 5 V or module startup readiness. MR_N is tied high; debug
reset is outside this block. RESET_N is open drain with a 10 kΩ AON pull-up.
SENSE-to-RESET delay is 20 µs typical, not a guaranteed maximum fault bound.
Below the supervisor/logic specified power range, outputs are not assumed
valid merely because pulldowns exist. Prove POWER_EN off through ramps and
partial power in the subsequent interface study.

## Startup and stop policy

1. Reset drives request/alive/qualification/clock low. Latch stays cleared.
2. Sample and latch the physical bench jumper once. In stack mode require
   live IHU permission; bench mode permits the initial standalone boot.
3. Validate the source and AON supply. Establish the previous rail discharge
   before enabling the converter. MCU alive then main request enable main 5 V.
4. Verify monitor/reference readiness and stable main 5 V. A provisional
   100 ms stable qualification interval is an engineering choice to test,
   not a manufacturer startup requirement. Any fault restarts qualification.
5. Keep clock low, raise D, wait at least 1 ms, pulse clock high for 1 ms,
   then return clock low before lowering D. Firmware delays comfortably
   exceed the nanosecond setup/hold limits, but hardware races still need test.
6. Gate carrier I/O with RUN_LATCH AND actual module SYS_RESET_N release.
   Camera triggers also require application/camera readiness and session state.
7. Normal CAN stop finishes SD writes and Linux shutdown while IHU permission
   remains high. Module SHUTDOWN_REQ clears RUN_LATCH. Remove main 5 V after
   the module sequence and verify rail discharge before acknowledging off.
8. IHU permission loss clears both converter request permission and run latch
   through hardware. Recovery requires deliberate new qualification and arm.

Off/discharge acknowledgement must be measured or otherwise established by
validated circuitry; monitor-window low alone cannot distinguish zero volts
from a fault voltage. No fixed off interval or SD-write hold-up is proven here.
Timeout/retry policy remains bounded and must be selected with the payload team.

## Timing and next interfaces

At 3.3 V, -40 to 125°C and datasheet loading, an allocated worst path through
three gates and latch clear is 3 × 6.2 + 7.9 = 26.5 ns. This is a core logic
bound only. Receiver delays, supervisor/monitor delays, translation, trace
loading and rail decay are excluded; it is not a system hard-kill guarantee.
LVC VIH is 2.0 V at 3.0–3.6 V, so module 1.8 V SYS_RESET_N cannot drive it
directly. Input/output leakage, pull-up loading and level interfaces must be
budgeted at the actual supply corners.

NVIDIA DG-10931-001 v1.5 (February 2026), pages 17–20, supersedes the
local preliminary v1.1 timing evidence. It removes the earlier 400 ms interval;
figure 6-3 shows >64 ms POWER_EN-to-SYS_RESET release, which is not a
software timeout or permission to bypass actual SYS_RESET_N. Carrier 3.3 V
must decay within 1.5 ms and 1.8 V within 4 ms of SYS_RESET assertion.
The guide also says module-input current limiting/eFUSE must not limit reverse
current. Reconcile any proposed module output isolation with that requirement;
source-input protection is a separate function. Exact older Nano compatibility
remains unqualified.

The [bench-mode sampler](bench_mode.md) now has a checked disposable circuit.
Next circuit block: IHU permission receiver and complete source/mode gating,
5 V SHUTDOWN_REQ receiver, 1.8 V SYS_RESET receiver, fail-off POWER_EN
translation, and measured carrier-rail discharge. SN74LV1T125 is a level
interface candidate only; its datasheet has no Ioff guarantee. No candidate
is accepted merely from nominal voltage translation.

## Sources and checks

- [TI TPS3808 datasheet](https://www.ti.com/lit/ds/symlink/tps3808.pdf), SBVS050N August 2026, pin map, electrical characteristics and CT timing.
- [TI SN74LVC1G11 datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf), SCES487I November 2024, pin map and full-temperature switching limits.
- [TI SN74LVC1G74 datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf), SCES794G September 2021, function table and timing.
- [NVIDIA guide download](https://developer.nvidia.com/downloads/jetson-orin-nx-series-nano-series-design-guide), [saved v1.5 PDF](Jetson_Orin_Design_Guide_DG-10931-001_v1.5.pdf).

Run `python3 design/run_latch_study.py` and
`python3 design/validation/check_latch_study.py` from payload_compute.
Checks cover ideal logic and exported package/topology evidence, not hardware
ramps, metastability, firmware execution or flight performance.
