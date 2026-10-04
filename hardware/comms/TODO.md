# Comms open work

**October 4 PR snapshot:** saved-board DRC still passes with zero errors/unconnected. Power/RX schematic cleanup and PCB saves postdate the October 3 quote; repeat native ERC/parity and refresh affected manufacturing outputs before ordering. [PR validation record](verification/pr_review_2026-10-04.md).

[Comms home](README.md) · [Design overview](design/overview.md)

**Updated October 3, 2026, evening:** layer migration and protected-input routing are complete. Current candidate is `releases/review_20261003_1952`; vendor preview/CAM and bench qualification remain. Earlier
Gerber ZIPs and the JLCPCB preview are historical candidates, not the release for
this new routing plan. Preserve the latest logos and schematic cleanup.

## Active layout migration — analog top, two inner ground planes

Target uses **physical layer numbers**, not the existing custom KiCad names:

| Physical layer | KiCad layer | Current display name | Target |
|---|---|---|---|
| 1 | F.Cu | Top Layer | Analog, RF and clock routes; local component connections; GND fill |
| 2 | In1.Cu | Layer 1 | Continuous GND reference plane |
| 3 | In2.Cu | Layer 2 | Continuous GND reference plane; remove power pours and power tracks |
| 4 | B.Cu | Bottom Layer | Power distribution and digital/CAN routing; GND fill where feasible |

Keep short top-side power-to-bypass/IC connections. Route distribution on the
bottom and use local vias; do not add long bypass loops just to enforce a layer
label. Preserve the accepted dielectric construction pending renewed impedance
review. Inner planes are GND-only; do not cut analog reference paths with routes.
H1/H2, mounting holes, board outline and user artwork remain fixed.

- [x] Save the live PCB and archive the current source/local libraries before edits.
  Checkpoint: `~/Desktop/transceiver_before_layer_migration_20261003_1505.zip`.
- [x] Inventory all zones, power feeds, vias, and bottom-layer analog routes.
  [Baseline evidence](verification/layer_migration_20261003/before-inventory.json).
  Physical layer 3 has +3V3/+5V pours and 56 traces: +3V3 86.91 mm,
  +5V 167.91 mm, +3V0 12.28 mm. Existing layer 2 is already GND.
- [x] Restore C69 to RX_AMP_IN, synchronize native F8 net changes, and rotate
  R39 180 degrees at its original position to align its swapped pad numbers.
  Saved DRC returns to zero errors/unconnected; one existing H1/H2 silk warning.
- [x] Refresh editor-native ERC/full netlist parity after the completed migration.
  Original review scope: review C69's move from
  RX_AMP_IN to VREF_RX, R39 pin reversal, and renamed/removed labels. Preserve
  intentional cleanup; use native editor netlist/F8, never the incomplete CLI
  netlist for synchronization. Final native parity: 213 nets, 572 logical pad entries, zero mismatch.
- [x] Normalize CAN pair stems to CAN_A_P/N and CAN_B_P/N, retaining H=P/L=N.
  Confirm header pin mapping and selectable 120-ohm terminations.
- [ ] Size bottom power distribution for rail current, transient demand and drop;
  record 1 oz outer-copper assumptions, branch lengths, via and neck-down limits.
- [x] Route replacement +3V3 feeds on bottom with local top component escapes.
  Connect the supply beyond the CAN/+5V crossings using a new via at
  (128.4, 102.2), then route the receiver-side supply at 0.5 mm width.
  Remove all 22 old inner +3V3 segments, the inner +3V3 pour and five obsolete
  plane-feed vias. Saved DRC without the 3V3 plane: zero errors/unconnected,
  only the existing H1/H2 silk warning. All inner-layer tracks are now gone.
  The final +5V join and inner GND conversion are now complete below.
- [x] Move both +3V0 distribution segments (12.28 mm, 0.25 mm width) from
  In2.Cu to B.Cu; retain existing via endpoints and local bypass connections.
  Refilled/saved DRC: zero errors/unconnected, one existing H1/H2 silk warning.
