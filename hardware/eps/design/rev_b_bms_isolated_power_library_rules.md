# BMS isolated-power library construction rules

2026-10-24. **Proposal; user approval required before authoring.** This covers a project-owned ADuM5028-3BRIZ symbol and a project-owned derivative of an existing stock footprint, retaining its eight copper/paste/mask lands and increasing the courtyard for the maximum package body. It does not approve electrical closure, manufacturing or flight use.

## Purpose and scope

The shared-positive ISO1540 development supply introduces a state-dependent error in battery-current measurement. Evaluate ADuM5028-3BRIZ to power the isolator's raw-reference side from permitted essential +3V3, without a direct positive-supply connection across the shunt reference. Input ground stays system GND; output return stays GND_BMS_RAW. The new output would be `3V3_BMS_ISO`. It powers only ISO1540 VCC2 and its two BMS-side pull-ups. No raw-cell LDO is added and this converter receives no power during RBF inhibition. Existing external interface names and the single shunt connection remain intact.

The converter is an electrical candidate pending complete load/ripple/startup, current budget and boundary checks. Do not replace ISO1540 or its supply in the real design merely because a symbol has been authored. ADM3260 is rejected as a direct substitute because its normally powered isolated side has a low-output specification above the BMS input-low limit.

## Library-first evidence

Registered project/global `ADuM502` search returned no symbols. The installed stock `Package_SO:SOIC-8_7.5x5.85mm_P1.27mm` exists and was queried with all graphics and pads; [readback](../verification/bms/isolated_power/stock_footprint.json). Do not edit vendor libraries or make another footprint solely for convenience. The stock nominal-body courtyard does not provide 0.25 mm around the maximum package body. The explicitly bounded derivative below addresses that documented gap; it is not a new manufacturer land-pattern claim.

## Primary sources actually inspected

