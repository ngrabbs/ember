# Comms RF review and PCB cleanup — 2026-09-09

[Verification index](README.md) · [Current work](../TODO.md)

> Dated checkpoint record. Intermediate counts and commit-status statements below
> apply to that pass; use the index and current work list for the latest consolidated status.

Placement checkpoint: **6eaf5d6**. The subsequent changes described here are saved, uncommitted and not pushed.

## Status of the five requested tasks

1. **Git checkpoint — complete.** Committed the compact TX/RX placement and its existing validation before this pass.
2. **Filter/matching review — completed as an engineering screen.** Verified four identical seven-part BPF topologies from exported component/pad connectivity; ran ideal and trace-aware calculations. Found and improved the TX output filter's long internal connection by moving C94. RF qualification is still incomplete.
3. **L16 review — completed; qualification remains open.** Retain the exact installed Coilcraft part for prototype testing. Its published data supports further testing at 435 MHz, but does not satisfy the old >1.5 GHz SRF target or establish assembled stability. No speculative substitution or value change.
4. **Ground-return review — completed for the defined sampled scope.** Checked 20 RF nets and ground-pad/via proximity at U8, U9, U10, U11 and J9. Moved three non-RF vias away from the TX/RX return corridors. The J9 signal-pin launch requires separate impedance validation.
5. **Warning triage and fixes — complete.** 120 active warnings reduced to one intentional header-outline overlap. Final native PCB DRC and exported-netlist parity checks pass as detailed below.

This is not a fabrication release or a measured RF-performance approval.

## Filter and matching findings

All four filters use series 3.9 pF input/output capacitors, two shunt 10 nH || 9.1 pF resonators, and a series 1.6 pF inter-resonator capacitor:

| Filter | Components, in circuit order |
|---|---|
| RX input | C55, L12/C56, C60, L13/C64, C67 |
| TX preselector | C93, L23/C96, C98, L24/C100, C101 |
| TX output | C84, L19/C87, C89, L21/C92, C94 |
| RX LO | C86, L20/C90, C91, L22/C95, C97 |

With ideal parts and 50 Ω terminations, the calculated relative −3 dB passband is approximately 396.5–472.1 MHz. Calculated insertion loss is 0.005 dB at 435 MHz and 0.014 dB at 437 MHz. These near-zero numbers describe a lossless model, not realizable performance. Ideal rejection is approximately 22.8 dB at 870 MHz and 25.6 dB at 1305 MHz; this does not prove complete transmitter harmonic compliance.

An illustrative fixed series-resistance model corresponding to inductor Q=40 or 60 at 435 MHz predicts roughly 1.84 or 1.23 dB filter loss at that frequency. Those Q values are sensitivity cases, not measured properties of the installed inductors. This loss ahead of the LNA affects receiver noise performance. Adding 0.3 pF to both shunt capacitors or increasing both inductors by 5% also changes the response; actual tolerances and parasitics must be included before value tuning.

The BOM identifies Coilcraft 0402HP-10NXGRW via LCSC C40976557. Capacitor ordering codes are C1566 (3.9 pF), C526972 (9.1 pF), and C161311 (1.6 pF), with C0G/NP0 descriptions in the exported design. The distributor mapping identifies the orderable inductor; the manufacturer must supply its RF characteristics. Its Q at 900 MHz must not be silently reused at 435 MHz.

### Trace-aware comparison

We modeled each internal routed segment as a lossless 50 Ω line, using assumed effective permittivity 3.3. Trace endpoints form a nodal network, including tee branches; a source/load is placed at the outside terminals of each filter's series capacitors. This is a screening model, not a full electromagnetic extraction. It omits pad/via capacitance, shunt ground inductance, component loss/SRF, coupling, bias networks, active-device impedances, and leads outside the filter. Nearby track endpoints inside a pad are collapsed to that terminal.

