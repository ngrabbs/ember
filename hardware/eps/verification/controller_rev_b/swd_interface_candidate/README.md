# SWD service package acceptance and development screen

2026-10-24, native basis `0660ad3`. Package contact/pin maps pass for development schematic use. The main 305-part EPS circuit remains unchanged. This checkpoint does not qualify the SWD circuit, stock lands, assembly, flight operation or partial-power behavior.

Run `python3 verify_parts.py`, `python3 calculate.py`, then `python3 hash_evidence.py --check` from this directory. `verified.json` binds saved native sources; `physical_map.csv` contains all26 raw objects, including three mechanical holes. `readback.json` retains supported Konnect saved-file queries. The CLI XML/ERC/PDF are unmodified exports recorded in `cli_commands.json`.

## Exact maps and physical limitations

* Tag-Connect stock symbol/footprint: TC2030-CTX-NL external cable, six PCB contacts plus three unnumbered NPTH alignment holes. PCB component-side top row2/4/6, bottom1/3/5. Contact1VTref,2SWDIO,3NRST,4SWCLK,5GND,6optionalSWO. Cable contact-face views are mirrored relative to the PCB top. The six contacts have copper/mask and **no paste**. Old logical J100's pins3/4 must exchange functions when the physical six-contact interface replaces it. There is no soldered connector to purchase for the target.
* TMUX1511PWR: approved custom five-unit review symbol, unchanged stock TSSOP-14. Exact fourteen-pin TI map queried and compared with saved instances. Channels preserve bidirectional S/D and input SEL electrical types. The API-supported rectangular functional units place SEL on the left below S, rather than beneath the rectangle; this is a recorded presentation deviation, with clear names and active-high closure callout. Green `CUSTOM—REVIEW REQUIRED` text is the approved body-color alternative; no claim of a green body or complete library-default metadata. All instance MPN/package fields are saved. Four prior review-library symbol subtrees and the top-level structure remain exact.
* TPS3839K33DBZR: unchanged stock TPS3839DBZ/SOT-23. Pin1GND,2push-pull RESET,3VDD, no exposed pad. This supervisor qualifies switch supply independently of MCU NRST.

Generic stock lands differ from manufacturer examples. TMUX pads1.475×.4mm atX±2.8625 versus TI1.5×.45 at±2.9; TPS pads1.475×.6 at±.9375 versus TI1.3×.6 at±1.05. Stock courtyards do not fully cover maximum body flash plus clearance. Reserve at least **7.70×5.90mm** for TMUX and **3.86×4.04mm** for TPS in future layout; no stock footprint was modified. Tag's stock7×4mm courtyard does not encode its central no-routing region,0.508mm other-signal clearance, mating head, axial insertion or underside alignment-pin access. The16mm stack gap does not prove service-cable fit.

## Electrical screen, separate from package inspection

`calculate.py` verifies the exact330Ω MPN `TNPW0603330RBEEA` against accepted frozen UART R800, using0.1% plus25ppm/K over65°C and4.5Ω switch on-resistance. Under3.2328–3.3244V rail, probe VOL≤.4V and10µA digital load guard, target SWDIO low is≤.49849V. The clock probe must provide at least2.34709V high under load; require≥2.4V from the actual probe. Loaded VTref is≥3.22680V for1mA plus10k bleed. These are conditional requirements, not measured debugger specifications.

TPS selector load is≤.34132mA using four2µA input bounds and10k pulldown; within its.5mA drive row. Normal high margin is1.6328V; low margin only50mV. K33 threshold2.857–2.974V, release120–350ms;29mV hysteresis and20µs assertion are **typical only**. MCP809-3002 also has typical-only assertion and does not remove this gate. Correct reset atVDD=.6V is tested with only1µA load, less than this selector load.

With56pF assumed load,330Ω+Ron adds41.3ns10–90% RC edge time. A10k passive rise is1.234µs. NRST100n gives32.45µs discharge and1.003ms release time constants; propose≥10ms reset assertion while retaining actual STM32 reset/probe pulse verification. Initial100kHz is a development starting point, not a cable/turnaround guarantee. New target NRST10k is necessary: the main graph currently contains C112.1/U100.6/J100.4, without an external pullup.

TMUX off leakage±2µA is specified atVDD=0. Conditional held-zero bleed budgets are20.05mV per10k node,94.25mV per47k and80.21mV from four paths into a10k rail bleed. These do **not** establish floating-rail equilibrium, nonzero brownout leakage or whole-EPS inhibit. Rapid collapse/recovery, injection, ESD, ground offset, all-path leakage, exact NRST limits, actual probe output/VTref/clock/turnaround and full-temperature behavior remain open. No MCU-enable dependency is proposed.

## Actual rendered inspection

`symbols.png` is the actual ANSI B fixture page, and `symbol_detail.png`, `tmux_units_detail.png`, `supervisor_detail.png` are inspected details. The green marker and closure truth statement are visible. `J1/U1/U2_{copper,mask,paste,fab,silk}.png` are individual crops of actual saved-board CLI SVG exports, inspected at useful scale. Full-board plots are mostly blank because of the sheet origin and are not used alone for acceptance. Tag no-paste and alignment holes, all IC contacts, keys and layer geometry were inspected against source figures.

Inherited fabrication reference/value text intersects some tiny number strokes (especially J1/U2); the individual crops expose this limitation rather than hiding it. Numeric maps are independently corroborated by raw queries/native pad coordinates. No clear-all-fab-label claim is made. Board Value remains the generic stock-footprint name because supported closed-board edits do not expose instance Value editing; exact schematic MPN and reference-linked package maps are authoritative here.

All fixture leads are intentionally unwired: CLI reports34errors/0warnings (23unconnected pins,6undriven power inputs,5undriven inputs). No fake source/NC flags hide these. This is a physical package fixture, not an electrical application circuit.

## Native boundary and preservation

Only the review-library append and the new disposable schematic/project/PCB/table are protected-source changes. Main EPS and historical sources/evidence:306 byte-frozen files, plus exact preservation of four existing library symbols/top-level structure; all five specified preexisting progress artifacts remain exact. The library itself is intentionally appended and is not counted byte-frozen. Runtime `.history`, embedded`.git`, locks, PRL, caches and backups are excluded from portable manifests, never deleted or claimed byte-frozen.

The manager IPC endpoint originally did not expose the standalone editor. After clean GUI closure, Konnect confirmed IPC unreachable and safely used its supported revision-checked closed-board file placement/readback. No socket/config/process workaround was used. Saved-file queries are not described as live-board acceptance. The scratch project normalization is included in final native hashes. No real EPS circuit placement or production PCB synchronization was performed.

Manufacturer PDFs, URLs and hashes are in `sources.json`; actual pin/application/package pages are retained as PNGs. Primary ST UM2910 text supports that STLINK-V3MINIE does not provide target power; its local PDF download failed, so no local ST screenshot inspection is claimed.
