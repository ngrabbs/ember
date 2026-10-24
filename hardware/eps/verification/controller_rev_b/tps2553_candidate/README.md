# TPS2553DBVR-1 read-only library review

2026-10-24, basis `d8ad529`. **Historical read-only snapshot before construction approval.** At this snapshot no TPS native library, disposable project, real circuit or PCB mutation existed. Candidate may serve independent CAN A/B and isolated-BMS primary branches only after separate electrical selection. Construction and package acceptance do not establish fault containment. Subsequent construction approval is recorded in the rules document; new package evidence must use a separate directory and verifier.

Complete proposed rules: [rev_b_tps2553_library_rules.md](../../../design/rev_b_tps2553_library_rules.md). Existing [branch screening](../branch_selection/README.md) is frozen historical evidence, including its unbounded initial response/shared-load gaps; it is not reused as isolated-BMS branch acceptance.

## Source and actual inspection

Downloaded the full **44-page manufacturer PDF** from [TI](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf), saved as `tps2553-1.pdf`; SHA-256 `89d15eeda9575fb38ddcfc491b122e370fe76dd75a9cc49a31a1abc4110983ee`. Electrical document **SLVS841F, revised August 2016**; current appended ordering addendum 21-Aug-2026, package material pages 22-Oct-2026. Drawing **DBV0006A, 4214840/G, 08/2024**.

Actual rendered pages opened/inspected: p1 typical application; p5 top-view pin/functions; p7 electrical columns/conditions; p18 two-level application; p21 retry example; p22 USB application; p25 DBV layout; pp27–29 ordering and qualification notes; pp34–36 outline/land/mask/stencil. These are `ti-pN.png`, not prospective CAD renders. Full extracted PDF text is retained in `source_text.txt`; it does not substitute for those visual inspections. No symbol or placed-board render exists in this read-only stage.

Order p27 explicitly lists TPS2553DBVR-1 active/production, DBV SOT-23 six leads, 3000 large T&R, marking CHZ, −40..125°C. `-1` selects latch-off; TPS2553 EN is active high. DRV WSON has different pin numbering and EP; no DBV EP exists despite generic application drawings showing a PowerPad.

## Fresh library findings

`library_queries.json` contains current configured/project symbol inventory, zero-hit `tps2553` symbol search, four-hit `SOT-23-6` footprint search and detailed stock/hand-solder readbacks. No configured `KiCadLib` nickname exists. Its absence is distinct from searching that unavailable library. Stock standard and hand-solder lands differ from TI's 1.10 × 0.60 mm, X=±1.30, R0.05 example. Standard stock body-zone courtyard has only 0.175 mm to maximum 1.75 mm body, below 0.25 mm; hand-solder has larger lands. Proposal uses new project-owned TI lands; no vendor library edits.

Pin contract: 1 IN power_in; 2 GND power_in; 3 EN input; 4 FAULT open_collector; 5 ILIM **output**; 6 OUT power_out. ILIM corrects the old written passive hypothesis: TI p5 marks O and §9.5.1 describes sourced programming current. No type weakening proposed. Top view is pin1 upper left, counterclockwise.

Mask p35 preferred NSMD specifies **0.07 mm MAX around**, while the unselected solder-mask-defined alternative says 0.07 MIN. Proposed +0.05 mm nominal blank mask apertures must be checked against inherited base pad margins, with ≤0.07 mm effective maximum; no native margin API is assumed. Proposed raw 12 objects comprise six numbered Cu/paste/base-mask pads and six blank mask-only shapes, no duplicates or drills. Stencil p36 equals copper geometry; manufacturing/stencil acceptance remains open.

## Electrical observations, separate from package proposal

Actual p7 columns confirm DBV on-resistance 95 mΩ max at25°C /135 mΩ max over −40..125°C; RILIM=210k gives110/130/150mA min/typ/max before resistor error. Recommended IN range is2.5..6.5V, ≥100nF local input bypass, EN high≥1.1V/low≤0.66V. Full-temperature continuous-current ceiling is1.2A;1.5A only through105°C junction.

Short response **2µs is TYP at VIN5V**, with no guaranteed max/3.3V response. Turn-on/turn-off delay3ms is MAX for CL1µF/RL100Ω. Reverse comparator95..190mV and MOSFET turnoff3..7ms apply to stated5V timing test; initial reverse current can flow. Overcurrent deglitch5..10ms; reverse FAULT deglitch2..6ms. Reverse leakage1µA max row is **25°C only** (OUT6.5/IN0); it is not a hot partial-power guarantee. FAULT VOL180mV max is at1mA; FAULT leakage1µA max. Thermal trip values155/135°C and10°C hysteresis are TYP table values, despite inconsistent minimum wording in prose; do not promote prose into a thermal guarantee. Input current at6.5V/no load is120µA max at210k and140µA max at20k. No-load figures do not bound arbitrary branch startup or fault current.

Latch-off after sustained overcurrent/reverse needs EN toggle or power cycle. ILIM external drive is forbidden; resistor range15..232k is recommended. USB120µF/example retry circuitry are application examples, not selected CAN/BMS topology. Root owns coupled startup/source-current/effective-capacitance and shared healthy-rail analysis. No fast-short survival, reverse fault isolation, PCB fit, production or flight acceptance is claimed.

## Reproducibility and preserved boundary

Run `python3 verify_candidate.py` here. It checks the full PDF hash/page count, source figure hashes, search results, six-lead proposed table/raw-mask geometry and **every tracked protected native file** against `d8ad529`, plus frozen tracked old branch/UCC/LT3014/UART/BMS checkpoint artifacts. Raw stock pad lengths are checked before unique maps. `baseline.json` lists the exact frozen paths/hashes; ignored/untracked volatile/progress artifacts are not byte-frozen claims. `verified.json` reports counts. This is a read-only source/proposal check, not native symbol/pad acceptance. New S08 construction approval and actual disposable acceptance remain required.