| Filter | Internal copper, before → after | Calculated S21 at 437 MHz, before → after | Calculated input return loss at 437 MHz, after |
|---|---:|---:|---:|
| RX input | 6.48 → 6.48 mm | −0.47 → −0.47 dB | 9.93 dB |
| TX preselector | 8.53 → 8.53 mm | −0.70 → −0.70 dB | 8.30 dB |
| TX output | 19.36 → 9.45 mm | −2.79 → −0.81 dB | 7.70 dB |
| RX LO | 6.58 → 6.58 mm | −0.48 → −0.48 dB | 9.84 dB |

At the intended RX frequency of 435 MHz, the RX input model gives S21 ≈ −0.33 dB and input return loss ≈11.35 dB. There is still limited matching margin, especially in the TX filters. Do not translate these screening values directly into a link budget.

**Applied C94 correction:** moved C94 from (132.6,145.0) to (130.8,138.35), oriented vertically, immediately after the output filter resonators. The long run to U11 is now after the final coupling capacitor. Rerouted the two affected nets with 0.358 mm traces and extended the top-pour setbacks. This preserves all circuit values and connections while reducing the high-impedance internal filter wiring.

ADL5602 is intended for a 50 Ω environment; its 400/450 MHz datasheet points support using 50 Ω as a first approximation. The adjacent BPF coupling capacitors are part of the filter and must not simply be replaced by the amplifier evaluation board's 100 nF blocking capacitors. The actual L15=220 nH and C71=100 nF/C76=10 µF bias network differs from the datasheet's wideband 470 nH and 68 pF/1.2 nF/1 µF example. Verify supply-node RF impedance and stability; no blind capacitor/choke substitution was applied. The tripler collectors are not established 50 Ω sources, so the TX-preselector and LO calculations are especially provisional.

## L16 decision

Keep **0805HP-221XJRC, 220 nH, 5%**, with the previously manufacturer-audited custom land pattern. The official table specifies typical SRF 930 MHz, typical Q=75 at 250 MHz, maximum DCR 0.426 Ω at the specified conditions, and 0.50 A reference current for a 15 °C rise. Ideal reactance at 435 MHz is about 601 Ω, roughly 12 times 50 Ω. At an illustrative 100 mA, the 25 °C DCR limit gives 42.6 mV drop and 4.26 mW dissipation. These calculations establish neither measured RF isolation nor worst-case temperature performance.

**Open acceptance gate:** measure or obtain a suitable model for impedance versus frequency under operating bias; check LNA gain, input/output match, stability and RF leakage onto +5 V. Resolve the old >1.5 GHz SRF target against those results. A typical SRF figure is not a guaranteed minimum. Keep prototype qualification markings and the exact MPN in place. No component substitution was needed in this pass.

## Grounding and geometry

Moved the +3V0 via from (132.78,143.0) to (132.45,142.45), and switch-control vias from (136.3298,141.8625) to (136.4,141.0) and from (138.39,140.2) to (138.0,139.1). Adjusted their attached routing. Their antipads no longer interrupt the sampled RF return corridors. No RF layer transitions or signal routing on In1.Cu were added.

Final sampling: **21,947 points**, longitudinal step no greater than 0.1 mm and 17 transverse positions spanning ±0.6312 mm (three times the planned 0.2104 mm L1–L2 dielectric thickness). **21,757 points have filled In1 ground; 190 are in the ANT launch clearance around J9's plated signal pin.** Every sampled point on the other reviewed RF nets is covered. All reviewed RF traces remain 0.358 mm wide. Sampling does not prove uninterrupted copper at every point or predict actual current distribution.

U8 retains its ground-tab copper and thermal stitching; U9 has short local ground-via connections and U11's ground via is about 0.81 mm from its ground-pad center. U10's custom ground structure and J9's four plated ground pads provide direct through-board ground connections, so their nearest separate-via distances are not by themselves a defect. The through-hole ANT launch is not a uniform microstrip and remains an RF measurement/EM-extraction item.

## Warning disposition

