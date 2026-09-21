# Routing cleanup and receiver bias correction

[Verification index](README.md) · [Current work](../TODO.md)

> Dated checkpoint record. Intermediate counts and commit-status statements below
> apply to that pass; use the index and current work list for the latest consolidated status.

Saved-board DRC: **0 active errors, 120 warnings, 0 unconnected items**. The H3/H4 courtyard overlap is a single user-authorized exclusion preserving equal pin spacing; all other courtyard checks remain enabled. Routing rules were not relaxed. Native schematic ERC now reports zero errors, one local/global GND label warning, two previously excluded transistor warnings and four ignored tests. Native connectivity matches the PCB across all 181 nets with zero mismatches. This is not fabrication approval.

## Completed

- Restored U5 MCP6022 placement to the existing SOIC-8 routing and rebuilt its filter/gain connections.
- Corrected TX capacitor/choke/test-point placement and routing; restored C65, C80, C81 and L17 functions.
- Restored digital IRQ, MISO, CS, power-rail connections, D14 supply direction and LED resistor orientation.
- Removed obsolete TP1, TP2, L2, NC copper, an isolated +5 V stub, and the unused tripler via.
- Added receiver R38/R39, both 100k 0402 (C25741). R38 biases RX_IF from VREF_RX; R39 biases U5B input. C72 now bypasses VREF_RX, and R30 returns to VREF_RX rather than ground. C88 is placed at U5 power input.
- Added ground stitches for previously isolated component ground pours. All saved-board connections pass.
- Added pour-only setbacks around restored tripler/BPSK/CLK0 RF routes. All 705 sampled trace center/edge points have In1 ground underneath. This geometric check is not RF bench qualification.
- Preserved H3/H4 centers/orientation and J6/J7/J8/J9 locations. H3/H4 bodies remain on top; J6/J7/J8 remain DNP.

## Receiver calculations and limits

R28=R29=10k establishes an ideal 1.65 V midpoint from 3.3 V. Returning R30 to that same reference gives ideal DC output 1.65 V while retaining AC gain 1+100k/10k=11. The C69=100n/R39=100k coupling corner is approximately 15.9 Hz, assuming a low-impedance source and AC-grounded reference. C72=10u bypasses the reference; its ideal impedance is about 13.3 ohms at 1200 Hz.

The existing unity-gain, equal-R/equal-C Sallen–Key topology has Q=0.5, not the Q=0.707 claimed by the old schematic note. With R=22k and C=2.2n, ideal f0=3288.3 Hz and -3 dB frequency=2116.3 Hz. Ideal attenuation at 1200 Hz is -1.09 dB. These are analytical ideal-component results, not a new SPICE simulation or measured response. Component values were retained. The outdated schematic text and field placement still need native-editor cleanup, followed by native ERC and netlist parity.

Reference topology: TI TIPD185 (https://www.ti.com/tool/TIPD185), AC-coupled single-supply amplifier design.

## Accepted header courtyard exception

H3/H4 have 5.08 mm center spacing and 6.0 mm courtyard widths, producing 0.92 mm courtyard overlap. Samtec's drawing lists a nominal 0.195 inch / 4.95 mm double-row body width, giving only about 0.13 mm nominal separation. User explicitly accepted this overlap on 2026-09-09 to preserve equal pin spacing across the stack interface. KiCad stores one pair-specific exclusion with that rationale. Header positions and courtyard geometry remain unchanged. This records acceptance of the overlap; it is not evidence of a physical fit test. Drawing: https://suddendocs.samtec.com/prints/esq-1xx-xx-x-x-xxx-xx-x-xx-mkt.pdf .

Other DRC warnings: 51 silk overlaps, 51 silk-over-copper, 10 hole-to-hole, 6 small text, 2 isolated copper. These have not been waived by this pass.