- [x] Move CAN and receiver-side +5V distribution to bottom; remove 24 superseded
  inner-layer segments after separate candidate and final DRC checks passed.
  Bottom CAN feed: 0.5 mm width, 77.31 mm total; receiver feed: 0.4 mm, 42.66 mm.
  Existing bypass/inductor connections and supply vias retained. Power pours
  remain active pending complete feed replacement.
- [x] Move the remaining TX-side +5V tree to bottom at 0.5 mm width; connect
  one branch to the existing receiver-side feed. Remove all eight superseded
  inner segments after candidate/final DRC passed. All +5V traces are now outer.
- [x] Move the 2.54 mm, 0.4 mm VBAT header link from In2.Cu to bottom.
  Candidate/final DRC: zero errors/unconnected. Only +3V3 tracks remain on In2.Cu.
- [x] Complete +5V outer distribution and remove its inner pour. Move GPIO0,
  GPIO1, GPIO13, GPIO22 and RUN_RESET to top to open the bottom corridor.
  Final feed: 50.21 mm, 0.5 mm bottom; six obsolete plane-feed vias removed.
  Retain local top bypass copper and chokes. Saved DRC proves continuity
  without either inner power pour; complete rail-drop/thermal review still open.
- [x] Remove superseded physical-layer-3 power tracks/pours and add/refill GND.
  Both inner layers verified GND-only, zero traces. In2.Cu uses the existing
  In1.Cu outline and 0.5 mm clearance / 0.25 mm minimum fill width.
  Final saved DRC: zero errors/unconnected, one existing H1/H2 silk warning.
  In2.Cu has a main fill and a small grounded header pocket; neither is floating.
- [x] Move RX_BASEBAND and VREF_RX bottom branches onto top, retaining all
  branch connections. Remove eight old bottom tracks and five obsolete vias.
  Baseband replacement 10.38 mm (was 10.50); VREF replacement 26.21 mm total
  tree (was 20.59). Saved DRC: zero errors/unconnected, existing H1/H2 silk warning.
- [x] Move ADC_VREF to top: 26.18 mm at 0.254 mm width, down from 34.65 mm.
  Candidate and final saved DRC: zero errors/unconnected, existing silk warning.
- [x] Complete RX_IF top routing: C99 changed to stocked C1711 100 nF 0805
  to bridge over the mixer RF trace. All new tracks retain 0.358 mm width;
  the two obsolete IF signal vias are removed. Saved/refilled DRC: zero
  errors/unconnected, existing H1/H2 silk warning only.
- [x] Audit all bottom net names: no unnamed analog, RF, clock or reference nets remain below top. RF return screening and all-layer plots reviewed; bench RF qualification remains.
- [x] Replace D8 with LM73100 protected input, route local capacitors and repeat native ERC/DRC. Custom footprint accepted after editor recovery. Static margin screened; dynamic EPS/load voltage and heating remain bench qualification.
- [x] Establish clock baseline: CLK0_OUT 9.76 mm and CLK1_OUT 8.09 mm are already
  top-only with zero signal vias; source-side Y2 output nets are top-only too.
- [ ] Preserve top clock/RF paths during power/CAN rerouting; check 50-ohm segments,
  pad neck-downs and reference continuity with the actual selected stackup.
- [x] Regularize CAN A bottom-trunk bends to 0.65 mm center spacing
  (0.45 mm edge gap), retaining 0.20 mm width. Saved/refilled DRC: zero errors
  and unconnected items; existing H1/H2 silk warning only. This is geometry
  cleanup, not differential-impedance acceptance.
- [x] Measure CAN controller-to-header paths separately from termination branches.
  A: H 83.03 mm / L 77.65 mm, two transitions each. B: H 125.89 mm /
  L 122.79 mm, four versus two transitions; source crossover review remains.
