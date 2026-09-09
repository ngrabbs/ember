# Mixer IF routing — 2026-09-09

Routed U10 IF pin 2 to the existing R34 termination and relocated C99 coupling capacitor at (159.6, 123.2), with RX_IF continuing through two vias on B.Cu to TP15 and the existing R20 input route. Component values and all pad nets remain unchanged. R34 now has a 0.6 mm / 0.3 mm ground via. Signal tracks added in this pass are 0.358 mm wide.

Removed eight obsolete +5V segments crossing the mixer area, the old R34 ground dogbone/via, and the obsolete C99-to-TP15 segment. Added 16 copper items; 742 total, 141 footprints. All retained copper geometry and net assignments were verified unchanged, as were all component fields and pad nets. C99 and R34 were also read back through live Konnect after reopening.

Main-board DRC: 479 errors, 200 warnings, 98 unconnected items (previously 501 / 202 / 101). No violations reference new copper or C99/R34/C77. Existing TP15/R20 courtyard and labeling problems remain for later cleanup. This is an incremental routing result, not fabrication approval.

The F.Cu mixer IF trace has the RF pour setback. Ground sampling under this and previously routed RX RF paths found no missing L2 ground at 3,740 sample positions, including lateral margins. The post-coupling B.Cu RX_IF route is not claimed to be a controlled 50-ohm transmission line. Both front and combined front/back plots were inspected.

Next: place and route the LO filter/driver to U10 pin 6; consolidate the mixer IF net's explicit RF netclass assignment; resolve remaining board-wide DRC and connectivity findings. L16 remains a prototype selection with RF qualification and the former SRF target still unresolved.
