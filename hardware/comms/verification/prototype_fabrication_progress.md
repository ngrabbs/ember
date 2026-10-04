# Prototype fabrication progress — October 3, 2026

[Open work](../TODO.md) · [Verification index](README.md)

**Not ready for fabrication.** Target: 5 PCBs, 2 assembled by JLCPCB; Pico and
headers hand soldered. Work is on `feature/transceiver-dual-can`, following the
schematic checkpoint `1fd327c`. This record describes the subsequent working tree.

## Completed

- Native KiCad schematic-to-PCB update: added U1/U4 MCP25625 and their support
  parts, removed obsolete U2/U3, and removed the malformed duplicate R38/R39
  footprints while retaining the valid instances. Native preview: no errors or warnings.
- Placed the two CAN circuits above the Pico. Twelve short local connections
  route controller VIO/VDD/VDDA bypassing, oscillator supplies, clocks and standby
  pull-ups. No local CAN clearance or courtyard violations were added.
- Native netlist parity: **208 nets, 544 schematic nodes, zero pad-assignment
  mismatches**, compared with 549 unique PCB reference/pad entries. This includes
  unnamed RF nets. See [machine-readable result](evidence/prototype_native_parity_2026-10-03.json).
  Routing continuity remains incomplete. Konnect's CLI export produced only 53
  named nets; it is insufficient for this check and its unsafe synchronization
  proposal was not applied.
- Restored four mounting holes using original Rev-A drill and copper data.
  All are locked, board-only, excluded from BOM and placement files, with 3.18 mm
  plated drills and 6.35 mm copper pads.

| Hole | X (mm) | Y (mm) |
|---|---:|---:|
| MH1 | 105.5936 | 67.5436 |
| MH2 | 191.3236 | 65.0036 |
| MH3 | 105.5936 | 141.2036 |
| MH4 | 191.3236 | 145.0136 |

## Current DRC and next work

After zone refill and the twelve local connections: **145 errors, 79 warnings**.
Of the errors, **122 are unconnected items**. The remaining 23 comprise six
clearance, six track-width, five courtyard, four shorting, one hole-clearance and
one solder-mask bridge findings. See [saved DRC](evidence/prototype_drc_2026-10-03.json).
Mechanical attributes were then saved; they do not change copper geometry.

1. Complete CAN power/ground, SPI, reset/interrupt and bus routing; remove obsolete
   transceiver copper without disturbing shared supplies or RF paths.
2. Fix the GND via at (139.7398, 116.2088) overlapping C65's signal pad/tracks.
   It accounts for the four shorting findings and one hole-clearance finding.
   Resolve the remaining clock/supply clearances, RF track widths and mask bridge.
3. Review mechanical findings. The accepted H1/H2 pin-spacing exception does not
   automatically waive mounting hardware clearance. Nominal 6.35 mm circular
   hardware leaves about 0.38 mm to the adjacent header body at MH1/MH3; actual
   fastener/washer dimensions and tolerances are still unconfirmed.
4. Close TX startup/inhibit behavior and power sequencing. Y2's MSOP-10 package
   has no OEB pin; constant BPSK data does not disable the carrier, and a Pico
   reset alone does not reset an already configured Si5351. Define and validate
   startup/reset behavior before release.
5. Verify exact stock/assembly eligibility for all populated parts, resolve L16
   and D15, verify J9 mechanical drawing, and record the chosen four-layer vendor
   stackup/thickness before exporting fresh Gerbers, drills, BOM and CPL.

## Parts and prototype test boundary

