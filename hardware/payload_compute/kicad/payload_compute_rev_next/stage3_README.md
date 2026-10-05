# Stage 3 — committed source/mode and qualified watchdog control

2026-10-05. This is a completed bounded schematic capture, with 132 physical components and 105 exported nets across six sheets. It is not a completed payload schematic or a fabrication/flight release.

Open [the current six-page PDF](payload_compute_rev_next-stage3.pdf), [root schematic](payload_compute_rev_next.kicad_sch), [mode/watchdog drawing](05_mode_watchdog-stage3.png) and [source-lock drawing](06_source_lock-stage3.png). [Exact saved topology](payload_compute_rev_next.net), [raw query/check evidence](stage3-evidence.json), [repeatable checker](check_stage3.py) and [results](stage3-check-results.json) accompany it. Run `python3 check_stage3.py`. Frozen stage1.net and stage2.net retain the preceding milestones; their historical checkers remain available.

## Captured circuitry

Sheet 05 contains a TPS3700DDCR external IHU receiver and grounded-jumper detector, buffered AON reset, startup mode latch, TPS3431SDRBR watchdog, and buffered reset/readiness/permission gates. Sheet 06 contains immutable source-request latches, three-bit one-hot decoding, mode-qualified choices and a source lock cleared only by AON reset. Their owned outputs are physically wired through the root hierarchy into the existing reset/run core. +3V3_AON spans the real buck output and all new supply/bypass pins. No missing source or control driver is hidden by a power flag.

TPS3700DDCR, TPS3431SDRBR, SN74LVC1G14DBVR and SN74LVC1G32DBVR received exact manufacturer lead–symbol–pad checks and disposable placed/readback/render acceptance before real placement. See [package acceptance](../../design/validation/payload_control_acceptance/library_acceptance.md). Reused packages were queried again. The mode latch is **SN74LVC1G373DBVR, six leads**; it is not a DCUR eight-lead part. Each new IC has a 100 nF bypass capacitor. Footprint and stencil acceptance is provisional for prototype construction, not a manufacturing release.

## Physical logic and ownership

`AON_RESET_RAW_N` is the supervisor open-drain node; U303 independently buffers it into `WDT_ENABLE`, while U304 produces clean `AON_RESET_N` for the core and both lock clears. Watchdog enable never feeds back from watchdog/reset outputs.

The jumper applied to ground selects bench; open selects flight. The filtered comparator output is transparent through U306 until the first `MODE_LOCK_CLK` rising edge sets `MODE_LOCKED`. Bench state and its inverse remain fixed until AON reset. Ordinary MCU/debug reset cannot change mode or source choice.

The three `USB_REQ`, `BENCH_REQ`, `STACK_REQ` bits remain transparent until the first `SOURCE_LOCK_CLK` edge sets `SOURCE_LOCKED`. Hardware rejects 000 and multiple asserted bits. Committed choices require AON reset released, both locks committed, exactly one bit, and bench mode for USB/bench or flight mode for stack:

```
CHOICE_LOCKS_VALID = AON_RESET_N & MODE_LOCKED & SOURCE_LOCKED
USB_CHOICE_ONLY   = CHOICE_LOCKS_VALID & USB_ONEHOT   & BENCH_LATCHED
BENCH_CHOICE_ONLY = CHOICE_LOCKS_VALID & BENCH_ONEHOT & BENCH_LATCHED
STACK_CHOICE_ONLY = CHOICE_LOCKS_VALID & STACK_ONEHOT & FLIGHT_LATCHED
MODE_PERMISSION  = AON_RESET_N & MODE_LOCKED &
                   (USB_CHOICE_ONLY | BENCH_CHOICE_ONLY |
                    (STACK_CHOICE_ONLY & IHU_EN_VALID))
```

These are logical requests, not proof of available power. `SOURCE_OK_AON` retains the existing 10 kΩ default-low bias and has no invented driver: raw voltage windows, valid PD contract, exclusive laboratory attachment, selected bus/inrush/fault conditions and protected main admissions remain future capture.

TPS3431 WDO and ENOUT share `MCU_NRST_N` with a 10 kΩ AON pull-up. Future MCU/debug reset connections must be open drain sinks; an external push-pull high is incompatible. `WD_RESET_VALID` is the buffered active-high combined reset release. `MCU_CONTROL_READY = AON_RESET_N & MCU_READY & WD_RESET_VALID`; MCU_READY alone cannot grant power. Loss of qualified readiness clears the existing run permission. Recovery requires a fresh arm edge; it cannot automatically re-arm the payload.

## Startup and firmware contract

The mode sampling delay is a firmware qualification obligation; this circuit does not enforce the delay itself. Wait at least 20 ms after clean AON reset release and observe BENCH_LATCHED stable for at least 10 ms. Fix the jumper throughout sampling. Apply a 1 ms MODE_LOCK_CLK high pulse with at least 1 ms setup/hold. An early erroneous pulse can commit the wrong mode until AON reset. Commit mode before source choice. Hold all request bits stable at least 1 ms before and after the first 1 ms source-lock pulse. Request/clock inputs have 10 kΩ default-low biases.

