# Single-antenna routing progress

## Initial RF routing — 2026-09-09

Routed J9–C102–U11 and the TX_OUT/RX_IN branches to C94/C55 on F.Cu at the existing project width of 0.358 mm. ANT and Net-(U11-RFC) are assigned to RF in the project. Source stackup remains JLC04161H-7628, with the 0.2104 mm outer prepreg confirmed against https://jlcpcb.com/impedance on 2026-09-09; width comes from the existing project calculator record, not a new field-solver result.

Moved D15 to (133.0,139.9) mm, 0 degrees, reducing its ANT branch length to about 1.25 mm. D15 GND pad 1 is at (132.6,139.9), ANT pad 2 at (133.4,139.9). Added 0.6/0.3 mm GND vias at (132,139.9), (134.8798,144.65) and (131.5,141.9), and routed C106 to U11 VDD and local ground. Supply from U12 and switch control remain unrouted.

A single F.Cu pour-only rule area buffers RF segments by at least 1.1 mm from trace edges. Pads, tracks and vias remain allowed, and inner ground zones are unaffected. This removes nearby pour; it does not prove 50-ohm behavior through component pads and connector transitions. Native filled-ground sampling at 0.1 mm along new RF centerlines found ground on L2 at 101 of 113 sample points; the 12 absent samples are all in J9's through-hole launch, from y=136.7676 to 137.8592. Full-width return-path/launch analysis and bench VNA remain open.

Saved board: 18 new segments and three vias; all 633 pre-existing track/via objects retain geometry and net names. Refilled DRC: 626 errors, 268 warnings, 152 unconnected items. No violations involving new copper or the placed RF parts. This is an intermediate routed switch island, not a fabrication release.

Tooling note: native saving during this pass overwrote the first file-based netclass assignment. Reapplied both assignments after the final PCB save and verified them on disk. The currently open editors may retain older netclass settings until the project is reloaded; all newly routed RF tracks have explicit 0.358 mm width. Recheck these two assignments before further native project saves.

## Local power and control routed

Added 25 segments and five vias for the local regulator, bypass capacitors, bleeder, 3.0 V distribution, control-buffer output/pull-down and input/pull-down. Two B.Cu segments distribute 3.0 V between explicit-net vias at (132.78,143) and (139.28,146.2). Native KiCad initially reassigned the isolated bridge/vias to GND; all four items were corrected, the supply vias marked free to preserve their explicit net, and their +3V0 assignments verified after zone refill. Rerouted the B.Cu bridge around two ground vias.

Final DRC: 626 errors, 268 warnings, 143 unconnected items; no violations involving this pass's copper. All 633 original copper objects and the prior 21 RF copper objects are unchanged. Incoming board +5V and Pico TX_ACTIVE remain disconnected, as do the chain sides of C94/C55. RX filter L12 remains unplaced; do not route to its temporary origin location. No fabrication readiness is implied. RF netclass assignments reapplied and verified after the final save due the documented editor cache issue.

## Incoming switch feeds routed

TX_ACTIVE now connects J6.14/Pico GP10 to R35/U13 through L3 (In2.Cu), ending at a new 0.6/0.3 mm via at (145.49,143). The regulator input now connects to the existing +5V via at (122.8846,117.2344), through L3 to a new via at (122.475,142.7), then C103/U12 on F.Cu. Control width 0.2 mm and supply width 0.3 mm. L2 ground is unchanged. The board-wide +5V network still has disconnected sections; this pass does not establish a working power tree.

All 16 new segments and two vias retain their expected nets after refill. Final DRC: 626 errors, 268 warnings, 141 unconnected items, with no violations involving these new items. Original 633 copper items and the first 21 RF copper items remain unchanged. Next filter placement: C56/L12 (RX input) and C89/C92 (TX output) are still at temporary origins; the chain sides of C55/C94 must wait for reviewed placement and obsolete copper cleanup.

## Schematic junction visibility correction