U9 can remain PSA4-5043+: JLCPCB C5240848 was verified October 3 with 1,923
orderable pieces, minimum one, and both Economic/Standard SMT assembly eligibility.
Availability must be checked again at ordering. No replacement RF amplifier was
introduced. [JLCPCB listing](https://jlcpcb.com/partdetail/C5240848).

L16's exact order code and acceptance of its 930 MHz typical self-resonance remain
open. D15's exact stocked part and RF voltage margin remain open. J9 requires its
actual mechanical drawing to confirm the selected board thickness and footprint.

RF gain, sensitivity, LO drive under load, antenna mismatch behavior, filter tuning,
TX spectrum and CAN/RF concurrency are measurements for the assembled prototype.
Provide probe/rework access now; these measurements are not possible before boards
exist. Keep the 9.1 pF filter baseline pending measurement. Old bench firmware is
not compatible with the new CAN pin map and must be ported before powered tests.

No fabrication package has been released, uploaded or ordered from this revision.

## Follow-up after checkpoint fdafe1d

Saved a comms-only Git checkpoint before further PCB changes; unrelated documentation
was left out. The checkpoint also preserves the saved R39 schematic placement change.

Moved the GND via `60c56541-8011-470b-bb67-66ca19f4b33b` from
(139.7398, 116.2088) to the existing C65 ground-trace endpoint
(139.5998, 118.0888). Refill and DRC confirm no remaining findings on that via;
the four shorting findings and hole-clearance finding are cleared, along with
the associated mask bridge and one missing ground connection.

Connected each CAN controller's pin 17 to its chip-select pull-up (U1–R40 and
U4–R43) with 0.25 mm top-layer traces. Fresh refill and DRC: **136 errors,
including 119 unconnected items, and 78 warnings**. The two routes added no
physical-rule findings. These follow-up changes are saved after the checkpoint.
See [follow-up DRC](evidence/prototype_drc_after_checkpoint_2026-10-03.json).

## CAN routing continuation after fdafe1d

Completed through live Konnect IPC, with saved zone refill and DRC after each group:

- Sixteen short ground connections and 0.6/0.3 mm vias for the controller ground
  pins, oscillators and bypass/reset capacitors. DRC confirms the ground islands
  connect into the existing ground system.
- Both TXD/controller-output loops, both RXD/controller-input loops, and local
  reset RC networks. TXD uses top copper; RXD crosses on bottom copper.
- Local 3.3 V supply branches, oscillator enable pins, pull-ups and shared local
  supply trunk. The connection from this trunk to the existing board supply is
  still open; neither CAN channel is ready to power.
- Shared MISO/MOSI/SCK bus to J6 pins 6/10/9; independent chip selects to J6
  pins 19/20, reset signals to pins 11/12, and standby to pins 4/5.

DRC at the end of that stage: **81 errors = 64 unconnected items + 17 physical errors;
78 warnings**. The 17 pre-existing physical errors and warning count are unchanged
by this continuation; missing connections decreased from 119 to 64. See the
[latest saved DRC](evidence/can_routing_progress_2026-10-03.json).

Remaining routing includes CANH/CANL, interrupts, board supply feeds and obsolete
copper removal. Full routing review, mechanical findings, startup behavior and
procurement checks remain release blockers. This pass is saved but uncommitted.


## CAN interrupt routing and obsolete copper cleanup

Both MCP25625 interrupt nets now connect to the Pico header. CAN_A_INTn uses a
front-layer route to J7.17; CAN_B_INTn transitions below the Pico header and
connects through the retained back-layer fanout to J7.16. The B transition via
was explicitly assigned to CAN_B_INTn with automatic net updating disabled;
J8.19 retained its original unconnected net.

Removed 43 obsolete chip-select/interrupt track segments and four obsolete vias
at the former CAN transceiver locations. Removed the unused trial interrupt via
as well. Trial routes that caused crossings were removed before verification.

After zone refill and save, DRC reports **78 errors: 62 unconnected items,
5 clearance errors, 6 track-width errors, and 5 courtyard errors; 72 warnings**.
No new physical finding identities appeared relative to the preceding saved
check. Cleanup removed one existing clearance error and six warnings.
Evidence: [saved DRC](evidence/can_interrupt_cleanup_2026-10-03.json).

