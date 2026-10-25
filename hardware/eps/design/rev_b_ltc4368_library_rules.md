# LTC4368-1 development library construction rules

2026-10-24. **Operator approved construction on2026-10-24.** Construction authorization applies only to the exact library part and disposable fixture below. It does not select an essential3V3/RBF circuit, authorize main integration or accept electrical/flight behavior.

## Source and search

Primary source: [ADI LTC4368 RevC](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4368.pdf), pin/order table p2, electrical characteristics pp3–4, pin descriptions pp7–8 and MS10 package drawing p19, LTC drawing05-08-1661 RevF. Select **LTC4368IMS-1#TRPBF**, industrial−40..85°C, MS10, bidirectional±50mV nominal current-breaker variant. No substitution of−2 (−3mV reverse trip), C/H/W grade, DD package or reel suffix. Procurement remains separate.

Fresh registered symbol search `LTC4368` returned zero. Global/project inventory includes no KiCadLib nickname; that absence is not a claimed negative search inside an unavailable library. The stock `Package_SO:MSOP-10_3x3mm_P0.5mm` has ten1.50×0.35mm lands atX±2.10mm. ADI's example uses0.889±0.127mm length and0.305±0.038mm width, so propose an exact project land instead of silently treating the larger stock lands as ADI geometry. Do not modify vendor libraries.

## Symbol contract

Append only `Ember_Charger_BMS_Review:LTC4368IMS_1_REVIEW` to the existing project review library; proposed footprint `Ember_Charger_BMS_Review:ADI_MS10_05_08_1661_REVIEW`. One readable rectangular unit, ten visible separate physical pins, no hidden power, NC, EP or stacked aliases. Exact physical MS10 top-view mapping:

|Pin|Name|Electrical type|
|---|---|---|
|1|VIN|power_in|
|2|UV|input|
|3|OV|input|
|4|RETRY|bidirectional: configuration input and timer-current path|
|5|GND|power_in|
|6|SHDN, overbar visible|input|
|7|FAULT, overbar visible|open_collector|
|8|VOUT|input: monitored terminal and internal bias path, not an output driver|
|9|SENSE|input|
|10|GATE|output|

GND is physical5, RETRY4, SHDN6: do not copy the eight-pin LTC4367 map. No optional DD exposed pad11 belongs on the MS10 part. Use VIN above, GND below, UV/OV/SHDN left, GATE/SENSE/VOUT/FAULT right and RETRY below with room for its grounded timer. Use1.27mm grid,2.54mm pin separation where needed, visible electrical stubs and a clear Value/MPN block. Pin-coordinate queries decide actual wiring anchors, never inferred body centers.

Require ReferenceU, Value and `MFG P/N=LTC4368IMS-1#TRPBF`, `Manufacturer=Analog Devices`, exact Datasheet/Footprint, `PackageSize=MS10 / MSOP-10`, description and review status. Preserve exact property names, all fields and prior symbol subtrees. Apply S11 display operations only as actually supported; adjacent readable callouts document unsupported field defaults/anchors without claiming full compliance.

## Exact manufacturer-example land

Front/component view, millimetres, Ydown. Five lands per side on0.50mm pitch. Pads1–5 atX−2.1055,Y−1.0/−0.5/0/+0.5/+1.0; pads6–10 atX+2.1055,Y+1.0/+0.5/0/−0.5/−1.0. Ten numbered rectangular SMD lands **0.889×0.305mm**, F.Cu/F.Paste, no drill or rotation; dedicated mask-only apertures below define F.Mask. This gives5.100mm outer copper span and3.322mm inner gap, within ADI's3.20–3.45mm inner-gap example. Copper/paste adjacent gap0.195mm. No arbitrary corner rounding, paste shrink or extra thermal feature.

Implementation clarification after disposable testing: omit F.Mask from the numbered Cu/Paste pads, because the default board mask margin would otherwise override the approved aperture. Ten blank-number F.Mask-only rectangular apertures **0.969×0.385mm** at the same centers provide a proposed+0.04mm nominal mask expansion. Number counter1..10eachonce andblank10; **20 raw pad objects,10 electrical numbers,10 copper/paste regions,10 effective mask regions**, no holes/EP. The intended mask web is0.115mm. Query effective inherited mask settings and inspect rendered apertures; if larger inherited settings override these bounds, stop mask acceptance and report it. Fabricator mask tolerances remain open.

F.Fab nominal3.00×3.00mm body, pin1 chamfer upperleft and readable reference/value. MS10 maximum lead span5.052mm; body nominal3mm with±0.102mm size and separately allowed0.152mm flash per side gives a conservative3.406mm body envelope. Closed unfilled F.CrtYd **X±2.85,Y±2.00mm** (5.70×4.00mm),0.05mm stroke: at least0.25mm outside intended mask and flash-inclusive body. No guessed3D model. Silk0.12mm, top/bottomY±1.82mm with clear pin1 marker, never crossing effective mask. Verify actual extents and field clearances in saved/rendered fixture.

## Review marker and verification

S08 body-color support remains unavailable in the installed Konnect schema. The operator approved a bright-green#00FF00 enclosure/callout **CUSTOM — REVIEW REQUIRED; construction authorized: LTC4368IMS-1#TRPBF**, retained after development acceptance. Do not claim the body itself is green or change theme/DNP/connectivity to mark review status.

After approval, use Konnect for every library/table/project/disposable mutation. Freeze the then-current source/evidence state; do not alter historical fixtures or verification baselines. Build a new independent ANSI B symbol and PCB fixture with one instance. Query all ten symbol pins/types/default fields and all20 raw pad objects before dictionaries. Verify the exact source MS10 map, top/bottom view, pin1, unique numbers, layer sets, geometry, apertures and clearances. Export and actually inspect full/detail schematic plus copper, paste, mask, silk, courtyard and numbered fabrication views. Fresh CLI netlist/ERC is separate electrical evidence; retain honest unwired-pin findings, without fake NC flags. Confirm old native source/UUID/metadata preservation and exact append-only library change. No real EPS PCB placement/synchronization.

Electrical integration stays gated on supply/gate-drive loading, UV/OV threshold/hysteresis, total opening delay at actual supply/gate charge, current-breaker behavior and reset ownership, source/magnetic bounds, raw-bank voltage rating, downstream capacitance and stability, turn-off clamp, MOSFET hot SOA, startup/prebias and all-path backfeed. The library candidate's20V OV-pin rating removes the LTC4365-specific5V sense-pin issue for the35V/58.8k/10k example; that is a rating comparison, not overall circuit acceptance. No interpolation of typical gate-drive curves into a guaranteed MOSFET resistance or timing limit.
