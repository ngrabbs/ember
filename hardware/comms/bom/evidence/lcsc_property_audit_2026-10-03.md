# Embedded LCSC property audit — October 3, 2026

The canonical property is **`LCSC Part #`**. Keep the verified C-number embedded
in every purchasable schematic symbol and synchronize it to the PCB. Include
this exact field in every BOM export. Do not rely on the older `LCSC` alias.
DNP and hand-solder assembly choices are separate from ordering identity.

153 exported placements: **147 purchasable placements with valid C-numbers**,
including J6/J7/J8 DNP, plus six bare PCB test pads marked `N/A`. Zero blank
fields, zero invalid purchasable codes, and zero schematic-to-PCB code mismatches.
Board-only mounting holes are fabrication geometry and have no purchased part.

## Changes

18 existing CAN-part codes were copied from `LCSC` to `LCSC Part #`:
C107–C114 C14663; R40–R45 C25804; U1/U4 C184944; Y3/Y4 C12710.
Their earlier October 3 identity/stock checks are recorded in the comms TODO.
The old alias was preserved for compatibility.

| References | New embedded code | Exact part | Live JLCPCB stock observed |
|---|---|---|---:|
| C8/C9 | C1711 | Samsung CL21B104KBCNNNC | 1,290,870 |
| R5/R6 | C17437 | UNI-ROYAL 0805W8F1200T5E | 1,649,249 |
| J6/J7/J8 (DNP) | C50981 | BOOMELE 2.54-1*20P straight male | 39,646 |
| JP1/JP2 (hand solder) | C86471 | TE Connectivity 826629-2 | 21,397 |

Sources: live JLCPCB search results on October 3 for
[C1711](https://jlcpcb.com/parts/componentSearch?searchTxt=C1711),
[C17437](https://jlcpcb.com/parts/componentSearch?searchTxt=C17437),
[C50981](https://jlcpcb.com/parts/componentSearch?searchTxt=C50981),
and [C86471](https://jlcpcb.com/parts/componentSearch?searchTxt=C86471).
Stock is not reserved. This pass checks newly assigned codes, not a fresh live
stock audit of every previously populated BOM line.

C8/C9 retain 100 nF / 0805, selected 50 V X7R ±10% for the CAN supplies.
R5/R6 retain 120 ohms / 0805; selected 1%, 125 mW. At 3 V differential,
P=V²/R=75 mW. This does not establish survival of continuous bus-to-supply faults.

Header drawings were downloaded through JLCPCB and visually inspected:
`datasheet/Header_C50981.pdf` shows 20 single-row 2.54 mm positions, 0.64 mm
square posts, 1.0 mm PCB holes, 2.50 mm housing, 5.7 mm mating posts and 3.0 mm
solder tails. `datasheet/Header_C86471.pdf`, TE drawing 826629 rev AA sheet 1,
shows 2.54 mm pitch, 0.63 mm square posts and 1.0±0.05 mm holes; 826629 has
2.8 mm housing, 6.7 mm mating posts and 3.2 mm tails. Existing PCB footprints
have the corresponding 20 or 2 pads and 1.0 mm drills. These unkeyed headers
have interchangeable physical contacts; logical pin numbering follows the
existing board labels and pad-1 mark. No pin remapping or footprint change.
JP1/JP2 codes identify the male headers only, not removable shunts; use matching
2.54 mm shunts only when termination is required. J6/J7/J8 remain DNP.

## Verification

Konnect edited the schematic with its editor closed. Native KiCad update preview
contained exactly 33 field updates and no other actions (zero warnings/errors).
Saved PCB property readback matches the exported BOM for every placement.
Fresh DRC: 0 errors, 0 unconnected, 1 existing H1/H2 silk overlap warning.
209-net native connectivity baseline still matches all PCB pad assignments.
No routing, net, footprint or DNP changes were requested.

The accompanying CSV is an **audit BOM**, including DNP/test features, not an
assembly-upload BOM. Final assembly output must omit DNP, bare test pads,
board-only mounting holes, Pico and hand-soldered headers, while retaining
these parts and ordering identities in the full project BOM.