Next routing work: CANH/CANL pairs, supply feeds, and remaining isolated power
and ground copper. This remains an unfinished PCB, not a fabrication release.


## CAN bus and supply routing — completed continuation

Routed CAN_A_H/L and CAN_B_H/L from the relocated controllers to the existing
header/termination wiring. Most of each bus run follows parallel tracks; these
are ordinary 0.2 mm routes under the existing Default rules, not a claim of
validated controlled impedance. CAN B transitions around the controller's
existing power connection.

Connected the shared CAN 3.3 V network to C59 and the 3.3 V header supply.
Connected both 5 V transceiver decoupling networks to C58 through a 0.5 mm
In2.Cu supply trunk. Connected the incoming 5V_CON header rail through C70/C68
and D8. Header escape sections use 0.25 mm tracks between the 1.8 mm pads;
other added supply tracks are 0.5 mm. Final current/drop/thermal acceptance
against the selected copper and stackup remains part of the fabrication contract.
No In1.Cu signal or supply tracks were added.

After refill and save: **66 errors = 50 unconnected items + 16 physical errors;
72 warnings**. The physical findings are the same five clearance, six width,
and five courtyard errors as before this pass. Exact physical finding identities
and all warning identities are unchanged. Missing connections fell from 62 to
50. There are no missing-connection entries involving a CAN net or U1/U4.
Front/back copper exports were visually inspected after routing.

[Saved DRC evidence](evidence/can_bus_supply_routing_2026-10-03.json).

Next: remaining power/ground islands and local RF/switch connections, followed
by clearance/width repairs and a fresh electrical and manufacturing review.
The board remains unsuitable for fabrication in its present state.


## Routing completion and physical copper corrections — October 3

Completed the remaining 50 missing connections through live Konnect routing and
native KiCad via-property edits. This includes local RF/switch links, ground
returns, 3.3 V and 5 V feeds, the 3.0 V switch supply, RX reference and TX_ACTIVE.
Power distribution uses In2.Cu; no signal or power tracks were added to In1.Cu.
Removed 19 obsolete isolated ground/3.3 V segments at the old CAN locations.
Moved the C65-area ground stitch to (140, 115.3) mm to clear the completed route.
Trial copper that introduced conflicts was removed before the final check.

Corrected four TRIPLER_OUT and two U9 input segments to the existing 0.358 mm RF
width. Necked two short U12 supply segments to 0.2 mm under the existing Default
rules. Adjusted two clock-route bends away from ground stitches; Y2's short CLK0
pin escape is 0.35 mm to satisfy both its pad clearance and RF minimum width.
This closes existing geometric rules; it does not establish vendor impedance
or supply current/thermal acceptance. The final clock-route copper export was
visually inspected.

After refill and save: **5 errors (all courtyard overlap), 0 unconnected items,
0 clearance errors, 0 track-width errors, and 49 warnings**. The five remaining
error identities were present before this continuation. Evidence:
[routing completion DRC](evidence/routing_completion_2026-10-03.json).

The remaining courtyard pairs are H1/H2, MH1/H1, MH1/H2, MH3/H1 and MH3/H2.
The user's intentional header pitch exception does not establish washer/standoff
clearance. Preserve fixed stack coordinates while verifying that envelope.
Warnings still require disposition, including dangling copper and silkscreen.

Before release: rerun RF ground-return checks with the new vias and completed
routing; confirm vendor stackup/impedance and supply sizing; resolve startup TX
inhibit; finish exact-part stock/footprint and connector mechanics checks; then
produce and inspect current Gerber/drill/BOM/CPL outputs. Zero unrouted items is
not fabrication approval. These changes are saved and uncommitted.


## Unused copper and warning cleanup — October 3

