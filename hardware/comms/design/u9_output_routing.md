# U9 output, ground and bias routing

Saved 2026-09-09. U9 OUT/DC pin 1 now feeds C75, then U10 RF pin 3. L16 supplies the OUT/DC node; C77/C79 local bypass nodes are joined on In2.Cu and connected to the existing +5 V feeder near C71. The single-antenna switch and RX input filter remain unchanged.

C75 is at (158.9, 131.3), 0 degrees; L16 at (158.3, 129.15), 0 degrees. Both U9 ground pads have direct 0.4 mm dogbones to 0.6/0.3 mm through vias. Two obstructing legacy ground vias were replaced by 0.6/0.3 mm stitching vias nearby. All four new ground vias contact filled L2 and bottom ground. The obsolete OUT/DC via and four obsolete +5 V segments, including copper intruding into U10 RF pad 3, were removed after endpoint/pad review.

RF routes are 0.358 mm F.Cu, assigned to RF class, with pour-only setbacks. Bias supply traces are 0.3 mm; the local feeder runs on In2.Cu. The new feeder avoids existing ground vias. Full shared supply current/voltage-drop budgeting remains open; copper routing is not rail-budget acceptance.

Validation: 7 copper items removed, 28 added; 141 footprints and 737 copper items remain. All retained copper, component metadata, pad nets and unmoved footprint positions were compared to the saved baseline. New via nets, diameters and drills were verified after save. No DRC findings involve new copper; no new moved-part clearance, courtyard or label findings. Main-board DRC: 509 errors, 204 warnings, 102 unconnected items, versus 519/211/107 before this pass. Ground sampling across the new RF paths, prior RX input pass and adjusted U8 bias branch: 2,975 points, no missing L2 ground. This is local validation, not fabrication acceptance or a fresh ERC.

L16 remains 1 µH, LCSC C18221300, without a qualified UHF selection. The earlier project instruction to change it to 220 nH remains a candidate, not an accepted exact-part substitution. The local translated DDY record reports a typical 550 MHz SRF for WI0805QD1R0MST-HF, so the older blanket claim that every 1 µH part resonates at 200–400 MHz is not sufficient evidence. Obtain exact-part primary impedance data or bench measurements and validate the footprint before replacement. C75 RF insertion loss and complete receiver gain/noise figure also need measurement.

Primary amplifier reference: https://www.minicircuits.com/pdfs/PSA4-5043+.pdf ; product and evaluation-board links: https://www.minicircuits.com/WebStore/dashboard.html?model=PSA4-5043%2B . Existing package mapping evidence is in `rf_pinmap_audit.md`.

Remaining local issues: L16 qualification, legacy C77/C79 bypass vias (undersized and/or in-pad), full rail budget. Other global supply islands and remaining mixer LO/IF routing are still open.
