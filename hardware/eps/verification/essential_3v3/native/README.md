# Essential 3V3 native development stage

2026-10-23. **Selected standalone development circuit, not complete EPS essential-power acceptance.** [Project](../../../studies/essential_3v3/essential_3v3.kicad_pro), [native PDF](essential_3v3.pdf), [page image](essential_3v3.png).

The single ANSI B sheet contains16 physical parts and six named nets. All CAD writes used Konnect0.11.1/KiCad10.0.0. No existing scratch, controller,5V,protection,library or PCB geometry was changed. The auto-created blank PCB and .kicad_prl are excluded from the schematic deliverable. The parent reviewer independently reran both verification scripts and inspected the full page plus all three detail images before the Git checkpoint.

## Circuit and selected parts

Input SYS_PWR_PERMITTED is after RBF/deployment permission and source OV isolation. EN is wired directly to VIN; no MCU is needed for startup. SYS_PWR_PERMITTED now uses a real upward power symbol whose Value is the exact interface name; its previous scratch local-label path prefix disappears, but its basename is unchanged. +3V3 and GND retain legacy names. CFF remains omitted. No input bulk was added because the upstream capacitor/source budget is not integrated.

| References | Exact MFG P/N | Selection |
|---|---|---|
| U1 | LMR51635XDDCR | 400kHz PFM/dither, DDC6 |
| L1 | XAL6060-562MEC | 5.6uH20%;15.9mohm max25C;9.9A typical30%-drop reference;7.5A20C-rise reference |
| C1,C2 | GRM32ER72A225KA35L | 2.2uF100V10%X7R1210 |
| C3,C4 | GRM188R72A104KA35D | 100nF100V10%X7R0603; C4 bootstrap |
| C5–C12 | GRM32ER71E226KE15L | Eight22uF25V10%X7R1210,176uF nominal |
| R1 | TNPW060331K6BEEA | 31.6k0.1%25ppm/K0603 |
| R2 | TNPW060310K2BEEA | 10.2k0.1%25ppm/K0603 |

TNPW uses **0.11W general P70**,125C permissible film, per Vishay28758Rev10-Apr-2026p2, not the advanced-mode0.21W rating. The output capacitors require **>=12uF effective each**, including3.6Vbias,-40..85C and aging, giving>=96uF total. That is a qualification requirement, not a manufacturer guaranteed combined minimum. The input pair similarly requires>=2.2uF aggregate effective through35V. Supplier bias curves/approvals, actual ripple heating and aging remain open.

