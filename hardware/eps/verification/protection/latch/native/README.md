# Native latch and source-short corrections

2026-10-23. Current development circuit: `hardware/eps/studies/recovery_protection/recovery_protection.kicad_pro`, root source sheet plus attached `recovery_rail_final.kicad_sch`. Only these schematics and the required project net-class setting changed. No existing PCB, converter source, controller source or library changed.

## Electrical and metadata verification

[Fresh XML](protection.xml), [canonical netlist](protection.net), [explicit verifier](verify_native.py), [result](verified.json), and [current 83-part development BOM](development_bom.csv) supersede the historical 81-part protection exports. All **41 endpoint sets** are asserted, including 37 connected nets and 4 NC pins. All 81 original physical UUIDs persist; 75 unrelated component records are identical. The only existing value/MPN changes are C9, C112, C119, R107, R108 and R5. R5 preserves 27.8 kΩ / 0.1% / 25 ppm/K but changes to TNPW121027K8BEEA, stock 1210, 0.33 W P70 general operation. R115 and L2 are the only new physical parts.

R115 connects +5V to GND. L2 splits existing SOLAR_PERMITTED from internal SRC_FILTERED; the former input endpoints now follow L2. No existing external interface was renamed. [Net classes](netclasses.json) contain 37 exact connected-net assignments, including SRC_FILTERED in POWER. Default routing dimensions are not accepted fabrication/current rules. The post-L2 power flag represents the legitimate externally powered passive filter, whose drive ERC cannot infer.

[Konnect ERC](erc-konnect.json) and [direct CLI ERC](erc-cli.json) have **0 errors / 1 warning**, the existing single-pin REC5_RESET interface. [Final per-sheet readback](final-readback.json) reports no floating ends, unconnected required pins, shorts or geometry overlaps. [Exported geometry](layouts.json), [geometry verifier](verify_geometry.py), and [result](geometry.json) separately check the electrical grid, four-direction endpoints and collinear wire overlaps. S03 four-way-junction severity persistence remains API-blocked; a separate geometry pass does not satisfy that settings gate.

[Checkpoint](checkpoint.json) records pre-change hashes and Git revision. PCB hashes remain unchanged. All native writes used Konnect 0.11.1 eadbe451 and KiCad CLI 10.0.0; the root agent was the sole mutation owner for this bounded correction. KiCad was not bypassed with file rewrites.

## Library evidence

No configured KiCadLib nickname was present in the 222 global symbol libraries; the project symbol-library list was empty. Stock Device:R and Device:L pins were queried before wiring; the reused capacitor symbols/1210 land assignments retain prior identity. R115 uses the already-used stock 1206 resistor land and manufacturer ordering rule. New resistor/capacitor ordering identities remain subject to procurement confirmation.

XAL1010-472MED is a nonpolar two-terminal part: symbol pins 1/2 join stock footprint pads 1/2; either electrical orientation is valid. The stock footprint query gives centers ±3.325 mm, pad size 2.38 × 9.0 mm, and 10.5 × 11.8 mm F.Fab outline. These match the manufacturer recommended 6.65 mm center spacing and maximum body drawing on Document 804-4, 2026-02-25, which was downloaded, rendered and inspected. The marked short winding lead is an EMI orientation preference for later PCB placement, not diode-like electrical polarity. No disposable or production PCB was altered; complete package/assembly/physical-fit acceptance is not claimed.

## Actual rendered inspection

The current [source full page](source.png) and [rail full page](rail.png) were opened and inspected independently of connectivity. Detail inspections cover [source input/L2](source-input.png), [source timer](source-timer.png), [rail bleeder](rail-bleeder.png), [rail timer](rail-timer.png), [rail gate slew](rail-gate.png), and [rail feedback divider](rail-feedback.png). L2 has exposed wires on both sides and a distinct filtered rail; R115 branches from the existing output-bank bar with a downward ground and visible wire stubs. The rail title now states 5.27 V and the sequencing note includes both a 5 ms admission ramp and 20 ms settling. An initially overlapping source annotation was removed through Konnect and re-created in the clear upper-right area; final images have the corrected arrangement. Both sheets remain ANSI B. Historical page-ID inconsistency remains visible.

Required visible Arial/orientation-aware parameter blocks remain **S11 API-blocked**; query-back metadata is not a presentation acceptance. Existing approved custom Panasonic review candidates retain their status. No custom symbol or footprint was authored.

## Engineering status

The parent [latch/SOA record](../../../../design/rev_b_5v_latch_and_mosfet_survival.md) controls electrical acceptance. Native ERC, endpoint assertions and rendered inspection do not qualify low-VCC clamp accuracy, hot SOA, capacitor/magnetic/pulse limits, actual load transients or flight hardware.
