# Managed-feed passive selections and DC screen

2026-10-24. `parts.csv` specifies all 37 proposed passives: 23 resistors and
14 capacitors. Together with the 12 proposed semiconductors, these retain the
49-part branch count. **None is integrated by this packet.** No real EPS circuit or PCB source changed. The separately approved TDK
footprint and disposable fixture are now constructed; all222 prior native
files are preserved by that package verifier.

The exact resistor order codes follow [Vishay 28758, 10-Apr-2026](https://www.vishay.com/docs/28758/tnpw_e3.pdf).
Use B=0.1%, E=25 ppm/K and EA packaging. R1424=1 MΩ requires **0805**;
0603's selected precision range stops at 332 kΩ. R1412 uses1210 for power and the configured60% utilization limit.
Other values fit0603. General-mode P70 fields are0.110/0.140/0.330 W for
0603/0805/1210, with derating, rather than the larger advanced-mode headline
ratings. Purchase/lot confirmation remains open.

`python3 check.py` decodes the selected values, checks family ranges and
regenerates the manifest and DC screen. It applies the imposed35 V source
ceiling, independent0.1%/25 ppm corners and the published general-mode85°C
derating. Source-connected upper resistors conservatively see the full35 V;
bottom resistors use divider corners without clamp credit. Control pins use
explicit3.6 V or5.5 V stress assumptions. All23 pass that scoped arithmetic.
Worst utilization is R1412:122.82 mW versus240 mW derated general allowance,
or51.18%. It is below the configured60% ceiling (144 mW). The1206 option
would reach62.55% under the same conservative full-voltage screen.
This excludes pulse/open-short fault acceptance, board thermal proof and
long-term drift. Existing threshold calculations include initial/TCR corners,
not a mission-life drift allowance; flight threshold acceptance remains open.

C1405/C1406 select [TDK CGA3E2C0G1H102J080AA](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA3E2C0G1H102J080AA):
1 nF,5%,50 V,C0G,0603. Other capacitor MPNs retain the prior screened choices.
No claim is made that nominal X7R values equal effective input capacitance.

The manufacturer's live land diagram and ranges were visually inspected;
`TDK_lands_browser.png` records them. Its reflow PA/PB/PC ranges are0.60..0.80 mm.
The stock capacitor pads0.90×0.95 mm exceed that recommendation despite a
valid0.65 mm gap. The manifest therefore identifies the separately approved
[project footprint](../../../design/rev_b_payload_tdk_filter_footprint_rules.md),
now [constructed and verified](../tdk_filter_package/README.md). Stock parts
were preserved. Stock resistor lands
also differ from Vishay's representative IPC/IEC patterns; this packet records
the differences instead of calling them exact manufacturer lands.

Structural/calculation evidence and actual rendered-source inspection are
separate: Vishay pages1/2/3/4/6/15 and land document28950 p1 were opened and
inspected, as was the TDK live gallery drawing/table. `source_review.json`
records image hashes. The TDK PDF fetch returned403; no PDF-byte or PDF-render
inspection is claimed. No new circuit sheet was rendered, ERC run or assembly
pass established here. Sources and stock query packets are retained locally.
