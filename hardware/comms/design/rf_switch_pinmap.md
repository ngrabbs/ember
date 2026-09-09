# RF switch component pin-map acceptance

Datasheets: [PE4259 DOC-03694-5.01, July 2026, pp. 11–12](https://www.psemi.com/pdf/datasheets/pe4259ds.pdf); [TLV755P SBVS320D, September 2024, p. 3](https://www.ti.com/lit/gpn/TLV755P); [SN74LVC1G17 SCES351Y, October 2025, p. 3](https://www.ti.com/lit/gpn/sn74lvc1g17). Exact DBV order suffixes used; no DQN, DCK, or DRV substitution.

Disposable schematic and native PCB placements rendered and queried. PE4259 symbol was enlarged/rearranged after the first render revealed text overlaps, refreshed in scratch, queried and rendered again. Physical lead functions stayed unchanged. All pad coordinates below are local to an unrotated F.Cu footprint (screen Y increases down). Top-view pin 1 is upper left; numbering proceeds down the left side and up the right.

## pSemi 4259-63 (PE4259), SC-70-6

Symbol: Ember_RF:PE4259. Footprint: Package_TO_SOT_SMD:SOT-363_SC-70-6.

| Physical lead | Function / symbol pin | Pad | X / Y mm | Pad W / H mm | View / direction |
|---|---|---|---|---|---|
| 1 | RF1 / 1 | 1 | -0.8375 / -0.65 | 1.025 / 0.35 | Top, counterclockwise from upper-left key |
| 2 | GND / 2 | 2 | -0.8375 / 0.0 | 1.025 / 0.35 | Top, counterclockwise from upper-left key |
| 3 | RF2 / 3 | 3 | -0.8375 / 0.65 | 1.025 / 0.35 | Top, counterclockwise from upper-left key |
| 4 | CTRL / 4 | 4 | 0.8375 / 0.65 | 1.025 / 0.35 | Top, counterclockwise from upper-left key |
| 5 | RFC / 5 | 5 | 0.8375 / 0.0 | 1.025 / 0.35 | Top, counterclockwise from upper-left key |
| 6 | VDD / 6 | 6 | 0.8375 / -0.65 | 1.025 / 0.35 | Top, counterclockwise from upper-left key |

Counts: 6 physical leads, symbol pins, and pads; no duplicates, exposed pads or mechanical holes. SMD front copper/paste/mask; all drills zero.

## Texas Instruments TLV75530PDBVR, SOT-23-5 DBV

Symbol: Regulator_Linear:TLV75530PDBV. Footprint: Package_TO_SOT_SMD:SOT-23-5.

| Physical lead | Function / symbol pin | Pad | X / Y mm | Pad W / H mm | View / direction |
|---|---|---|---|---|---|
| 1 | IN / 1 | 1 | -1.1375 / -0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 2 | GND / 2 | 2 | -1.1375 / 0.0 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 3 | EN / 3 | 3 | -1.1375 / 0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 4 | NC / 4 | 4 | 1.1375 / 0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 5 | OUT / 5 | 5 | 1.1375 / -0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |

Counts: 5 physical leads, symbol pins, and pads; no duplicates, exposed pads or mechanical holes. SMD front copper/paste/mask; all drills zero.

## Texas Instruments SN74LVC1G17DBVR, SOT-23-5 DBV

Symbol: 74xGxx:74LVC1G17. Footprint: Package_TO_SOT_SMD:SOT-23-5.

| Physical lead | Function / symbol pin | Pad | X / Y mm | Pad W / H mm | View / direction |
|---|---|---|---|---|---|
| 1 | NC / 1 | 1 | -1.1375 / -0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 2 | A / 2 | 2 | -1.1375 / 0.0 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 3 | GND / 3 | 3 | -1.1375 / 0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 4 | Y / 4 | 4 | 1.1375 / 0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |
| 5 | VCC / 5 | 5 | 1.1375 / -0.95 | 1.325 / 0.6 | Top, counterclockwise from upper-left key |

Counts: 5 physical leads, symbol pins, and pads; no duplicates, exposed pads or mechanical holes. SMD front copper/paste/mask; all drills zero.

Stock KiCad SC-70 pad geometry is the library land pattern, not an exact copy of pSemi’s recommended 0.90 × 0.40 mm lands on 2.10 mm row centers. It matches the 0.65 mm lead pitch and package orientation; pad outer edges extend beyond the maximum package lead ends. Assembly/paste and RF launch still need layout review.

Evidence: outputs/rf-switch-scratch.png, outputs/rf-switch-packages.svg, work/rf-switch-scratch/native-pads.json, and MCP library/pin readbacks under work/rf-*.json in the Codex working directory.
