# RX input filter routing

Saved 2026-09-09. C55 feeds C56/L12, C60, C64/L13 and C67 into U9 pin 3. U9 and six filter parts are placed on board to the right of U8. The single antenna and PE4259 switching topology are unchanged.

The three RX signal nets use the RF netclass and 0.358 mm F.Cu traces. Pour-only keepouts provide the established microstrip setback; L2 remains the ground reference. The long approach from C55 follows the bottom corridor inward of the board notch. Bench insertion-loss, matching and isolation measurements remain required, particularly for this approach length near the TX amplifier.

L15, C71 and C76 were shifted to clear the corridor. Their local bias connections were rerouted, and C105 supply/ground vias moved above its pads. Eighteen explicitly reviewed copper items were replaced; 45 were added. All retained copper, component fields and pad nets were verified unchanged. No schematic topology edits were made.

Validation: 141 footprints, 716 copper items. Main-board DRC: 519 errors, 211 warnings and 107 unconnected items (previously 118). No DRC violation involves new copper. Moved-component checks found no new clearance, courtyard or label violations; legacy U9 output-via and library findings remain. All 2,125 sampled points beneath new RF traces and the adjusted U8 bias branch contact filled L2 GND, including trace edges and the selected return-width offsets.

Remaining: U9 ground stitching, bias via/L16/C75 placement and routing to U10 RF pin 3; existing global supply islands; full-board DRC/ERC and RF/thermal qualification. This pass does not establish fabrication readiness.
