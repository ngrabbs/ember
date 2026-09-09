# TX filter entrance cleanup — 2026-09-09

Moved TP13 to (143.9,126.223) mm to clear C93 and Q3. Rebuilt the TRIPLER_OUT connection with 0.358 mm F.Cu routing and moved the TP13/C93 labels. The direct Q3 collector-to-C93 input feed is preserved; TP13 is on a 1.578 mm probe branch beyond C93. Probe-pad and branch parasitics remain part of RF bench qualification; this is not a claim of a perfect 50-ohm transition.

Four old track segments were removed and three added. All retained copper, all pad net assignments and all footprint placements except TP13 were verified unchanged. A top-pour-only clearance area was added. All 200 RF centerline, edge and return-region samples hit filled L2 GND. The temporary-board render was inspected before applying with native KiCad while the saved PCB editor was closed, then the board was reopened and TP13 verified live through Konnect.

The saved board has no DRC violations involving the new traces, TP13 or C93. Full DRC is now **519 errors, 211 warnings, 118 unconnected items**; total 141 footprints and 689 copper items. Fabrication, thermal and RF-performance acceptance remain open.

## RX review started

C56, L12, C60 and L13 remain off-board. The first RX resonator is C55.2/L12.1/C56.1; C60 couples it to the next resonator on L13.1. These components need a coherent placement before extending the switch's RX branch. U9 remains the PSA4-5043+ amplifier at its existing placement.

U10's schematic value is ADE-1+, using the RF_Mixer:ADE-6 symbol and RF_Mini-Circuits:Mini-Circuits_CD542_LandPatternPL-052 footprint. The [manufacturer ADE-1+ product page](https://www.minicircuits.com/WebStore/dashboard.html?model=ADE-1%2B) identifies CD636 and PCB layout 98-PL-052. The shared PL-052 name may explain the different footprint case name, but name similarity is not physical-footprint acceptance. Native readback shows multiple same-number GND copper pads; these must be distinguished from physical package leads during the audit. Do not renumber or replace U10 based only on those duplicated logical ground numbers. Manufacturer top/bottom/package drawings and complete lead-to-pad geometry reconciliation remain required before routing release.