Removed 19 obsolete track segments: the unused J8.18/J8.19 routes, old CAN bus
stubs, and a dangling RX reference spur. Removed three one-layer 3.3 V vias and
one obsolete RX reference via with native KiCad selection and deletion. Live
Konnect refill/save/DRC after each pruning pass retained zero unconnected items.
Moved R41/R44 labels beside their resistors, R45 below its resistor, and Y3/Y4
labels below their oscillators. Fresh DRC clears all findings involving these
five references; the channel B copper/silkscreen export was visually inspected.

Saved result: **5 courtyard errors, 24 warnings, zero unconnected items, zero
clearance/track-width errors, and zero dangling-track/via warnings**. Evidence:
[warning cleanup DRC](evidence/warning_cleanup_2026-10-03.json).

Ten remaining warnings are same-net via-hole spacing in the 3.3 V and 5 V
clusters. Actual drill-edge gaps are 0.3001–0.5698 mm versus the project's
0.5995 mm rule. JLCPCB's [published rigid-board capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/)
(accessed October 3, 2026) specify 0.2 mm via-hole spacing and 0.45 mm pad-hole
spacing. These ten via pairs exceed the published via minimum. This is a scoped
manufacturability comparison, not a changed rule or a waiver of other drill/
copper constraints. The project rule and findings remain visible.

Mechanical inspection of the exported H2 fabrication outline gives the closest
body edge 3.555 mm from each adjacent MH1/MH3 center. A circular 6.35 mm hardware
envelope would have about 0.380 mm nominal body clearance; 7.11 mm would leave
none. This excludes tolerances and must be checked against the actual screw head,
washer, standoff envelope and socket body. Hardware dimensions requested from
user; no mechanical exception added and no stack hole moved. Existing H1/H2
pitch intent remains unchanged.

The four mounting-hole library mismatches were dry-run inspected only. Konnect
reports differences in pads, attributes and metadata, so no blanket refresh was
applied. Exact geometry and fabrication exclusions must be preserved when those
are reconciled. Remaining silkscreen and library warnings still need closure.
All changes are saved and uncommitted; no fabrication release has been exported.


## Fixed PC/104 interface and silkscreen closure — October 3

User confirmed that H1/H2 and the four mounting holes are fixed interface
locations. Recorded five individual native KiCad courtyard exclusions with
comments: MH1/H1, MH1/H2, MH3/H1, MH3/H2, H1/H2. These persist in the project;
courtyard checking remains enabled for other pairs. This resolves the placement
findings as intentional interface exceptions, not as permission to move the
holes or shrink physical bodies. Compatible mounting hardware remains a physical
assembly requirement; hardware dimensions are not a prerequisite to preserving
these specified coordinates.

Updated the mounting-hole library through Konnect: board-only, excluded from BOM
and position exports, with its unnecessary square silkscreen outline and dot
removed. Refreshed the four placed holes through the reviewed atomic library
update. Drill remains 3.18 mm plated, copper remains 6.35 mm. Exact normalized
before/after PTH drill, NPTH drill, top copper and Edge.Cuts exports are identical
(excluding generation timestamps). See [geometry comparison](evidence/mechanical_geometry_comparison_2026-10-03.json).
These limited scratch exports were verification artifacts, not a release package.

Moved MH1/MH2/MH3/MH4, H2 and C107 reference text to clear copper. Visual review
caught H2 text in the edge notch; it was moved to (101.8636, 80) mm within the
upper board edge. No component or hole position changed. Mounting-hole library
mismatch checks now pass in the saved-board DRC. Native editor library caches
may need refresh if they retain old library comparison results.

Final saved [DRC](evidence/mechanical_cleanup_2026-10-03.json): **0 errors,
0 unconnected items, 11 warnings** with the five courtyard exclusions applied.
The warnings are the ten documented via-hole spacings and one overlapping
H1/H2 silkscreen outline from fixed adjacent bodies; neither changes electrical
connectivity. There are no clipped silkscreen, dangling copper, clearance,
track-width or saved-board library mismatch findings. Five pre-existing ignored
tests remain; this pass did not disable any additional test.

