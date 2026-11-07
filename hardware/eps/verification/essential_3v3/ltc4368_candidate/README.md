# LTC4368 library and gate-drive development checkpoint

2026-10-24. The operator approved [exact LTC4368 construction rules](../../../design/rev_b_ltc4368_library_rules.md). A project-owned symbol and MS10 footprint now exist, with fresh disposable placement/readback and actual rendered inspection. **Construction/geometry checks pass; manufacturer-page pixel inspection and circuit acceptance remain open.** No main EPS circuit or PCB was changed. The integrated root remains318 parts/175 nets/866 endpoints.

## Part and native verification

`Ember_Charger_BMS_Review:LTC4368IMS_1_REVIEW` preserves exact MS10 physical mapping1VIN,2UV,3OV,4RETRY,5GND,6SHDN,7FAULT,8VOUT,9SENSE,10GATE. Its five earlier library symbol subtrees are byte-exact. The old eight-pin LTC4367 pin map is not reused. All ten physical pins and their electrical types are checked separately from pad numbering. The symbol's first composition had a lower-pin/field collision; the enlarged functional arrangement was rebuilt through Konnect, the temporary duplicate definition removed through Konnect, and the final library checked for exactly one new symbol. The actual final page/detail is readable and retains the approved green CUSTOM—REVIEW REQUIRED callout. No symbol-body color support is claimed.

`ADI_MS10_05_08_1661_REVIEW` follows the numerical ADI MS10 RevF example:0.889×0.305mm lands atX±2.1055,0.50mm pitch, five per side,5.10mm outer span/3.322mm inner gap. Final construction has ten numbered Cu/Paste pads and ten blank-number Mask-only apertures,20 raw objects total. The final raw board/library objects, ten unique electrical numbers, geometry, layer sets, lack of holes/EP and exported mask dimensions are checked. The5.70×4.00mm courtyard includes the stated flash envelope and clearances. No3D model or thermal feature is invented.

The first `disposable/ltc4368_check` fixture is retained as a **diagnostic**: its numbered pads included F.Mask, and the blank board's0.05mm mask margin enlarged the openings beyond the approved0.04mm. It is not the accepted aperture source. The final fixture is `disposable/final/ltc4368_final`: numbered pads deliberately omit F.Mask; ten dedicated0.969×0.385mm mask rectangles produce the exact0.04mm expansion and0.115mm web even with that same inherited board setting. This supported layer strategy is an implementation clarification in the construction rules. Both raw geometry and the actual final SVG mask polygons corroborate the correction.

`verify.py` compares all4355 frozen prior files outside explicitly owned library/ledger/candidate-doc scope, all five old symbol subtrees, final library/saved pad maps and raw fixture netlist. All20 final saved pad objects remain separate before dictionaries. Native board-size/geometry inspection is read-only where get_component_pads omits sizes/mask settings. Portable fixture registrations use `${KIPRJMOD}`. Instance MFG/Manufacturer/Package/Footprint fields are set/read back; unsupported library custom defaults remain explicit. A fresh main-root CLI export has byte-identical component/net blocks to the318-part SWD checkpoint.

Fresh final fixture ERC is **17 errors/0 warnings**: ten intentionally unwired pins, five undriven signal inputs and two undriven power inputs. No fake NCs or source flags were added. That honest fixture report is separate from main-root ERC and from circuit functionality.

Root actually opened final full-page/detail schematic and copper, paste, copper+mask, silk/courtyard and numbered fabrication detail. The native fabrication Value field overflows the footprint/courtyard; pin numbers and key are visible. It remains a presentation limitation, not a clean fabrication drawing claim. Original diagnostic images are historical; final_ images and queries are the current construction source.

## Source boundary

ADI LTC4368 RevC web text supplies the exact MS10 order/map, electrical characteristics and p19 package dimensions. Direct ADI and Mouser PDF downloads failed (HTTP2 stream errors/HTTP1 timeout). Web screenshot calls returned references without available pixels; the temporary browser PDF remained blank. Consequently **no manufacturer reference-page image inspection is claimed**, and full package acceptance remains open. Source review and failed retrieval evidence are recorded in source_review.json. Do not integrate from a statement that every source gate passed.

Unlike LTC4365's5V OV-pin limit, LTC4368 permits20V on OV. The earlier58.8k/10k divider's5.11V at the imposed35V source therefore does not violate this part's corresponding rating. That comparison does not establish transient protection. The−1 variant has approximately symmetrical forward/reverse trip intent, not the−2's much smaller reverse threshold.

## Actual gate-bias simulations

Eight completed LTspice26.0.2/27°C runs compare the unmodified installed LTC4365 and LTC4368-1 macros at forced VIN=VOUT3.2328/3.3244V,2.2nF gate load and0/1µA DC gate loading. Source/symbol/model hashes, portable decks, normalized completion logs and raw hashes are retained. Some runs use Gmin stepping; completion is not process-corner coverage. Models and large raw files remain outside Git.

