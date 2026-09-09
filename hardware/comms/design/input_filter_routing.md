# TX input filter routing — 2026-09-09

Placed the existing C98 (1.6 pF) on the board between the two resonators. Repositioned C96, L24, C100, C101 and TP14; retained component values and every pad net assignment. C101 is the final series coupling capacitor into U8; C100 is a shunt capacitor. No schematic topology or component-value changes were made.

The routed path is C93.2 → L23.1/C96.1 → C98.1, C98.2 → L24.1/C100.1 → C101.1, then C101.2 → TP14 → U8.1. Signal tracks are 0.358 mm F.Cu using the existing 50-ohm microstrip sizing record. Four 0.3 mm ground dogbones and 0.6/0.3 mm vias connect the resonator shunts to ground. A pour-only rule area maintains the established top-ground setback; the RF nets are explicitly assigned to the RF class.

Removed 39 obsolete copper items: four vias and 35 track segments, including unassigned former filter copper, incorrect ground connections and old TX_437 fanouts. Added 22 items: 18 tracks and four vias. All other copper geometry/net assignments and all other footprint positions were verified unchanged. Total remains 141 footprints, with 690 copper items.

## Validation

- Disposable native KiCad preview rendered and inspected before application; final geometry and labels have no new local DRC violations.
- Saved-board checks verify every new track's endpoint, width and net, all retained copper, all pad net assignments and unchanged placements outside this pass.
- No unconnected items remain on Net-(C93-Pad2), Net-(C100-Pad1), or TX_437.
- All 755 samples on the RF centerline, trace edges and wider return region contact filled L2 GND.
- Full saved-board DRC: **525 errors, 219 warnings, 118 unconnected items**, improved from 569/249/127. This is not fabrication acceptance.
- Live Konnect queries after reopening confirm C98, C101 and U8 pad assignments and positions.

The old TP13/C93 courtyard overlap and two related silkscreen issues remain at the filter entrance. They are identical to the previous DRC baseline and were not introduced by this routing. Review TP13 and the TRIPLER_OUT feed next. Other upstream circuitry, RX routing, legacy footprints and board-wide DRC remain open. Filter response, component parasitics, amplifier stability and thermal performance still require engineering/bench qualification; connectivity and DRC do not establish RF performance.

## Application

The board was saved through Konnect and closed cleanly. Its full track geometry/net assignments and pad positions were compared with the pre-preview inspection to rule out intervening changes. The validated preview was saved to the main board using native KiCad LoadBoard/SaveBoard with the PCB editor closed, then the PCB was reopened. RF netclass assignments were applied through Konnect before reopening. No KiCad source files were modified as text. A pre-application board copy is retained in the task working directory.