Remaining work is final RF return-path review, startup/TX inhibit and power
acceptance, vendor stackup/impedance contract, exact parts/stock and fabrication
output inspection. Saved and uncommitted; no fabrication release or order.

## RF return-path cleanup — current saved board

Moved the +5 V via from (143.873726, 122.033474) to (144.6, 121.5),
the TX_ACTIVE via from (143.5136, 133.0036) to (144.0, 131.8), and the
+3V0 switch-supply via from (133.8, 133.6) to (134.05, 133.6). Updated their
connected tracks and refilled zones. The +5 V inner-layer feed retains its
previous approach with a short final segment to avoid adjacent +3V3 routing.
No component, header or mounting-hole placement changed.

Fresh saved-board DRC: **0 non-excluded errors, 0 unconnected items, 11 warnings**,
with the existing exclusions and warning dispositions unchanged.
[DRC evidence](evidence/rf_return_cleanup_drc_2026-10-03.json).

The exported In1.Cu filled ground-plane polygon was rasterized at 0.01 mm/pixel.
RF centerlines and a +/-0.6312 mm corridor were sampled at no more than 0.1 mm
along each segment and 0.0789 mm across it. Of 20,587 samples, the 189 without
ground are confined to the expected J9 antenna signal PTH launch. TRIPLER_OUT,
RX_IN and TX_OUT now have zero uncovered samples, including corridor edges.
[Screen evidence and saved-board hash](evidence/rf_return_screen_2026-10-03.json).

This conservative geometric screen excludes via/pad primitives and uses the
filled-plane polygon alone. It is not an EM extraction, impedance guarantee, or
substitute for confirming the actual vendor dielectric/copper stackup. The
antenna connector launch still needs its mechanical/stackup review.

Next electrical decision remains TX inhibition during startup and Pico reset;
then exact orderable parts, J9 mechanics and the fabrication stackup contract.
No fabrication package was released or uploaded.


## Hardware TX mute implemented — October 3

Added U14 SN74LVC1G08DBVR (C7666) and C115 100 nF 0402 (C1525).
U14 gates the U7 carrier with existing TX_ACTIVE before C73; R35 holds the
inactive state low. CLK1 and receive circuitry remain independent. U7 and local
clock/I²C/supply routing were adjusted to fit the gate. H1/H2 and MH1–MH4
placements match their saved pre-change values.

Native ERC: **0 errors, 2 existing warnings**. Saved PCB DRC: **0 errors,
0 unconnected, 11 existing warnings**. Native parity: **209 nets, 551 nodes,
556 PCB pad-map entries, zero mismatches**. RF plane screen remains 20,587
samples with 189 misses only at the existing antenna PTH opening.
[Validation](evidence/tx_hardware_mute_validation_2026-10-03.json) and
[implementation / remaining firmware and bench checks](tx_startup_inhibit_review.md).

Firmware sequencing is unchanged. The gate truth table does not guarantee
145.667 MHz waveform quality or RF isolation; verify both on the prototype,
along with reset/watchdog behavior. Vendor stackup, exact remaining part choices,
J9 mechanics and fabrication output inspection remain open. No release package
or order was generated.


## Restored power plane and routing cleanup — October 3

Preserved the user's restored +3V3 zone on In2.Cu (display name Layer 2).
Restored the five specific fixed PC/104 courtyard exclusions with comments.
No footprint, header or mounting-hole placement was changed during this pass.

Corrected three 0.20 mm CLK0_OUT segments to the established 0.358 mm width;
rerouted the test-point branch around C115 and R3 to maintain clearance.
Removed 26 redundant outer-layer power segments totaling 193.19 mm:
CAN +3V3 distribution on B.Cu, the long top-layer +3V3 feed, and local redundant
+3V3/+5V bottom links. Existing via connections now use the filled inner power
planes. Local component/decoupling connections remain. Re-spaced four +3V3
stitching vias into a 0.95 mm column pitch to clear the remaining hole-spacing
warnings, retaining 0.6 mm pads and 0.3 mm drills.