Watchdog SET1 is tied high and CWD intentionally unconnected, selecting the fixed 1.36–1.84 s watchdog timeout. Account for 150 µs WDI enable setup, 300 µs startup and 381 µs CWD evaluation; reset pulse is 170–230 ms. WDI falling pulses must meet ≥50 ns and its direct future MCU output must satisfy VIH ≥0.8 VDD (2.706 V at maximum AON), not merely a generic 2.4 V gate guarantee. A service interval ≤250 ms is a proposed firmware margin. The watchdog can reset an unprogrammed MCU repeatedly; default-low MCU_READY keeps main power off.

## Bias, levels and AON allocation

The IHU divider is 10 kΩ/5.1 kΩ ±1%; a proposed 3.0 V minimum high produces at least 0.9998 V sense and 0.4 V maximum low produces at most 0.1370 V, including ±25 nA input leakage. This brackets the comparator's 396–404 mV rising and 387–400 mV falling thresholds. The external IHU output remains proposed 3.3 V push-pull/default low, with exact connector/fault envelope pending. Its divided input uses TPS3700 rather than feeding a powered-down LVC input directly.

Each 10 kΩ default bias can load a high output by 0.342 mA at maximum AON/minimum resistance. Qualified push-pull gates drive the core inputs; equal 10 kΩ open-drain pull-up/pull-down dividers were not used. Dedicated WDT_ENABLE load is about 34.9 µA; clean reset fanout allocation is 74.2 µA including eight 5 µA input leakages. Both remain below the LVC 100 µA low-level test allocation. Additional future fanout requires review.

The captured control circuits allocate **0.036 W** at maximum AON, leaving **0.164 W** of the reduced 0.200 W bootstrap planning target for future MCU/receivers. New circuitry allocates 0.322 mA IC static consumption, fourteen 10 kΩ loads, four 100 kΩ loads and a conditional **1 mA reserve**. Existing core adds twelve 10 kΩ loads and 60 µA IC allowance. The reserve covers unplaced CMOS input leakage/fanout and low-rate lock/WDI edge charging; it is unmeasured and does not bound MCU clock activity, camera activity, bypass/output capacitor charging or buck cold startup. The 0.250 W ceiling and later 0.350 W active target do not prove pre-PD startup. Preserve [bootstrap input requirements](../../design/bootstrap_input_contract.md).

## Qualified prototype limits

Near-rail open-drain lines use SN74LVC1G17 Schmitt receivers. Its threshold tables are discrete VCC test points; interpolation across the allocated AON envelope is not asserted as a guarantee. Validate threshold margin, reset/comparator/watchdog release ramps, hysteresis and actual output edges over supply/temperature. TPS3431 output levels and its partial-power/startup sequence need waveform measurements. A 100 kΩ enable pull-down alone does not guarantee low during every partial-power state: 10 µA Ioff could imply 1 V. Validate AON reset guards and enable sequencing rather than assuming that bias proves safe behavior.

Measure worst source/current-limit cold startup of the VIN-enabled buck through slow-ramping eFuses, output capacitor charging, repeated reset/recovery, detach and full AON loss. Validate persistent unclean-session firmware policy before allowing automatic laboratory startup after an interrupted session. Physical flight inhibit, entry fuse/TVS/harness coordination, USB/PD inlet capacitance, main power, STM32 package/capture, CAN/debug, cameras and layout remain outside this stage.

## Exact ERC and verification status

All six sheets pass wire endpoints, component pin checks, shorts, orphan items and symbol overlaps with zero findings; hierarchy pin consistency has zero issues. Label-inclusive renders and all six PDF pages were reviewed. The checker reconstructs the old topology plus the independently specified new physical-pin map, then checks all 105 nets and 132 unique references. Exported physical-pin gate evaluation passes 256 source/mode combinations and eight qualified-readiness combinations. This proves the captured ideal logic/connectivity, not timing or analog behavior.

Direct ERC deliberately retains **31 errors and 3 warnings**:

- 25 open root boundaries: USB_ENTRY_POS, BENCH_ENTRY_POS, STACK_ENTRY_POS, SOURCE_OK_AON, MCU_MAIN_REQ, ORIN_5V_WINDOW_OK, SHUTDOWN_OK_AON, MCU_ARM_QUAL, MCU_ARM_CLK, POWER_PERMISSION, MAIN_BUCK_REQUEST_OK, RUN_LATCH, IHU_PAYLOAD_EN, BENCH_JUMPER_N, MODE_LOCK_CLK, MCU_WDI, MCU_READY, MCU_NRST_N, USB_REQ, BENCH_REQ, STACK_REQ, SOURCE_LOCK_CLK, SOURCE_LOCKED, WD_RESET_VALID, IHU_EN_VALID.
- Four missing external power drivers: U1.9 return and U201/U211/U221.1 source inputs.
- Two retained native-OR power-output conflicts: U201.15–U211.15 and U211.15–U221.15, qualified by the TPS2660 native-OR application topology and still requiring leakage/dynamic qualification.
- Three isolated IHU_PAYLOAD_EN labels at its one-passive-input external boundary. Konnect ERC serialization reports the AON sheet, but label queryback locates them on sheet 05; no stale IHU labels exist on the buck sheet.

These are exactly asserted by the checker, not suppressed. Konnect file-based schematic operations committed the sources; final file hashes/queryback/netlist/PDF confirm readback. `save_project` is PCB-only IPC and unavailable in this closed-editor workflow. A transient CLI lock disappeared before the final AON documentation correction. The stale inherited bootstrap-pending annotation was replaced through Konnect; refreshed AON render and full PDF now state captured native-OR feeds and pending entry/startup qualification.