Added explicit junction dots at R35/TX_ACTIVE (40.64,116.84) and R36/SW_CTRL_3V0 (101.6,116.84). Existing wire endpoints already met; no intended net changes. Rechecked RF sheet: zero floating wires, unconnected required pins, shorts and orphan items. Render visually confirms both dots. U12 pin 4 and U13 pin 1 are stock-symbol hidden NC pins; enabled View → Show Hidden Pins in the editor for inspection. This display setting does not change library symbols or exported drawings.


## TX filter cleanup — 2026-09-09

Removed obsolete C19/C20/C21/L6 and 17 reviewed old filter trace segments through live Konnect. Placed C87/C89/C92; their routing remains incomplete. Saved native readback shows 141 footprints and 685 copper items, with every retained copper item unchanged and only the three intended remaining footprints moved. Refilled DRC: 587 errors, 266 warnings, 134 unconnected items. Render review found overlapping reference labels to tidy during filter routing. Remaining legacy footprints: 16. See `tx_filter_cleanup_validation.json`.


## TX output filter routing — 2026-09-09

Routed C84 pad 2 through the two shunt resonators and series C89 to C94 pad 1. Existing C94-to-U11 TX connection remains intact. L19/L21 rotated 180 degrees to align signal pads with C87/C92; four obsolete fanout vias and 15 fanout segments were replaced with four 0.6/0.3 mm ground vias and 0.7 mm pad-center-to-via-center connections. One +3V0 F.Cu crossing moved to B.Cu with a new via so RF remains on F.Cu. Added 16 RF segments at 0.358 mm, four ground segments at 0.3 mm, one power segment at 0.2 mm and five vias total. Six references repositioned at 0.8 mm height. Added a F.Cu pour-only keepout at least 1.1 mm from RF trace edges.

Native saved readback: 141 footprints, 691 copper items; exactly 20 reviewed removals and 26 additions, all 665 retained copper items unchanged, new nets correct. DRC: 579 errors, 252 warnings, 128 unconnected items; no violations involving new copper or adjusted reference fields. No unconnected reports remain on the two internal filter nets. L2 ground sampling every 0.1 mm or finer at center, trace edges and ±0.6312 mm: 1,085 samples, zero gaps. Sampling does not replace EM analysis or VNA validation. C84 pad 1/upstream amplifier remains disconnected and U8 identity still needs audit. Restored ANT/RFC RF assignments after native save and assigned both new filter nets; readback confirms RF width 0.358 mm.

Evidence: `tx_filter_routing_validation.json`. Prior local-power evidence is historical: its F.Cu segment `43f6beb3-97f8-4089-bcea-795526d2a6b5` was intentionally replaced by the B.Cu crossing in this pass.


## U8 output and bias routing

Completed and verified on 2026-09-09: see `u8_bias_routing.md` and `u8_bias_routing_validation.json`. Current board DRC is 569 errors, 249 warnings, 127 unconnected items. U8 input and thermal stitching are still open.

U8 ground stitching added and checked: four vias and two tab connections; see `u8_ground_validation.json`. Input filter/C101-to-U8 routing and thermal qualification remain open.


## TX input filter completed

C98 is on-board and C93-to-U8 input routing is connected and checked. See `input_filter_routing.md` and `input_filter_routing_validation.json`. Current DRC: 525 errors, 219 warnings, 118 unconnected items. Existing TP13/C93 overlap at the entrance remains; thermal/RF qualification and RX/legacy cleanup remain open.


## TX entrance overlap resolved

TP13 relocated and TRIPLER_OUT routing rebuilt and checked. See `tx_entrance_routing.md` and `tx_entrance_validation.json`. Current DRC: 519 errors, 211 warnings, 118 unconnected items. RX placement and U10 physical audit are next; initial RX findings are recorded in the entrance report.


## U10 identity audit

Pin map and CD636/PL052 solder lands verified; PCB metadata corrected with no geometry change. See `u10_ade1_pinmap.md`. The linked CD542 3D model and unsaved schematic-editor reconciliation remain open. RX filter placement is pending.