- [x] Review CAN endpoint paths and crossover reference. Accept the short CAN_B source crossover for this classical-CAN prototype: missing reference is confined to intended via antipads. Do not add meanders or matching vias. Bench termination/ringing/error-counter checks remain.
- [x] Refill all pours and re-evaluate GND stitching after the layer changes.
  Remove redundant signal/power vias only when connectivity is proved.
- [ ] Run saved-board DRC after each circuit block; final acceptance requires zero
  errors/unconnected, only reviewed fixed mechanical/silk exclusions, editor ERC,
  native full-netlist parity, visual review of every copper layer, power-drop and
  analog-return checks. Existing DRC alone does not validate the new architecture.
- [x] Regenerate Gerber/drill, corrected BOM/CPL and bare friend-review ZIP. Fresh JLC draft matches/selects all144 placements;15 prior rotation corrections reapplied. Quote: $322.24 before shipping/taxes. See `releases/review_20261003_1952/README.md`.
- [ ] Obtain vendor engineering approval of U15 RPW0010A package/pin1/paste, remaining LED placeholder orientations, J9 soldered precision holes/assembly process, and50ohm±10% stackup before ordering.

RTS feedback resolved: MCP25625 SSOP pins 23/6/7 are input-only with internal
pull-ups; active-low does not make the existing high ties an output short hazard.
No added resistors are required for that stated concern.

## Prototype fabrication target — October 3

- JLCPCB: **5 PCBs, 2 assembled**; headers and Pico hand soldered (user selection).
- Preserve the existing four-layer board. Final vendor stackup, copper, finish,
  thickness, impedance option and assembly service still need a recorded order contract.
- [x] Transfer the new CAN schematic to the PCB; remove U2/U3 and the extra
  R38/R39 footprints. Initially place both CAN circuits above the Pico.
- [x] Restore MH1–MH4 from the original Rev-A drill/copper data: 3.18 mm plated
  holes with 6.35 mm copper pads. Keep their exact stack coordinates. All four
  are locked, board-only, and excluded from BOM/position files.
- [x] Complete CAN bus/control routing and controller supply feeds. Fresh DRC
  has no missing connection involving a CAN net or U1/U4.
- [x] Finish remaining board connections and remove obsolete isolated supply copper.
  Saved, refilled DRC reports **zero unconnected items, zero clearance errors,
  and zero track-width errors**.
- [x] Resolve copper defects and document fixed-interface courtyard exceptions.
  Saved DRC after power-plane cleanup: **0 errors, 0 unconnected items, 1 warning**. Five individual
  courtyard exclusions preserve user-confirmed PC/104 hole/header coordinates.
  Remaining warning: fixed H1/H2 silkscreen-outline overlap.
  The power-via spacing warnings are now cleared. No global check was disabled.
  All clipped reference labels and mounting-hole library mismatches are cleared.
- [x] Verify full native netlist parity: all 209 native schematic nets and 551
  nodes agree with live PCB pad assignments. This checks assignments, not routed
  continuity. Use native export; the CLI export omits unnamed nets.
- [x] Recheck RF ground return corridors on the current PCB. Moved three non-ground
  vias away from TRIPLER_OUT, RX_IN and TX_OUT; 20,587 sampled points leave only
  the expected J9 antenna signal-pin opening. This geometry screen does not
  validate impedance; final vendor stackup and RF bench measurements remain open.
- [x] Add and route U14 hardware TX mute with C115 bypass, controlled by existing
  TX_ACTIVE and R35 pull-down. Native ERC has zero errors; saved DRC remains
  0 errors / 0 unconnected / 11 existing warnings. H1/H2 and holes are unchanged.
  [Implementation and evidence](verification/tx_startup_inhibit_review.md).
- [x] Use restored In2.Cu +3V3 plane to remove 193 mm of redundant surface power
  feeds; repair CLK0 width/clearance and power-via spacings.
  [Current validation](verification/evidence/power_plane_cleanup_2026-10-03.json).