The current [ADI product page](https://www.analog.com/en/products/adum5028.html) links the exact -3BRIZ order code to its [pin diagram](https://mds.analog.com/api/public/content/adum5028-pc.png) and [RI-8-1 package drawing](https://mds.analog.com/api/public/content/RI_8_1.pdf), PKG-004099, 09-17-2014-B. Both figures were downloaded and actually viewed; [source images/hashes](../verification/bms/isolated_power/sources.json). The transparent pin diagram was also composited onto white to make its black function labels readable; the original is retained.

[ADuM5020/5028 Rev E](https://www.analog.com/media/en/technical-documentation/data-sheets/adum5020-5028.pdf), Table 14, independently supplies the pin functions. The full PDF's local download timed out, so no full datasheet render is claimed. The primary electrical text remains available. Obtain and view the relevant application figure before claiming that the native circuit follows it.

## Symbol construction

Create `ADuM5028-3BRIZ` in the existing registered project-owned EMBER EPS symbol library through Konnect only. Use a single unit with all eight numbered pins exposed. Keep primary pins to the left and secondary pins to the right, recognizing that the verified physical map, rather than drawn pin order, determines connectivity. A split body or clear barrier graphic should distinguish the returns. Use the 1.27 mm electrical grid. Do not stack or omit either duplicate ground pin.

| Physical lead | Name | Electrical type | Planned function |
|---|---|---|---|
| 1 | PDIS | input | Tie through a visible wire to system GND for permitted-input operation; never floating |
| 2 | GND1 | power_in | System GND |
| 3 | VDDP | power_in | Permitted essential +3V3 |
| 4 | GND1 | power_in | System GND |
| 5 | GNDISO | power_in | GND_BMS_RAW |
| 6 | VISO | power_out | New isolated positive output 3V3_BMS_ISO |
| 7 | GNDISO | power_in | GND_BMS_RAW |
| 8 | VSEL | input | GND_BMS_RAW for 3.3 V output |

Required metadata: Reference U, exact Value/MFG P/N `ADuM5028-3BRIZ`, Analog Devices manufacturer, RI-8-1 package description, exact primary datasheet URL and the new registered project footprint identifier below. Preserve the source's -3 variant: the -5 part requires a different input range. No exposed pad, thermal pad, mechanical pin or NC pin exists in this eight-lead package.

## Footprint derivative and physical map

The package drawing is a top view: pins 1–4 run left to right along the bottom and 8–5 along the top, with the pin-1 chamfer/notch at the left. Normalize by a 90° clockwise visual rotation to the stock footprint's component-view/Y-down orientation: pin 1 upper left, 2–4 downward on the left, 5 lower right and 6–8 upward on the right. Record this transform explicitly; do not confuse the diagram with a bottom view.

The stock footprint has eight separate 1.80 × 0.60 mm roundrect pads, corner ratio 0.25, no drills, on F.Cu/F.Mask/F.Paste. Pin centers are X = ±5.325 mm; left Y = −1.905, −0.635, +0.635, +1.905 mm for 1–4 and right reversed for 5–8. Body nominal dimensions normalize to 7.50 × 5.85 mm, pitch 1.27 mm. The package limits are 7.40–7.60 × 5.65–6.05 mm, lead span 10.11–10.51 mm and height 2.35–2.65 mm.

This is a **generic stock land**, not a manufacturer-recommended exact pad layout. Record toe/heel overlap and excess pad length against the lead-envelope drawing, mask/paste behavior, silk/pin-1 key and courtyard. Its nominal courtyard margins do not automatically prove a 0.25 mm margin around the maximum package body. The readback has central body courtyard bounds X ±4.00 and Y ±3.18 mm, only 0.20/0.155 mm beyond the maximum body. Create the bounded derivative below to obtain at least 0.25 mm. PCB spacing and the complete mechanical envelope remain separate gates; neither land-pattern solderability nor manufacturing acceptance follows from the courtyard correction.

## Exact derivative construction

Proposed footprint identifier: `Ember_Charger_BMS_Review:ADI_RI-8-1_SOIC8_StockLand_MaxBodyCourt_REVIEW`. Create through Konnect in the existing registered project footprint library. Retain all eight stock pad numbers, centers, sizes, roundrect ratios and F.Cu/F.Mask/F.Paste layers exactly as queried. Retain the stock nominal body/F.Fab and F.SilkS/pin-1 graphics. No exposed pad, drill, copper pad, paste aperture or electrical-number change is permitted. The derivative is based on the queried stock lands, with maximum-body courtyard accommodation; it is **not an exact manufacturer-recommended land pattern**.

Replace only F.CrtYd with a closed, unfilled stepped polygon, 0.05 mm stroke, using these component-view/Y-down millimeter vertices in sequence:

```text
(-6.48,-2.46), (-4.05,-2.46), (-4.05,-3.28),
(+4.05,-3.28), (+4.05,-2.46), (+6.48,-2.46),
(+6.48,+2.46), (+4.05,+2.46), (+4.05,+3.28),
(-4.05,+3.28), (-4.05,+2.46), (-6.48,+2.46)
```

The body margins are 4.05−3.80 = 0.25 mm and 3.28−3.025 = 0.255 mm; copper-pad outer margins are 6.48−6.225 = 0.255 mm and 2.46−2.205 = 0.255 mm. Record source and derivative graphics/pad comparisons. Preserve the stock 3D association only after its path and package identity are verified through query-back or permitted read-only metadata inspection; otherwise omit it and record 3D/mechanical verification open. Do not invent a model or assert 16 mm stack clearance from a footprint alone.

## Review marker and verification

Repository schematic policy S08 requires custom symbol body outlines in bright green and a visible `CUSTOM — REVIEW REQUIRED` marker. Konnect currently cannot color symbol bodies. Proposed alternative: the same bright-green review enclosure/callout used for the previously approved charger/BMS symbols, explicitly naming this new custom symbol. Do not claim the symbol body itself is green. Retain the marker pending user review.

After authoring, query every pin/function/type and every required field. Build an independent disposable schematic and board through Konnect, read back all eight placed pins/pads and save/requery. Inspect actual page/detail symbol, copper, numbered fabrication and pin-1 views. Verify raw pad cardinality, exact numbers, geometry/layers and no hidden/extra pads. Preserve all previous fixtures and real-board geometry. Do not place the part in the real design until the physical-map gate and remaining electrical candidate checks pass.
