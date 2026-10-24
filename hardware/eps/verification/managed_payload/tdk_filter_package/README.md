# TDK filter footprint disposable verification

2026-10-24. Constructed through Konnect under the user's approved
[exact rules](../../../design/rev_b_payload_tdk_filter_footprint_rules.md).
Project footprint:
`Ember_Charger_BMS_Review:C_0603_TDK_CGA3_PA0.70_PB0.70_PC0.70_REVIEW`.
No new symbol: stock `Device:C`, exact part CGA3E2C0G1H102J080AA.
The green **CUSTOM FOOTPRINT — REVIEW REQUIRED** marker remains.

| Physical terminal, front view | Symbol pin/type | Footprint pad | Center mm |
| --- | --- | --- | --- |
| Left, interchangeable | 1/passive | 1 | −0.70,0 |
| Right, interchangeable | 2/passive | 2 | +0.70,0 |

`verify.py` checks all222 baseline native files unchanged and exactly five
new native paths: the footprint, disposable project/schematic/board and its
portable footprint table. The real EPS circuit and PCB are unchanged.
Konnect0.11.1/KiCad10.0.0 closed-board placement was used: IPC/UI were absent
and the disposable board was created during this session. No unknown unsaved
board state was overwritten. No claim of live IPC verification is made.

Electrical/structural evidence: two2-terminal passive endpoints in CLI XML;
four raw footprint objects, electrical numbers1/2 once each plus two blank
mask-only pads. Copper/paste pads0.70×0.70 mm, radius0.05; mask-only pads
0.80×0.80 mm, radius0.10. No drills/model/polarity marker. Saved library and
board pad queries match. The actual CLI mask export, including the board's
0.05 mm inherited margin, has two coincident pairs of openings: **two effective
0.80 mm mask regions**, giving+0.05 mm around copper and0.60 mm web. Courtyard
is2.70×1.40 mm, including the specified maximum body/mask clearances.
Recheck effective mask geometry when this is placed in the real board.

Actual rendered inspection was separate: ANSI B `symbols.png`,
`symbol_detail.png`, combined `board_detail.png`, copper/paste/mask montage,
courtyard and silkscreen details, and the query-derived numbered copper view
were opened and inspected. The combined render includes the fab body and full
package identifier. Numbers over copper are an overlay, not native artwork.
No fabricated pin key is shown for this unpolarized device.

The deliberately unwired fixture has **two genuine unconnected-pin ERC errors**;
no suppressions were added. Generic fixture ignored-check defaults remain
listed in `erc.json`. This is not an ERC-clean circuit or a full policy pass.
Exact sourcing/rating metadata is preserved and checked via CLI XML; installed
tools cannot position/show the native auxiliary fields. Visible annotations
show those values, but **S11 native field presentation remains incomplete**.
Board Value is the package identifier, not an assembly MPN. Construction and
geometry verification do not release assembly/stencil processing, coupled
filter response, or hardware/flight qualification.
