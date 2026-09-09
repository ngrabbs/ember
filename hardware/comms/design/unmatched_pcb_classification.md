# Unmatched PCB footprint classification

Candidates below are evidence for review, not approved automatic replacements. Pad-net anchors use the 86 preserved UUID matches and full native netlist. Ground and supply matches alone are weak evidence.

| PCB reference | Value | Existing pad nets | Candidate schematic parts (matched anchored pads / comparable pads) |
|---|---|---|---|
| C31 | 10p | 1=GND, 2=Net-(C29-Pad2) | C82 (100n): 1/1; C81 (8.2p): 1/1 |
| C30 | 10p | 1=Net-(C30-Pad1), 2=Net-(C30-Pad2) | No anchored candidate |
| TP1 | TestPoint | 1=+3V3 | No anchored candidate |
| C24 | 10p | 1=Net-(U4-LO), 2=GND | C95 (9.1p): 1/2; C92 (9.1p): 1/2; C90 (9.1p): 1/2; C87 (9.1p): 1/2; C85 (8.2p): 1/2 |
| TP2 | TestPoint | 1=/+5V | No anchored candidate |
| J5 | Conn_Coaxial_Small | 1=/RX_IN, 2=GND | No anchored candidate |
| C19 | 10p | 1=Net-(C19-Pad1), 2=/TX_OUT | C94 (3.9p): 1/2; C92 (9.1p): 1/2 |
| C21 | 6.8p | 1=Net-(C19-Pad1), 2=GND | C92 (9.1p): 2/2; C95 (9.1p): 1/2; C94 (3.9p): 1/2; C90 (9.1p): 1/2; C87 (9.1p): 1/2 |
| L12 | 68n | 1=Net-(C22-Pad1), 2=Net-(C23-Pad1) | No anchored candidate |
| C22 | 10p | 1=Net-(C22-Pad1), 2=GND | C95 (9.1p): 1/2; C92 (9.1p): 1/2; C90 (9.1p): 1/2; C87 (9.1p): 1/2; C85 (8.2p): 1/2 |
| C29 | 10p | 1=/RX_IN, 2=Net-(C29-Pad2) | No anchored candidate |
| L10 | 82n | 1=GND, 2=Net-(C29-Pad2) | No anchored candidate |
| C23 | 33p | 1=Net-(C23-Pad1), 2=GND | C95 (9.1p): 1/1; C92 (9.1p): 1/1; C90 (9.1p): 1/1; C87 (9.1p): 1/1; C85 (8.2p): 1/1 |
| L9 | 82n | 1=Net-(C29-Pad2), 2=Net-(C30-Pad1) | No anchored candidate |
| L13 | 68n | 1=Net-(C23-Pad1), 2=Net-(U4-LO) | No anchored candidate |
| C20 | 6.8p | 1=Net-(C20-Pad1), 2=GND | C87 (9.1p): 2/2; C95 (9.1p): 1/2; C92 (9.1p): 1/2; C90 (9.1p): 1/2; C89 (1.6p): 1/2 |
| U1 | MCP6022 | 1=Net-(U1A--), 2=Net-(U1A--), 3=Net-(U1A-+), 4=GND, 5=Net-(U1B-+), 6=Net-(U1B--), 7=/RX_BASEBAND, 8=+3V3, 9=, 10= | U5 (MCP6022): 8/8 |
| C32 | 10p | 1=GND, 2=Net-(C30-Pad1) | C82 (100n): 1/1; C81 (8.2p): 1/1 |
| L2 | 15n | 1=Net-(C10-Pad2), 2=Net-(C11-Pad1) | No anchored candidate |
| L6 | 15n | 1=Net-(C20-Pad1), 2=Net-(C19-Pad1) | No anchored candidate |
| L11 | 82n | 1=GND, 2=Net-(C30-Pad1) | No anchored candidate |

## Schematic parts not linked by preserved UUID

C81 (8.2p), C87 (9.1p), C89 (1.6p), C92 (9.1p), C94 (3.9p), C98 (1.6p), C55 (3.9p), C56 (9.1p), C60 (1.6p), C64 (9.1p), C67 (3.9p), C75 (100n), C82 (100n), C85 (8.2p), C86 (3.9p), C90 (9.1p), C91 (1.6p), C95 (9.1p), C97 (3.9p), L12 (10n), L13 (10n), L18 (15n), L20 (10n), L22 (10n), Q4 (2SC3356), R33 (47k), U5 (MCP6022)

## Disposition by circuit role

- **U1 → U5: confirmed electrical role, replace footprint.** All eight connected pins match the native netlist using neighboring UUID matches. Existing Vault:SLAB-MSOP-10_N has ten pads; selected MCP6022-I/SN requires the audited SOIC-8 footprint. Do not retain old pad geometry.
- **C20 → C87 and C21 → C92: strong replacement candidates.** Both numbered pads match anchored signal/ground nets. Values change from 6.8p to 9.1p. Inspect actual placement and copper before accepting.
- **C19 → C94: output coupling candidate.** PCB output endpoint agrees with TX_OUT; upstream endpoint is supported by C21→C92. Value changes from 10p to 3.9p.
- **L6 → C89 and L2 → C98: topology changes, not reference repairs.** Old series inductors bridge the two resonator nodes; current schematic uses series coupling capacitors. Their neighboring preserved UUID components identify the sections. Replace with selected capacitor footprints and reroute as needed.
- **C29/C30/C31/C32/L9/L10/L11: old RX input filter section.** Old RX_IN entry and its connected resonator network identify this group. Current section is C55/C56/C60/C64/C67/L12/L13, with changed series/shunt topology. Replace as a reviewed block; no one-to-one pad-preserving relink is accepted.
- **C22/C23/C24/L12/L13: old mixer LO filter section.** The network terminates at old U4 LO (current U10.6). Current LO path adds Q4/L18/C85 and a revised filter C86/C90/C91/C95/C97/L20/L22. Rebuild this section against the schematic rather than relinking by reference.
- **TP1/TP2: board-only supply test points.** Connected to +3V3 and old /+5V respectively. Preserve pending explicit review of test access and the /+5V rail identity; no automatic deletion.
- **J5: old RX_IN coax connector with no current symbol.** Keep pending the antenna-switch design decision. Current RX_IN is a schematic boundary label, not an approved instruction to remove this connector.

All 21 unmatched footprints now have a circuit-role classification. Only U1 has a full eight-pin electrical match; the three capacitor candidates need placement/copper review. No board edits or deletions were applied. Full native connectivity remains required for update; the CLI discrepancy remains open.
