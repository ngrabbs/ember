# IF test-point/resistor spacing — 2026-09-09

Moved TP15 left to (169,129.1132) and R20 slightly left to (171.1,129.0878), clearing the TP15/R20 and R20/R21 courtyard overlaps and TP15 silk clipping. R21 and adjacent filter components stay in place. Replaced five RX_IF segments with four 0.358 mm front-layer segments from the existing via through TP15 into R20; this also removes three old undersized RX_IF segments.

Values, fields, all pad nets and retained copper were verified unchanged. Both moved parts were read back through live Konnect, and the local front copper render was inspected. No DRC or unconnected findings reference TP15, R20, R21 or the added copper. Repaired board outline remains valid.

Main-board DRC: **439 errors / 149 warnings / 77 unconnected** (previously 444 / 150 / 77). 136 footprints and 761 copper items. Next: remove already-classified obsolete RX filter remnants, verify surrounding retained circuitry, and continue remaining connectivity. Full RF qualification and board-wide validation remain open; not fabrication-ready.