| Macro | Rail | No DC gate load |1µA gate load |
|---|---:|---:|---:|
|LTC4365|3.2328V|2.17036V|1.88940V|
|LTC4365|3.3244V|2.23119V|1.95037V|
|LTC4368-1|3.2328V|6.80160V|6.41163V|
|LTC4368-1|3.3244V|7.01093V|6.62097V|

Values are modeled late GATE−VOUT, not guaranteed hardware minima. This rejects relying on a4.5V MOSFET Rds(on) specification with the former LTC4365 candidate under these modeled conditions. LTC4368 merits continued development evaluation; no interpolation of typical curves is promoted into a supply/gate-current guarantee. A forced VOUT is a bias test, not actual startup, inrush or fault behavior.

`connected_screen.py` additionally tests an unmodified local TI CSD18543Q3A PSpice model with the actual LTC4368 macro. The locally available TI archive/header is identified by hashes; no encrypted model is altered or decrypted. It uses a separate10µH guard,15mΩ shunt,100nF/22k gate-slew network,96µF raw/192µF protected imposed banks and0.2→2A load. It does not select those parts or qualify capacitance, source impedance or loop interaction. The first two nominal experiments completed, but **the proposed connected circuit fails the 3 V startup-plus-load-step screening floor**. The 80–120 ms window uses every original raw sample, not decimated plotting data.

| Assumed source resistance | Late-window output minimum, 110–120 ms | Output minimum after 80 ms step | Late-window gate−source minimum | Peak absolute shunt current |
|---|---:|---:|---:|---:|
|50 mΩ|3.00641 V|2.56334 V|4.50967 V|2.78325 A|
|1 mΩ|3.10537 V|2.60192 V|4.58709 V|2.91176 A|

Lowering the imposed source resistance improves the late-window voltage but does not remove the transient deficit. The source impedance is an experimental assumption, not measured LMR51635 output behavior. Even the lower-resistance case has only about 87 mV of nominal late-window margin above the MOSFET's 4.5 V resistance-test reference; no guaranteed hot/cold drive envelope follows. This topology and component set remain **unselected**. The controller library remains available for further evaluation. Gate drive was still increasing at the 80 ms step, so the first pair cannot establish a fully settled load response.

A third completed run delays the step to 250 ms and extends the simulation to 400 ms, with the same1 mΩ source assumption. Its pre-step output is3.221032–3.221035 V and gate−source is 6.44794–6.46396 V (exact ranges in JSON). The later step still reaches **2.79881 V**, at250.073 ms, with3.11828 A peak absolute shunt current; the390–400 ms output minimum is3.11474 V and gate−source minimum6.29673 V. This separates the early gate-ramp issue from a persistent load-step deficit. These are typical model experiments, not a guaranteed final steady state or a regulator-loop model. `connected_late_step.png` shows the original-sample trace around the later step; `connected_late_plot.csv` is interpolated for plotting.

`connected_results.json` binds the exact unmodified model/archive and raw hashes, portable decks and normalized completion logs. `connected_load_step.png` and `connected_plot.csv` show both experiments; the CSV uses linear interpolation for plotting only. No35V fault, short, hot SOA, source magnetic or all-path backfeed acceptance follows.

## Reproduction and next design gate

Use Python with NumPy. `gate_screen.py --output /absolute/new-directory` runs the eight gate fixtures; installed unmodified model hashes must match. `connected_screen.py --output /absolute/new-directory --ti-model-archive /absolute/archive.zip --source-r 0.05` runs the early nominal connected experiment; add `--source-r 0.001 --load-step 0.25 --stop 0.4` for the later-step case (supply each option once). The TI file is extracted unchanged outside Git. `verify.py` checks the saved native/geometry checkpoint without rerunning a simulator. Runtime history/caches/locks/PRL are outside portable evidence.

Before main integration: inspect actual manufacturer pin/land pages, close the MOSFET gate/drive envelope, select complete fault-rated raw/protected capacitor banks and stable feedback path, choose current/reset thresholds, verify source-limited and saturated-inductor faults with actual turn-off clamp and MOSFET SOA, then check weak-source/startup/prebias and backfeed. C3225X7R1H226M250AC is a concrete TDK22µF/50V/±20%/X7R/1210 raw-bank candidate; its current manufacturer record confirms production status and2.50±0.30mm thickness, but effective capacitance/cold/aging and land compatibility remain unverified. No capacitor has been changed in the native EPS.

The final disposable schematic retains one Konnect-generated whitespace-only line (line335); generated SVGs likewise retain exporter formatting. These artifacts are kept byte-exact. Authored Markdown/Python/JSON/CSV/decks are checked separately for trailing whitespace; no native text repair is applied.
