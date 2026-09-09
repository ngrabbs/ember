# Obsolete RX filter removal — 2026-09-09

Removed C29/C30/C31/C32/L9/L10/L11, the obsolete RX input filter classified in `unmatched_pcb_classification.md`. The active C55/C56/C60/C64/C67/L12/L13 replacement was already placed and routed. Before removal, no retained footprint pads belonged to the obsolete /RX_IN, Net-(C29-Pad2), Net-(C30-Pad1) or Net-(C30-Pad2) nets.

Removed 32 reviewed copper items: the obsolete network's named tracks/vias, its local unnamed filter interconnects, and two dedicated ground dogbones/vias. No new copper was added. All retained copper signatures, footprint positions, fields and pad nets were verified unchanged. Final board has 129 footprints and 729 copper items. The cleared area was rendered and inspected. Previously checked RX/IF/LO/Q4 paths retain ground at all 5,355 sample positions. The repaired outline remains valid.

Saved-board DRC: **387 errors / 129 warnings / 69 unconnected**, previously 439 / 149 / 77. The reduction includes removal of obsolete dangling connections; it is not evidence of eight newly routed active connections.

Fresh DRC also reports unresolved issues on unchanged retained items around legacy U1, crystal C2/unnamed clock copper, J6/SPI and H3/ground. Full comparison is recorded in the validation JSON; these were not fixed in this pass. Next: audit legacy U1 against U5 and correct the remaining shorting/unnamed copper before further routing. Bench RF qualification and shared supply budget remain open. Not fabrication-ready.