- [ ] Finalize startup/TX inhibit firmware, power sequencing and debug access
  before release. Validate 145.667 MHz waveform, disabled RF leakage and
  reset/watchdog behavior during prototype bring-up.
- [x] Stitch new top ground to inner/bottom ground: 100 verified GND vias,
  including RF-region/perimeter ties; resolve pour priority and thermal errors.
- [x] Verify nominal RF width with the live JLCPCB calculator (14.12 mil);
  route CLK0 entirely on top and clear the TRIPLER_OUT return corridor.
- [x] Review J9 nominal launch/footprint and classify clock/IF exceptions.
- [x] Inspect exported inner planes/paste; verify closed outline and all 140 CPL
  positions/angles against saved geometry. [Fabrication notes](releases/review_20261003_1230/fabrication-notes.md).
- [ ] Confirm precision finished-hole tolerance for all five J9 holes (0.84 ±0.05 mm);
  standard JLCPCB hole tolerance is wider. Specific export coordinates are in the fabrication notes.
- [ ] Accept the proposed 50-ohm ±10% fabrication service and exact 7628 stackup
  in the vendor order. J9 clearance confirmed: top board, no board above, installed connector fits.
  [Detailed review](verification/ground_stitching_rf_review.md).
- [ ] Complete exact parts, mechanics and manufacturing checks below, then export
  a fresh Gerber/drill/BOM/CPL package. A local review candidate now exists at
  [review_20261003_1230](releases/review_20261003_1230/README.md); it is not released for ordering.

RF gain, sensitivity, filter tuning and spectrum measurements requiring the
assembled board belong to prototype bring-up. Before fabrication, close the
circuit/footprint decisions and ensure access for those measurements and rework.
[Current evidence and limits](verification/prototype_fabrication_progress.md).

## Dual CAN conversion — October 3

- [x] Wire U1/U4 MCP25625-E/SS: common SPI0 bus, separate chip selects,
  interrupts, standby and reset, independent 16 MHz clocks, 3.3 V logic and 5 V
  transceiver supplies. Preserve jumper-selectable 120 ohm termination.
- [x] Verify exported netlist: 15 CAN signal groups, all controller power pins,
  separate A/B clocks and bus nets, RF ADC/TX pins, and unaffected circuitry.
  Konnect reports no floating wire ends, unconnected pins, shorted nets or orphans
  on Digital Control after wiring checks.
- [x] Confirm saved U1/U4 SO pin 16 types are tri-state on shared MISO. Fresh
  native KiCad ERC reports zero errors and two library-mismatch warnings for
  these deliberately corrected symbols; four existing ignored tests remain.
  Corrected duplicate Digital Control power references and assigned the Y3/Y4
  SiT 7050 footprints. Netlist assertions and all four connection checks pass.
  Command-line ERC still reports 36 dangling-wire findings not reproduced in
  the native editor; do not delete functional wires solely on that discrepancy.
- [ ] Preserve the corrected MCP25625 symbols in a project library to resolve
  the two library-mismatch warnings; do not overwrite their tri-state SO pins
  with the stock library's output type.
- [x] Update PCB from schematic and place both controllers and support circuits.
- [x] Route changed CAN and Pico connections; current DRC has zero unconnected
  items and native pad-net parity passes. Functional CAN checks remain below.
- [ ] Port firmware to two MCP25625 instances and the pin map below. Old bench
  firmware is not pin-compatible. Use SPI0 as master, service both interrupt
  sources, and control A/B standby independently. Keep standby high until the
  associated controller is configured; drive low for normal transceiver operation.
- [ ] Verify simultaneous RF receive and CAN traffic, bus-off recovery, and A/B
  failover on hardware. Budget up to 70 mA from 5 V per active CAN transceiver
  (140 mA for both) in addition to the controller/clock 3.3 V loads.

