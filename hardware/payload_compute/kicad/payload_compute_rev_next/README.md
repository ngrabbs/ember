# Payload compute next prototype — current stage 3

Committed source/mode locks and qualified watchdog control now connect to the existing AON/reset/run hierarchy. See the [stage 3 capture and qualifications](stage3_README.md), [current six-page PDF](payload_compute_rev_next-stage3.pdf), and run `python3 check_stage3.py`. The full payload schematic remains incomplete and is not released for layout, fabrication or flight.

Historical [stage 2 record](stage2_README.md) and its frozen stage2.net remain available.

## Historical stage 1 record

2026-10-05. First real hierarchical schematic capture, separate from the
converted carrier and all disposable studies. **Stage 1 is complete as a
bounded capture milestone; the whole payload schematic is incomplete.**

Open [the project](payload_compute_rev_next.kicad_pro) and
[root schematic](payload_compute_rev_next.kicad_sch), or inspect the
[three-page PDF](payload_compute_rev_next-stage1.pdf).
The blank PCB was created by Konnect's project tool; it has no components,
mechanics, routing, manufacturing outputs or layout acceptance.

## Implemented

- Root: two child sheets, direct AON supply interconnection, shared ground,
  named open interfaces and architecture/release notes.
- [AON supply](03_aon_supply.kicad_sch): LMR36506R3RPER fixed 3.3 V,
  RT tied to internal VCC for nominal 1 MHz, nominal 15 µH and two 22 µF
  output capacitors, input bypass, bootstrap capacitor and unloaded internal
  VCC bypass. PGOOD intentionally unused.
- [Reset/run core](04_reset_run_core.kicad_sch): TPS3808G33DBVR, three
  SN74LVC1G11DBVR gates and SN74LVC1G74DCUR fresh-arm latch, five 100 nF
  decouplers and twelve 10 kΩ biases. CT and inverted Q intentionally unused.

Thirty physical components, six ICs / 41 IC pins and 22 exported nets.
The single derived `+3V3_AON` net joins 18 physical output, bypass,
supervisor supply/sense, gate supply and latch supply/preset pins. Stack
`+3V3`/`+5V` are absent; main/peripheral rails are still future domains.

The exact existing package maps were re-queried and joined to the placed
instance pin numbers and footprints. See
[AON package acceptance](../../design/aon_library_acceptance.md) and
[control package acceptance](../../design/latch_library_acceptance.md).
The AON footprint retains documented prototype land/stencil deviations;
physical-map correctness is not an assembly qualification. Passive footprints
and production MPNs remain unassigned intentionally.

## External interface contract

| Interface | Polarity / implemented behavior | Required future owner |
|---|---|---|
| AON_BOOTSTRAP_IN / GND | Protected supply and return; no input-source PWR_FLAG | Independent limited, reverse-isolated bootstrap feeds and entry protection |
| SOURCE_OK_AON | High permits source; R109 defaults low | Immutable source lock, raw windows and branch qualification |
| MODE_PERMISSION | High permits run; R110 defaults low | Once-sampled bench selection and live IHU permission hardware |
| MCU_MAIN_REQ | High requests main supply; R102 defaults low | STM32 sequencing / bounded stop handling |
| MCU_CONTROL_READY | High is qualified control/watchdog readiness; R103 defaults low | External watchdog and healthy supervisor qualification; never a stuck-high GPIO |
| ORIN_5V_WINDOW_OK | High means qualified main supply; R111 defaults low | Main monitor/reference readiness and AON-safe receiver |
| SHUTDOWN_OK_AON | High means module shutdown is not asserted; R112 defaults low | AON-safe module shutdown receiver |
| MCU_ARM_QUAL | D input; R104 defaults low | Fresh qualification state from supervisor |
| MCU_ARM_CLK | Rising edge arms; R105 defaults low | Direct supervisor pulse after qualification |
| AON_RESET_N | Low during AON fault; 10k AON pull-up | Future supervisor/source/control reset consumers |
| POWER_PERMISSION | High only with reset released, valid source and mode | Future control consumers |
| MAIN_BUCK_REQUEST_OK | Logic request; R106 defaults low | Partial-power-safe physical buck EN driver; not a direct AON-to-buck wire |
| RUN_LATCH | Q permission; R107 defaults low | Jetson POWER_EN interface and actual module-reset/peripheral gating |

