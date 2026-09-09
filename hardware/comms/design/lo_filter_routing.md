# LO filter routing — 2026-09-09

Placed and routed the current C86 → C90/L20 → C91 → C95/L22 → C97 band-pass filter into U10 LO pin 6. Values, footprint geometries and all retained component pad nets/fields are unchanged. Removed C22/C23/C24 and LEGACY_L12/LEGACY_L13, previously classified as the obsolete LO low-pass filter, together with its signal copper and local ground dogbones/vias.

Moved the crossing RX_BASEBAND run from J7 pin 9 to B.Cu, rejoining the retained front trace near (172.866,118.56206) through a new 0.6/0.3 mm via at (173,118.3). This is a baseband route, not a 50-ohm RF claim. Added four 0.6/0.3 mm grounded vias beside the filter shunts. Removed 30 copper items and added 28; final board has 136 footprints and 740 copper items.

RF traces are 0.358 mm F.Cu with the existing microstrip pour-setback approach. Sampling the new LO paths and previously accepted RX/IF paths found continuous L2 ground at 4,410 sampled positions, including lateral margins. All retained copper signatures were unchanged; planned new nets, dimensions, layers and via drills were verified. Front-layer plots were inspected. Seven relocated filter components were queried through live Konnect after reopening. Explicit RF netclass assignments were added and read back for both LO resonator nodes, U10 LO and U10 IF.

Main-board DRC: **460 errors / 167 warnings / 87 unconnected**, previously 479 / 200 / 98. No violations reference the added copper or the seven relocated filter components. Existing U10/C57 courtyard conflict, overlapping legacy ground drill holes near U10 pins 4/5 and neighboring silkscreen issues remain. Reference labels above the header are provisional and need final assembly readability review.

Next: place/connect Q4, C83/R33 input bias, L18/C85 collector network, C82 bypass and supply feeder to C86. The filter input is not yet connected to the off-board Q4. Verify the entire LO chain and drive level after completing routing. Older 145.9 MHz direct-LO bench notes describe a superseded topology; do not treat them as acceptance for this UHF tripler path. This is not fabrication approval. L16 RF qualification remains open.
