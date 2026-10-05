# Independent saved-design review — October 4, 2026

Verdict: **NEEDS ATTENTION for order release; no confirmed electrical fabrication blocker in the completed checks.** The electrical review has full eight-sheet coverage. Exact schematic/PCB pin identity does not pass: R39's terminals were interchanged during schematic redraw. Their electrical equivalence is explicitly proven below, rather than reporting an exact parity pass. Vendor availability, CAM acceptance, and final artwork inspection belong to the release owner's remaining review.

## Current evidence

- Saved PCB hash: `e969c80d28f62171bb6eb9b52046d4ef295c5c81170a37aa8faf685d421b0742`. All source hashes are in `source-hashes.json`.
- Fresh native ERC (`../../releases/review_20261004_1100/evidence/native-erc.rpt`): zero errors, two intentional U1/U4 library-copy mismatch warnings. Four disabled tests are recorded: global label used once, four-way junction, SPICE model issue, footprint filter mismatch. This is not a claim that all possible ERC tests are enabled.
- Fresh DRC within `aggregate.json`: zero errors, zero unconnected items, one known H1/H2 silkscreen proximity warning. Fixed PC/104 connector and mounting geometry stays as the user requires.
- Aggregate coverage: eight schematic files/instances, 287 resolved symbol instances, zero unresolved symbols, no failed audits or coverage diagnostics. PCB: 161 footprints, 591 physical pads. `manufacturing.json` reports READY within that tool's limited DRC/DFM contract; it does not certify stock, impedance, placement orientation, or vendor CAM.
- All eight direct short checks and orphan checks return zero. Single-pin findings are per-sheet global-label/local-label heuristics and are superseded by full native connectivity comparison.

## Explicit connectivity reconciliation

Native netlist has 213 nets and 567 electrical logical pin entries. The PCB has 572 logical pad identities and 591 physical pads; extra non-electrical/mounting pads and duplicate physical pad numbers account for the inventory difference. Every electrical PCB logical pad is represented in the native netlist.

`native-parity.json` records two exact-net discrepancies: native R39.1 is on the VREF node and R39.2 on the U5.5/C69.1 input node; PCB numbering is reversed. Both current inventories specify R39 as a nonpolar 100k resistor. **The resistor connects the same two electrical nodes.** `electrical-parity-r39-permuted.json` interchanges only R39's two terminals and obtains zero mismatches. This is an explicit passive-terminal equivalence, not a hidden waiver or an exact identity pass. Before a future Update PCB from Schematic, reconcile this terminal orientation to prevent needless net reassignment/unconnected indications.

U15's duplicate DNC pad 10 copper pieces carry two separate `unconnected-...` names. Both remain isolated and connect only the same logical DNC terminal; the comparison checks that neither joins a functional net. Multi-pad numbering was not silently collapsed.

RX sanity: C69.1/U5.5/R39's input-side terminal share RX_AMP_IN; R28/R29 form the bias divider, C72 bypasses it, and R30/R32 provide feedback. CAN A/B have shared SPI with separate CS/IRQ/reset/standby, 3.3V logic and 5V transceiver supplies. U14 hardware mute input and RF-switch control share TX_ACTIVE with its pull-down; current pad inventory preserves these connections.

## Layout and ground evidence

`traces.json` contains 1,020 track segments: 836 top and 184 bottom, zero inner-layer tracks. Bottom inventory contains power, digital, and CAN signals only. Analog, RF, clock, and ADC/reference signal routes remain on top.

The exported inner Gerbers contain only GND fill regions and no nonregion drawn traces: one region on physical layer 2, two on physical layer 3. Other net attributes on those layers correspond to isolated plated-hole/via annuli, not power planes. See `inner-gerber-net-audit.json`. This confirms ground-only planes, while the release owner performs the rendered fill/return-path inspection.

Principal top routes retain 0.358mm width: CLK0_OUT 9.761mm, CLK1_OUT 6.240mm, ANT 4.996mm, RX_IN 11.478mm, TX_OUT 9.984mm, RX_IF 9.438mm. Totals are trace lengths, not EM simulation or electrical-delay certification. Source escapes may be narrower. Vendor confirmation of the selected stackup and 50ohm tolerance remains necessary.

Current basic constraints: 0.15mm minimum clearance, 0.20mm trace width, 0.60mm via diameter / 0.30mm drill. No new copper clearance or courtyard violation is reported. The C65/R25 0.99mm center-distance heuristic is not itself an assembly collision; native DRC provides the stronger geometry evidence.

## Heuristic findings and remaining limits

The aggregate's sole error, missing decoupling on `3V3_IND`, is a classification false positive: that net drives D11 from Pico header J6.16 and is an LED control signal, not an IC supply rail. Per-sheet missing-bulk findings on +3V3/+5V overlook global C59/C58 47uF capacitors on Power and C79 10uF on RX. Generic >=10uF and dedicated-testpoint suggestions do not by themselves establish a defect in the +3V0 regulator branch or protected input. Existing local bypass parts remain present; no blanket capacitor additions were made.

Konnect's CLI ERC again produced implausible root-only dangling-wire results and wrong coordinates. That result is retained as `cli-erc.json` and explicitly rejected as the release authority in favor of fresh editor-native ERC and full native-netlist/IPC-pad comparison. No CLI-only pass is claimed.

No current parts-stock assurance comes from this audit. The release owner must check the new BOM/CPL and current JLCPCB preview, including mixer availability, U15 package/pin1/paste, LED orientation, J9 plated-hole acceptance, and impedance construction. Known bench qualification remains source-voltage margin under CAN/RF load, startup/reverse-feed behavior, thermal behavior, CAN traffic/termination, and RF gain/filter/spectrum/receiver performance. A DRC pass does not establish measured radio performance.