| Category | Before | After | Action |
|---|---:|---:|---|
| Silkscreen overlap | 51 | 1 | Repositioned 45 reference labels; remaining H3/H4 outline overlap is visible and intentional |
| Silkscreen over pads | 51 | 0 | Moved labels clear of exposed pads |
| Hole-to-hole spacing | 10 | 0 | Removed six redundant same-net vias; retained connectivity and existing spacing rule |
| Text height | 6 | 0 | Increased six board text items to 0.8 mm |
| Isolated copper | 2 | 0 | Removed the disconnected +5V_CON pour zone; no lost connections |

Also replaced the obsolete test-point legend with TP11 CLK0_OUT, TP12 BPSK_DATA, TP13 TRIPLER_OUT, TP14 TX_437, TP15 RX_IF and TP16 RX_BASEBAND. Rendered and inspected the resulting top silkscreen/mask/outline view. The H3/H4 courtyard exclusion from the earlier user-approved connector spacing remains; no new exclusions or relaxed rule thresholds were added.

## Final verification and limitations

- Main-project DRC: **0 errors, 1 warning, 0 unconnected items**. The one active warning is the header silkscreen overlap, not an electrical violation.
- Native exported schematic connectivity: **181 nets / 441 distinct ref.pin keys**, no mismatch with the saved PCB.
- Exactly one component moved in this pass: C94. All component values, pad-net assignments and fixed connector/header geometry preserved.
- Schematics were unchanged. Prior native GUI ERC remains 0 active errors and one naming warning, with the previously documented two exclusions and four ignored checks; it was not rerun for PCB-only changes. CLI schematic ERC remains unreliable for this hierarchy.
- No VNA, spectrum-analyzer, thermal or hardware stability tests were performed. No fabrication outputs or order were generated.

## Work still needed before RF acceptance

1. Incorporate actual inductor/capacitor models, pad/ground parasitics and device impedances; tune filter values only after that model is corroborated. The current simplified model still shows matching concerns, so RF acceptance remains **INCOMPLETE**.
2. Measure filter insertion/return loss, complete TX harmonics/spurs and power, and RX gain/noise/sensitivity. Verify actual LO drive at ADE-1+ under load.
3. Qualify L15/L16, supply bypassing and amplifier stability under operating bias and temperature; close the L16 SRF requirement explicitly.
4. Check the J9 launch and actual fabrication stackup/impedance contract. Verify U10 body-height/stack clearance and outstanding schematic annotation cleanup from the earlier review.

## Sources and reproducibility

- [Analog Devices ADL5602 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adl5602.pdf), basic connections and S-parameter table.
- [Analog Devices RF PCB layout guidance](https://www.analog.com/en/resources/technical-articles/pcbs-layout-guidelines-for-rf--mixedsignal.html), ground reference continuity.
- [Coilcraft 0805HP-221 specifications](https://www.coilcraft.com/en-us/products/rf/ceramic-core-chip-inductors/0805-%282012%29/0805hp/0805hp-221/), L16 ratings.
- [Coilcraft model limitations](https://www.coilcraft.com/en-us/models/spice/?partNumber=0805HP-221&seriesName=0805HP), de-embedded models exclude customer layout and use unbiased measurements.
- [Coilcraft 0402HP-10N](https://www.coilcraft.com/en-us/products/rf/ceramic-core-chip-inductors/0402-%281005%29/0402hp/0402hp-10n/) and [manufacturer model document](https://www.coilcraft.com/pdfs/spice_0402hp.pdf); model values were located but not incorporated in this screening run.
- [LCSC C40976557 ordering identity](https://www.lcsc.com/product-image/C40976557.html), used only to resolve the BOM code to 0402HP-10NXGRW.

`evidence/rf_review_validation.json` contains numerical results. `../design/analysis/rf_filter_screen.py` and its before/after exported inputs reproduce the trace-aware screen with Python and NumPy. `../design/analysis/rf_filter_ideal.py` reproduces the ideal and sensitivity calculations. CSV files are screening outputs, not measured S-parameters.