All positive-true boundary inputs have defined low bias. At the allocated
maximum AON voltage, a 10k ±1% pulldown needs up to about 0.342 mA from its
high-state driver. Future drivers must meet LVC VIH ≥2.0 V and VIL ≤0.8 V
with these loads, leakage, ramp and partial-power conditions. Use a buffered
push-pull receiver or separately budget any open-drain pull-up: **a 10k
pull-up against these 10k pulldowns produces approximately half supply and
does not meet VIH.** Missing receivers are not accepted by nominal voltage
alone, and module 1.8 V signals must not connect directly.

`POWER_PERMISSION = AON_RESET_N & SOURCE_OK_AON & MODE_PERMISSION`.
`MAIN_BUCK_REQUEST_OK = POWER_PERMISSION & MCU_MAIN_REQ & MCU_CONTROL_READY`.
`RUN_CLEAR_N = MAIN_BUCK_REQUEST_OK & ORIN_5V_WINDOW_OK & SHUTDOWN_OK_AON`.
Faults asynchronously clear Q. Recovery does not generate an arm edge.
Firmware keeps CLK low, sets D, waits at least 1 ms, pulses CLK at least
1 ms, lowers CLK and then D. Actual edge races, metastability and ramps
remain hardware qualification items.

CT open gives the accepted 12–28 ms reset-release interval, qualifying AON
only. DC allocation is 3.2505–3.3825 V against maximum G33 release
3.1928 V (57.7 mV static margin). Startup/transients are not measured.
The bootstrap target remains 0.200 W, with the previous 0.250 W ceiling;
future protection/PD/indicator loads must be included in the attach budget.

## Saved verification

[Exported netlist](payload_compute_rev_next.net),
[query-back/check evidence](stage1-evidence.json),
[direct ERC](stage1-erc.json),
[expected physical topology](stage1-expected-topology.json), and
[repeatable check results](stage1-check-results.json).
Run `python3 check_stage1.py` here.

Root and both child sheets each report zero floating wire ends,
unconnected unmarked component pins, shorts, orphans and symbol/label-origin
overlaps. Hierarchical pin/label validation reports zero issues. Rendered
images were inspected for functional flow, label/text overlap and page bounds;
the core heading was moved above the reset pull-up to clear its rail label.

**ERC is not clean for the whole project: 15 errors / 0 warnings.** Every
remaining finding is classified and the checker rejects any additional one:

- Two `power_pin_not_driven` findings represent the missing protected
  bootstrap source and return. The report selects U1.3 on the VIN/EN net
  and U1.9 on ground. No flag hides those missing entry circuits.
- Nine open input sheet pins: bootstrap input, SOURCE_OK_AON,
  MODE_PERMISSION, MCU_MAIN_REQ, MCU_CONTROL_READY, ORIN_5V_WINDOW_OK,
  SHUTDOWN_OK_AON, MCU_ARM_QUAL and MCU_ARM_CLK.
- Four open output sheet pins: AON_RESET_N, POWER_PERMISSION,
  MAIN_BUCK_REQUEST_OK and RUN_LATCH. Their consumers have not been captured.

The sole PWR_FLAG declares the **implemented buck output through L1**, on
the actual derived +3V3_AON net; its mid-wire junction is present. It does
not stand in for a connector, permission receiver, watchdog or input source.
Future open ports are left open rather than marked permanently no-connect.

Konnect's schematic writes committed each edit and returned file readback.
Netlist/ERC/PDF were exported from saved files. `save_project` was attempted
but is a PCB IPC-only operation and returned connection refused with KiCad
closed; no live PCB save is claimed or needed for these file-based schematic
edits. Initial root label stubs were replaced by direct power wiring and open
future ports after checking direct ERC and the actual full netlist. Output
sheet pins were re-added to update their right-edge angle, and a 0.01 mm
off-grid AON sheet-width gap was corrected on the 1.27 mm grid.

The PDF contains root, AON and core in that order. Child sheet IDs are 2/3
and 3/3; root's footer also reads 3/3. Supported Konnect page renumbering
only changes children, so this cosmetic root-page metadata issue remains
documented without editing protected sources directly. File names and sheet
names identify the pages unambiguously.

## Next bounded capture

Accept and build protected entry/bootstrap and the source/mode/watchdog
interfaces, then connect these existing ports. The old NMOS admission clamp
and old Schmitt jumper sampler were not copied. Follow the
[schematic-start baseline](../../design/schematic_start.md) and
[source hardware contract](../../design/source_hardware.md), accepting each
new physical package before placement. Conservative 7 W bring-up remains;
15 W operation, portable power and low-end battery startup need qualification.
This stage does not prove whole-board hard kill, physical POWER_EN safety,
rail discharge, synchronized Jetson acquisition or fabrication readiness.
