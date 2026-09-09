# L16 prototype selection and footprint acceptance

2026-09-09. Manufacturer: Coilcraft. Exact prototype MPN: **0805HP-221XJRC** (220 nH, J=5%, R=matte tin termination, C=reel packaging). Symbol `Device:L`; footprint `Ember_RF:L_Coilcraft_0805HP`. Source: Coilcraft document 1362-1/-2, revised 04/11/22, pages 1–2: https://www.coilcraft.com/getmedia/c30565bc-9cf5-4393-9380-6f782e4b4cd8/0805hp.pdf . Page 2 was rendered and visually inspected.

## Physical mapping

The manufacturer drawing shows two equivalent wraparound terminals and an unnumbered, nonpolar recommended land pattern. Rotate the depicted vertical land arrangement onto a horizontal axis; the left terminal is assigned logical 1 and the right terminal logical 2. This is a library convention, not a manufacturer polarity claim. Swapping terminals does not reverse a polarized function.

| Physical terminal | Function | Symbol pin/name/type | PCB pad | Local center mm | View and evidence |
|---|---|---|---|---|---|
| Left after land-pattern rotation | Inductor end, +5 V in this circuit | 1 / 1 / passive | 1 | -1.07, 0 | Component-side land view; source p2 recommended pattern |
| Right after land-pattern rotation | Inductor end, OUT/DC in this circuit | 2 / 2 / passive | 2 | +1.07, 0 | Same view; interchangeable unpolarized terminal |

Two physical terminals, two symbol pins, two SMD electrical pads. No duplicates, holes, exposed pads or mechanical-only terminals. Pad width F=1.02 mm along the terminal axis, height H=1.98 mm across it, gap G=1.12 mm; center spacing F+G=2.14 mm. Front copper/paste/mask only; no drill. Body maximum 2.21 × 1.73 mm, 1.55 mm maximum height before the source's optional solder allowance. Courtyard extends 0.25 mm beyond the pad envelope. The left silk bar and fab chamfer identify the library's pad-1 convention. No unrelated generic 3D model is carried over.

Existing library search found no 0805HP footprint. Konnect created the footprint; symbol and footprint queries were read back. A disposable symbol and native PCB instance were placed, reread and rendered. Both pad coordinates, sizes, layers and zero drills agree with the table. The schematic symbol has two passive pins. The final silk was moved outside the board's solder-mask clearance and checked in the full-board preview.

## Electrical scope

Prototype choice follows the existing 220 nH bias-choke plan. The manufacturer's table gives 930 MHz **typical** SRF, Q 75 **typical at 250 MHz**, 0.426 ohm maximum DCR and 0.5 A reference current for a 15 °C rise. The published typical L curve remains inductive around 435 MHz. Ideal reactance at 435 MHz is 601 ohms; this calculation is not measured choke impedance. At an assumed 100 mA design current, the 25 °C DCR figure gives 42.6 mV and 4.26 mW.

This selection **does not satisfy the old >1.5 GHz SRF target**, and no requirement is silently marked met. It is a prototype configuration for RF measurements, not fabrication/production qualification. Gate remains open: validate choke impedance/isolation over the operating band under bias and check assembled gain, return loss, stability and supply sensitivity; resolve or revise the old SRF target with that evidence. Use the exact MPN for purchasing; the old LCSC C18221300 must be removed to avoid ordering the former 1 µH part.

## Saved-board integration

L16 was moved to (158.3,129.55), 0 degrees, and C75 to (158.9,131.75), 0 degrees, to accommodate the larger manufacturer pads. Six RF segments were replaced with six adjusted segments. Retained copper and all pad nets are unchanged; other footprint fields and placements are unchanged. The L16 footprint UUID and schematic path were preserved. Both schematic and PCB specify 220n / Coilcraft / 0805HP-221XJRC / Ember_RF:L_Coilcraft_0805HP. The obsolete LCSC code was cleared. The saved schematic component export verifies these purchasing fields; it is not a fresh full ERC or proof that the known CLI hierarchy/net-export discrepancy is resolved. Live Konnect pad readback confirms pad 1 +5V at (157.23,129.55) and pad 2 OUT/DC at (159.37,129.55).

Main DRC remains 501 errors, 202 warnings and 101 unconnected items. New copper has no violations; L16/C75 have no new placement, clearance or label violations in the main project. Ground sampling includes the new routes plus the preceding RX/adjusted-bias paths: 3,460 samples all contact filled L2 GND. The 141-footprint, 738-copper-item board is still not fabrication-ready.