| Function | Pico GPIO | Header connection |
|---|---:|---|
| CAN SPI MISO | 4 | J6.6 |
| CAN SPI SCK | 6 | J6.9 |
| CAN SPI MOSI | 7 | J6.10 |
| A / B chip select, active low | 14 / 15 | J6.19 / J6.20 |
| A / B interrupt, active low | 18 / 19 | J7.17 / J7.16 |
| A / B standby, active high | 2 / 3 | J6.4 / J6.5 |
| A / B reset, active low | 8 / 9 | J6.11 / J6.12 |

GP27 RX_BASEBAND, GP16 BPSK_DATA, GP20/21 I2C, GP10 TX_ACTIVE,
GP11 RX_ACTIVE and GP12 status indication remain assigned as before.

Live JLCPCB product pages checked October 3, 2026 (stock is not reserved):

| Use | Exact MPN | JLC part | Observed stock |
|---|---|---|---:|
| U1/U4, SSOP-28 | MCP25625-E/SS | C184944 | 60 |
| Y3/Y4, 16 MHz, 3.3 V, 7050 | SIT8008AI-82-33E-16.000000Y | C12710 | 40 |
| R40–R45, 10 kΩ, 0603, 1% | 0603WAF1002T5E | C25804 | 23,015,202 |
| C107–C114, 100 nF, 50 V, X7R, 0603 | CC0603KRX7R9BB104 | C14663 | 58,102,611 |

C8/C9 retain their existing 100 nF 0805 assignments. Each channel has separate
VDD, VIO and VDDA bypass capacitors, oscillator bypass, reset RC, and CS/STBY/reset
pull-ups. Place bypasses at their respective pins. SiT8008A is manufacturer NRND;
the stocked part is acceptable for this prototype, but revisit it for later builds.
The oscillators' 45–55% duty cycle specification meets the MCP25625 external-clock
requirement. Their OE pins are held high. Unused OSC2, CLKOUT and buffer-full
outputs are marked unconnected; all three active-low RTS inputs are held high.

