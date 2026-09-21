# Antenna protection package acceptance

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


Candidate accepted for layout: Nexperia PESD5V0F1BRLD, DFN1006D-2 / SOD882D. Source: [datasheet v.2, 29 April 2024](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BRLD.pdf), pages 2, 7–8. Two interchangeable bidirectional terminals; no polarity requirement in this circuit.

| Physical lead | Function | Device:D_TVS pin / type | Diode_SMD:D_SOD-882D pad | Pad center, mm | View |
|---|---|---|---|---|---|
| 1 | K1 | 1 / A1 / passive | 1 | -0.4, 0 | Transparent top, left |
| 2 | K2 | 2 / A2 / passive | 2 | +0.4, 0 | Transparent top, right |

The generic symbol's A1/A2 names describe its abstract terminals, not a claim that the device's physical cathodes are anodes. Two physical leads, two electrical symbol pins, two numbered copper pads, no duplicate electrical pads, no mechanical holes. Two additional unnumbered F.Paste-only pads are intentional stencil apertures.

Native saved-instance readback: copper pads 0.5 × 0.7 mm, F.Cu/F.Mask, no drill; paste apertures 0.3 × 0.6 mm centered at ±0.35 mm, F.Paste only. Stock pad corners are rounded; solder-mask opening inherits board settings rather than hard-coding the drawing's 0.05 mm expansion. Courtyard extends 0.25 mm beyond copper. Library query, disposable schematic placement, native PCB placement/reload, and both renders passed. Pin 1 is on the marked left side in top view.

Electrical candidate: 5.5 V standoff, 0.4 pF typical / 0.55 pF maximum capacitance. At the current simulated +11.9 dBm into 50 Ω, a sinusoid is approximately 1.25 V peak, or 2.49 V for a doubled voltage under ideal full reflection. This is a voltage-headroom calculation, not system ESD qualification. Actual clamping, layout parasitics, receiver survivability and VNA performance remain bench requirements.

## Implemented D15 — 2026-09-09

D15 is wired across ANT/GND on RF_Switch and synchronized through the native UUID-based PCB update. Pad 1 = GND; pad 2 = ANT. F.Cu position (131.5, 139.65) mm, rotation 90 degrees; pad 1 center (131.5, 140.05), pad 2 center (131.5, 139.25). J9 remains the only antenna connector. The RF conductors and local ground connection still require routing.

Native ERC after insertion: zero active errors/warnings, existing two exclusions and four ignored checks unchanged. Konnect reports zero floating wires, unconnected required symbol pins, shorts and orphan items on RF_Switch. Final refilled PCB DRC: 626 errors, 268 warnings, 159 unconnected items; no violations involving D15 or C102. All 633 retained track/via objects match the pre-D15 geometry and net names after restoring nine legacy net names cleared by synchronization. Board contains 145 footprints including the 20 retained legacy items. Not fabrication-ready.

Placement updated during routing: D15 now (133.0,139.9) mm, 0 degrees; pad 1 GND=(132.6,139.9), pad 2 ANT=(133.4,139.9). Both sides routed; local ground via added. See rf_routing_progress.md for current validation.