Fresh refilled saved-board DRC: **0 errors, 0 unconnected items, 1 warning**
(intentional fixed H1/H2 silkscreen-outline overlap). Native netlist parity:
209 nets, 556 PCB pad entries, zero mismatches. No schematic edits in this pass.
[Evidence](evidence/power_plane_cleanup_2026-10-03.json).

The native GUI initially retained four mounting-hole library-comparison warnings
that do not occur in a fresh saved-board check; these were not globally ignored.
Prior RF corridor screen results predate the user's latest board edits. This
focused cleanup does not repeat RF/impedance qualification or close fabrication
gates. Saved, not committed; the previously created review ZIP is unchanged.


## Top-ground stitching and RF review — October 3

Added 100 ground ties; corrected top-pour priority, clearance and thermal
connections. Saved DRC is 0 errors / 0 unconnected / 1 warning; native net
parity has zero mismatches. Main UHF RF widths match the 0.358 mm design target,
but a fresh vendor solver result, clock/reference transitions, and a +5V-via
antipad at the TRIPLER_OUT corridor edge remain open. See the
[complete review](ground_stitching_rf_review.md). No fabrication release.


## RF return cleanup and vendor width — October 3, 2026

TRIPLER_OUT's C93/C81/test-point branch now clears the power-via return
corridor without moving that via or TP3. CLK0 is entirely on top; removed its
two transition vias and moved C2 0.10 mm east for clearance. JLCPCB's live
7628 calculation returned 14.12 mil for 50 ohms, agreeing with the 0.358 mm
route width. Saved DRC: 0 errors, 0 unconnected, one fixed H1/H2 silk warning.
All 100 added GND vias still contact F.Cu/In1.Cu/B.Cu, and schematic pad parity
has zero mismatches. Main RF corridor screen leaves only the J9 signal launch.
The clock centerline is covered; local corridor-edge discontinuities near
R3/I2C_SDA remain documented. Fabrication tolerance and launch/matching review
remain open. No fabrication outputs or refreshed ZIP were generated.

[Detailed review](ground_stitching_rf_review.md) ·
[Evidence](evidence/rf_return_cleanup_2026-10-03.json).


## J9 drawing and order requirements — October 3, 2026

Retrieved Molex SD-73415-147 C5 from LCSC and verified J9's 0.84 mm holes
and 2.54 mm ground pattern. Lead reach is sufficient for nominal 1.6 mm PCB;
stack/cable envelope remains to be confirmed. Live JLC C588477 showed 7,018
available order quantity and wave-solder service. Ordering fields remain to be
entered. Documented 50-ohm ±10% as the proposed requirement, explicitly distinct
from JLC's currently described free ±20% testing. Classified RX_IF as baseband
downstream of C99/R34, rather than a 435 MHz line-width issue. No design edits
or new DRC run in this evidence-only pass.

[Review and proposed specification](j9_launch_and_fabrication_requirements.md).

User subsequently confirmed 16 mm standoffs and ample connector/cable room.
J9 stack clearance is accepted from that confirmation; no CAD mating-envelope
measurement was performed.

Clarification: this is the top board in the stack, with no board above it.
The user confirms the installed MMCX connector already clears perfectly with
ample room. J9 connector clearance is closed; do not reopen an overhead-board
clearance check for this configuration.

## October 3 exact RF parts completion

L16, D15 and J9 ordering fields are synchronized and saved in schematic/PCB.
[Part disposition](components/prototype_parts_2026-10-03.md) records live stock,
package mapping, prototype exceptions and D15 operating envelope. Fresh DRC
remains 0 errors / 0 unconnected / 1 fixed-header silk warning; native pad-net
parity remains clean. No release files generated or order placed.