Source documents: [MCP25625 DS20005282C](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/MCP25625-CAN-Controller-Data-Sheet-20005282C.pdf),
[SiT8008A datasheet](https://www.sitime.com/sites/default/files/mature-datasheets/SiT8008-datasheet.pdf).
SSOP and SiT physical pin maps were checked against manufacturer top views and
rendered footprint pad coordinates. C191253 is not the SSOP ordering code.

## Resolve before release

- [x] **Stock substitutions (October 3):** L12/L13/L19–L24 now Murata C90642;
  U12 now TLV73330PDBVR C882826; D12/D13 now top-view C125094.
  Pins/packages and RF screening checked; all 11 properties synchronized to PCB.
  [Acceptance and validation](verification/components/stock_substitutions_2026-10-03.md).
- [ ] **Mixer order check:** retain ADE-1+ C2942210 per user; six displayed,
  two nominal. Verify available quantity plus assembly allowance at order time.

- [x] **U9 sourcing decision:** retain the existing audited PSA4-5043+, C5240848.
  Live JLCPCB page on October 3 shows 1,942 stocked / 1,923 orderable, including
  SMT assembly. TQP3M9036 replacement is unnecessary while this stock remains.
  Recheck at order time; gain, stability and receiver headroom remain bench tests.
- [x] **L16:** retain 220 nH using stocked 0805HP-221XGRC / C40877572, same
  audited footprint, 2% tolerance. Explicit prototype SRF exception; bench
  isolation/stability verification remains open.
- [x] **D15:** apply PESD5V0F1BLD,315 / C478204 in the existing SOD882D footprint.
  Conditional low-power prototype envelope and pin audit recorded in
  [parts acceptance](verification/components/prototype_parts_2026-10-03.md).
- [x] **J9:** verify nominal hole pattern and lead reach using Molex drawing C5;
  identify exact JLCPCB part C588477 and live availability.
- [x] **J9:** physical clearance confirmed by user: installed MMCX fits; this
  is the top board with no board above and ample room. Stack uses 16 mm standoffs.
- [x] **J9:** save Molex 734151471 / C588477 ordering fields; live listing supports wave assembly. Confirm selected service at order time. RF launch return loss remains a prototype measurement.
  [Review and fabrication requirements](verification/j9_launch_and_fabrication_requirements.md)
- [x] **Embedded ordering properties:** all 147 purchasable placements have `LCSC Part #`
  in schematic and PCB; six bare test pads are `N/A`. [Audit](bom/evidence/lcsc_property_audit_2026-10-03.md).
- [ ] **Procurement:** ordering fields are complete and retained U9 stock verified;
  recheck every exact populated part against live JLCPCB stock for the actual build
  quantity plus allowance. Preserve J6/J7/J8 as DNP. [Sourcing](bom/README.md)

## Prototype bring-up — measurements after assembly

- [ ] Define measured acceptance budgets and record available instruments.
- [ ] Measure all four filters; compare existing 9.1 pF tuning with 8.2/7.5 pF
  candidates. Resolve exact capacitor RF models and full tolerance/loading effects
  before selecting new values. [Worksheet](bringup/rf_prototype_checklist.md)
- [ ] Measure TX power, spectrum, XOR drive quality, and pulse-shaping behavior;
  the ADL5602 compression figure is not a clean antenna-output specification.
- [ ] Verify U10 LO drive under actual loading, RX gain/sensitivity/blocking,
  T/R switching, transmitter leakage, and receiver exposure.
- [ ] Qualify L15/L16 bypass/isolation and amplifier stability over intended supply
  and temperature conditions; verify C103/C104 effective capacitance and regulator
  stability. [Capacitor selection record](bom/evidence/remaining_field_completion.md)

## Close the physical and verification record

- [ ] Confirm fabrication stackup and impedance in the selected service.
- [x] U10 overhead clearance: actual CD636 maximum height 4.11 mm; user-confirmed
  top-of-stack placement has no board above and ample space. Retain the known
  shorter CD542 3D-model limitation; it is not an enclosure-clearance model.
- [ ] Correct stale schematic annotations, including baseband filter Q/cutoff and
  any remaining VHF references. [Baseband/header record](verification/baseband_and_header_review.md)
- [x] Regenerate the native netlist and BOM after ordering-field changes. Rerun
  native ERC, DRC, and net parity after accepted replacements; preserve documented
  exclusions without treating them as RF or mechanical qualification. October 3
  fresh native ERC: 0 errors/2 intentional library warnings; DRC: 0 errors/0
  unconnected/1 fixed silk warning; 209-net parity has no mismatches.
- [ ] Generate a new, reviewed release bundle after the pre-fabrication gates close.
  Existing Rev-A manufacturing files are historical.

Component candidates, old stock counts, and screening results are evidence for
this work, not completed substitutions or guaranteed performance.

## JLCPCB preliminary preview — October 3

- [x] Upload authorized Gerber/BOM/CPL to signed-in draft; match all 140 placements.
- [x] Correct 15 supplier-model rotations in the portal; retain original KiCad files.
- [x] Select 7628 stackup, ENIG, precision holes and 50-ohm tolerance service.
- [ ] Add the prepared impedance worksheet to the final vendor archive while preserving placement corrections.
- [ ] Complete placeholder LED/D15 polarity acceptance, final placement checks and CAM/hole-process confirmation.
- [ ] Review final quote before payment: preliminary $319.98 excludes shipping/tax/discount changes.

[Draft findings and preserved corrections](releases/review_20261003_1230/jlc-preview-review.md). No order or payment made.

Evening BOM audit: R26/R31 corrected from erroneous C1152 (24k) to C11702 (1k 1%, 0402) in schematic and PCB; fresh assembly BOM reflects the correction. Final DRC remains zero errors/unconnected.