Primary sources: [TI SLUSF64B RevB](https://www.ti.com/lit/ds/symlink/lmr51635.pdf), [Coilcraft XAL6060-562](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal60xx/xal6060-562/), [Murata22u product sheet](https://www.murata.com/en-global/api/pdfdownloadapi?cate=luCeramicCapacitorsSMD&partno=GRM32ER71E226KE15%23), [Murata100n](https://www.murata.com/products/productdetail?partno=GRM188R72A104KA35%23), [Vishay TNPW](https://www.vishay.com/docs/28758/tnpw_e3.pdf). The current Murata cached product sheet verifies22uF25V10%X7R1210 and L/K packaging; its print endpoint redirects/blocks direct download. No missing DC-bias guarantee was invented.

The prior approved custom U1 pin map and manufacturer land are reused:1FB,2EN,3VIN,4GND,5SW,6CB; six unique pads,no EP/drill. [Symbol](ic_symbol.json) and [footprint](ic_footprint.json) readbacks agree. L1 uses stock Inductor_SMD:L_Coilcraft_XAL6060-XXX: two1.43x5.5mm pads atX±2.02mm, matching Coilcraft's4.04mm-center land example. Pad1 is the SW terminal; physical winding-start stripe orientation remains an assembly instruction. Existing custom review-marker approval coverage remains unresolved; no new custom part was authored. Library default Footprint/Description remain blank; every placed instance has explicit metadata.

## Reproducible electrical screening

Run `python3 hardware/eps/verification/essential_3v3/analysis/screening.py`. [Calculation](../analysis/screening.py), [48-corner results](../analysis/screening.json).

| Screening result | Value |
|---|---|
| Nominal divider output | 3.27843V |
| Reference and initial resistor tolerance | 3.24074–3.31623V |
| Including independent25ppm/K resistor extremes over65K | 3.23280–3.32439V |
| Worst sensitivity ripple / peak at2A | 2.91252App /3.45626A |
| Minimum peak-limit headroom | 0.74374A against4.2A minimum |
| Maximum RMS current | 2.16954A |
| Capacitive+ESR ripple estimate | 40.64mVpp with96uF/10mohm assumptions |

Inductance3.136uH is5.6uH x0.8tolerance x0.7 magnetic/hot sensitivity; it is not guaranteed hot L. Frequency329.4–477.4kHz includes switching tolerance and dither. Coilcraft9.9A is typical25C at30%L drop; it does not qualify hot operation at the IC's6A maximum peak threshold. Actual current limiting, delay overshoot and magnetic loss remain unverified.

**The96uF floor is not adequate proof for every load mode.** The TI eight-cycle triangular charge estimate for0.2→2A and96uF plus10mohm predicts0.2457V droop, placing the static-low estimate at2.9871V. No CAN3.0V minimum or tight3V3 transient acceptance follows. Actual MCU/IHU/CAN mode currents, controlled IHU ramp and loop settling must set the load-step budget. The regulator's internally compensated loop has not been characterized for this complete bank/PFM range. The TI table gives a starting effective capacitance, not an accepted arbitrary Cmax or measured phase margin.

Initial tolerance/temperature yields222.64uF maximum from the176uF nominal bank; life/aging recovery is not closed. A **250uF startup sensitivity allocation** is an assumption, not a published physical maximum. Ramps2–5ms add0.416–0.166A charging current at the high output setpoint. The actual soft-start is only typically specified; downstream capacitance is absent.

Partial IC-loss sensitivity peaks at0.927W using doubled room-temperature typical Rds(on) and assumed30ns combined switching edges. At85C ambient,48.5K/W EVM thermal resistance gives~130C junction, while105.2K/W JEDEC gives~182.5C. Neither establishes the actual board's thermal performance; core/drive losses and parameter maxima remain open. Layout must demonstrate its thermal path and current rating.

## Startup, weak source and faults

The selected part's operating minimum is4.3V; internal rising UVLO is4.25V maximum, falling3.8V typical, with0.2V typical hysteresis. Thus5V nominal and4.5V sensitivity exceed the stated startup limits, conditional on voltage at the device and losses. No independent UV supervisor or weak-solar anti-chatter scheme is selected. At2A output and assumed90%efficiency, input power is7.285W. A5V open-circuit source needs approximately1.457A before droop; static source resistance must be<=0.413ohm to retain4.3V. At4.5V the corresponding value is0.118ohm. These are load-line calculations, not a PV/startup model. Insufficient harvest can cause repeated collapse/restart despite autonomous enable.

**Autonomous3V3 output overvoltage containment is absent.** A failed-short high-side switch can expose MCU/CAN and the25V capacitor bank to~35V. The upstream solar protector cannot contain this regulator failure. The native sheet states this explicitly. This prevents complete EPS essential-power acceptance.

## Native electrical and actual visual evidence

[Verifier](verify_native.py) asserts all six exact endpoint sets,16 component metadata sets,6ICpins/6pads, inductor lands, six persisted class memberships, on-grid wires and branch geometry. [Verified result](verified.json), [CLI XML](essential_3v3.xml), [endpoint CSV](endpoint_sets.csv), [field readback](fields_readback.json), [BOM](bom.csv).

Fresh [CLI ERC](erc.json): **0errors,0warnings**. Three legitimate PWR_FLAGs model the external input/return and actual buck output after passive L1. They do not model upstream fault protection. Independent geometry finds51 orthogonal on-grid wires,zero four-way intersections and no component/power anchors at branching junctions. Class numerical values are default placeholders, not accepted fabrication constraints.

The [full page](essential_3v3.png), [input/switching detail](input_switching_detail.png), [output detail](output_detail.png), and [feedback detail](feedback_detail.png) were all opened and inspected. Actual support topology,power/ground stubs,feedback loop,bootstrap path and eight-cap bank are readable. Single-sheet printed pagination is1/1.

S03 native four-way severity remains ignored in the fresh report; no exposed setter can persist Error. S11 rating fields are saved but custom field visibility/font/position setters are unavailable, so required Arial rendered blocks remain unaccepted. S08 coverage of reused custom U1 is open as above. Clean ERC is not physical,current,thermal,transient,qualification or complete policy acceptance.

## Future integration

Standalone studies reuse physical references and cannot simply be linked together. Preserve their source histories. Rebuild integrated functional sheets through Konnect under an agreed reference-range allocation, with an explicit old→new crosswalk and endpoint comparisons. add_hierarchical_sheet alone links/mutates the existing child instance paths; it is not a safe import/copy strategy. No integrated root or PCB synchronization was attempted.
