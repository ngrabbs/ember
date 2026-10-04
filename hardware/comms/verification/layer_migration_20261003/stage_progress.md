# Migration stage — R39 and two 5 V distribution sections

C69 repaired and visually inspected; CAN _P/_N label changes synchronized via native F8. R39 rotated 180 degrees, restoring physical pad alignment without moving its center. Saved DRC after each completed block: zero errors, zero unconnected items, one known H1/H2 silk warning.

CAN supply: 0.5 mm external route, 77.31 mm total tree length. With nominal 35 um copper and copper resistivity 1.724e-8 ohm m, conservative full-length resistance is 0.0762 ohm; at 140 mA (two transceivers) this is 10.7 mV drop, 1.49 mW copper dissipation. Actual shared-current length is smaller. This is a routing voltage-drop screen, not final thermal qualification.

Receiver-side supply: 0.4 mm, 42.66 mm total tree length; nominal full-length resistance 0.0525 ohm. At a conservative 200 mA branch screen, drop is 10.5 mV and dissipation 2.10 mW. Final complete rail budget remains pending.

The 24 original inner-layer segments for these two connected sections were removed only after their replacement routes passed DRC. Inner-layer +5V pours remain; overall plane independence has not yet been demonstrated. The TX section was subsequently completed as recorded below. The pours remain active until all plane-dependent loads are supplied from outer copper.

All previous manufacturing releases are stale for this migration. No new manufacturing release or vendor upload performed.

## Subsequent stage — TX supply, analog branches and local 3.3 V feeds

The last eight +5V inner traces were replaced by two bottom routes, 17.45 mm and 15.30 mm at 0.5 mm width. One joins the existing receiver-side branch. The 2.54 mm VBAT header link was also moved to bottom at its existing 0.4 mm width. No +5V, +3V0 or VBAT tracks remain on In2.Cu; its 22 remaining tracks are +3V3. Inner power pours are still active.

RX_BASEBAND and VREF_RX were routed on top, then their eight old bottom segments and five obsolete vias were removed. The native Edit > Delete action was needed for selected vias; Konnect delete_trace correctly refused via UUIDs. Final saved DRC confirms no dangling-via warnings. Baseband replacement length is 10.38 mm, and the VREF replacement tree totals 26.21 mm. RX_IF and ADC_VREF still require migration; the new reference routing needs final analog review.

Added 18 local +3V3 bottom connections: 46 segments, 143.88 mm total, width 0.5 mm. These retain existing supply vias and local component copper. Candidate paths of 27.94, 58.22, 91.73 and 97.42 mm were deliberately left unapplied pending crossing/placement optimization. Width and total-length values are routing evidence, not a completed rail thermal/drop qualification.

Read-only geometry analysis of pads, outer tracks/vias and actual filled outer power polygons now finds five +3V3 groups and three +5V groups with inner copper excluded. Before these local additions, +3V3 had 23 groups. See migration-power-islands.json for exact pad membership and via anchors. The analysis is a planning aid; final acceptance still requires removing the inner power copper, refilling, and authoritative KiCad DRC/netlist checks.

All completed stages passed saved/refilled DRC: zero errors, zero unconnected items, one existing H1/H2 silkscreen overlap warning. The stage plot was visually inspected for route geometry; it omits fills and is not an impedance/return-path signoff. No new manufacturing outputs or uploads.

## Subsequent stage — ADC reference and three power-feed joins

ADC_VREF now routes entirely on F.Cu, 26.18 mm at its original 0.254 mm width, replacing nine B.Cu segments totaling 34.65 mm. Candidate and final saved DRC passed.

R2 receives a new 0.6/0.3 mm +3V3 via at (150.4, 117.0), with a short 0.254 mm local top connection to its supply pad and 0.5 mm bottom connection to the existing distribution. This avoids a very long route around TX_ACTIVE. U1 pin 19 similarly gains a local 0.254 mm top escape to a new 0.6/0.3 mm +3V3 via at (133.9, 78.8), then 0.5 mm bottom copper to the pin-23 supply branch. Existing local decoupling paths are retained. Old inner-connected supply vias remain until the inner copper is removed and redundant stubs can be checked.

An 10.99 mm, 0.5 mm bottom route joins (127.2, 111.3436) to (134.082606, 119.889594), connecting the input/CAN 5 V supply and TX supply groups. Each mutation was refilled, saved and checked: zero errors/unconnected, only the known H1/H2 silk overlap warning.

The outer-copper analysis now finds THREE +3V3 groups and TWO +5V groups. Inner supply tracks and pours still remain. A subsequent planner found a 40.97 mm 5 V detour and a 114.38 mm 3.3 V detour; neither was applied. That candidate still failed to connect all 3.3 V groups. Attempted local TX_ACTIVE layer-transition and L17 supply-via alternatives did not meet the short-route/clearance constraints; no speculative copper was added for them. Remaining crossings need targeted placement/routing work.

RX_IF's direct top path crosses Net-(U10-RF), the mixer RF input. Do not move that crossing to the bottom and claim the analog-top migration complete. Resolve placement or route topology and preserve the RF impedance/reference contract.

## 3.3 V plane independence verified

Added a source escape at (128.4, 102.2): 1.15 mm local F.Cu trace and 29.49 mm B.Cu feed, both 0.5 mm wide, via 0.6/0.3 mm. This reaches the existing R2 supply node beyond the CAN and 5 V crossings. Added the receiver supply connection from (152.9138, 122.0182) to (171.3, 121.0), 28.05 mm at 0.5 mm width. This moderate detour was accepted after the long alternatives were rejected; it is power distribution rather than an RF signal route. Final rail current/drop and thermal qualification remains open.

The outer-copper analysis then found one connected +3V3 group. Removed all 22 remaining In2.Cu trace segments via Konnect. Selected the inner +3V3 zone (ff7f6adb-572a-4a7c-b0b8-dde081b723a0) through Konnect and removed it using KiCad's native context-menu Delete. Saved/refilled DRC proved zero errors/unconnected without that plane. Removed the five now-dangling source-array vias identified by DRC using native Delete after exact UUID selection. Final saved DRC: zero errors, zero unconnected items, one existing H1/H2 silk warning.

All inner signal/power tracks are now removed. The original In1.Cu GND plane remains. The In2.Cu +5V pour remains until the last join between its two outer-copper groups is resolved; no new In2.Cu GND pour has been added yet. Local L17/C82 feed alternatives failed the geometry screen and were not applied. An 86.92 mm board-edge candidate was also left unapplied; remaining topology needs refinement rather than treating a large detour as final. RX_IF/mixer crossing remains open.

## Inner GND conversion complete

Moving five auxiliary digital connections (GPIO0, GPIO1, GPIO13, GPIO22 and RUN_RESET) from B.Cu to F.Cu opened the last bottom power corridor. Candidate and post-removal DRC both passed. Their top route lengths are 5.87, 8.99, 68.28, 42.38 and 40.83 mm respectively. GPIO13 is longer than before and is an auxiliary GPIO route, not an RF/clock signal; final signal/return review remains open. No footprint positions, mechanical locations or artwork were changed.

Added the final +5V B.Cu feed from (174.2, 72.1) to (186.01, 117.699), 50.21 mm at 0.5 mm width. This replaces the 86.92 mm planning detour; no extra top power bridge was required. At nominal 35 um copper and resistivity 1.724e-8 ohm m, the new segment has approximately 0.0495 ohm resistance: 14.9 mV drop and 4.46 mW at a 300 mA screening current. This is not a complete rail budget or thermal qualification.

Removed the original inner +5V pour through exact Konnect selection and native Delete, then added GND on In2.Cu through Konnect. The new zone follows the existing In1.Cu ground outline, with 0.5 mm clearance, 0.25 mm minimum fill width and thermal pad connections. Removed six now-dangling +5V plane-feed vias.

Final saved/refilled DRC reports zero errors, zero unconnected items, and only the existing H1/H2 silk overlap warning. Read-only board verification proves zero trace segments and GND-only zones on BOTH inner copper layers. In1.Cu has one filled polygon; In2.Cu has a main polygon plus a small grounded pocket near the fixed headers (bbox x105.73–109.95, y96.21–102.38 mm). KiCad reports neither as an island. The layer verification includes the saved board SHA256.

RX_IF still crosses on B.Cu. No speculative RF edits were applied: route searches at the current component positions did not find a legal top route, including a longer path allowance. A narrower experimental route was only calculated and not applied; RX_IF retains its RF-class 0.358 mm width. Resolve component placement/port ordering while maintaining the RF netclass and reference rules. CAN pair review, final native ERC/parity, rail qualification and full-layer return-path review remain open. All old manufacturing exports remain stale.


## CAN A trunk cleanup and RX_IF placement investigation

Replaced seven CAN_A_N bottom segments to maintain the existing 0.65 mm center spacing through the paired trunk bends (0.20 mm traces, 0.45 mm edge gap). The old diagonal portions reduced perpendicular spacing. Endpoint fanouts remain separate review items. No additional vias, layer transitions, or length-tuning meanders were added. Readback geometry was plotted and inspected. Refilled/saved DRC: zero errors, zero unconnected items, one existing fixed H1/H2 silk-overlap warning. Both inner layers remain GND-only with zero traces.

Saved PCB SHA256: `bd32e126b11b3048ccfe1c3cc1b64597d62600bae315dc30e752d47a2bb2145d`.

Approximate copper-centerline endpoint lengths, including pad-center escapes and excluding via barrel lengths:

| Net | Controller to H1 | Layer transitions on header path | Controller to termination pad |
|---|---:|---:|---:|
| CAN_A_P | 83.0338 mm | 2 | 74.0972 mm |
| CAN_A_N | 77.6528 mm | 2 | 68.1991 mm |
| CAN_B_P | 125.8852 mm | 4 | 112.0362 mm |
| CAN_B_N | 122.7915 mm | 2 | 108.0159 mm |

These are endpoint path measurements rather than branched-net totals. They do not establish electrical skew, controlled differential impedance, or acceptable stub length. CAN B has a short bottom crossover near U4 while its other line remains on top; its fanout also conflicts with the local VIO supply escape. An offline attempt to tighten that fanout was rejected on clearance grounds and was not applied. Review topology/return paths before accepting or changing this crossover. Do not add vias or tuning solely to equalize these totals.

RX_IF: offline local C99 placement trials, including trials that rerouted the mixer RF input or removed a nearby ground strap/via, did not produce an acceptable top route. All were geometry-only; C99, U10, RF input and the existing bottom IF crossing remain unchanged. The next placement study must coordinate mixer port orientation and neighboring RF/LO/IF circuitry rather than forcing a narrower trace. The 0.358 mm RF-class width remains intact. RX_IF top migration is still open.

Evidence: `migration-can-a-bends-drc.json`, `migration-can-a-bends-plan.json`, `migration-can-a-bends.png`, `migration-can-endpoint-metrics.json`, `migration-layer-verification.json`. Manufacturing outputs and the JLC draft remain stale.

## Top-only IF bridge completed

C99 is now Samsung CL21B104KBCNNNC / C1711, 100 nF 50 V X7R, 0805, centered at (163.3, 127.4) mm and rotated 180 degrees. Its two pads bridge the mixer RF trace without a copper crossing. Mixer RF path is approximately 9.744 mm; R34-to-C99 IF path is 6.246 mm; C99-to-existing RX_IF node is 4.577 mm. New traces retain 0.358 mm width and the existing RF pad clearance. Both former IF signal vias and the bottom IF section are removed. Final saved/refilled DRC reports zero errors, zero unconnected items, and the existing H1/H2 silk warning. Native schematic sync also corrected U12 Manufacturer Part # to TLV73330PDBVR.

Power review identified inadequate worst-case voltage margin across D8 SS14. LM73100RPWR / C3210761 is prepared as a replacement with local input/output decoupling and controlled slew. The actual Power schematic is not changed yet: custom footprint acceptance is paused because Konnect refused a write to the separate disposable PCB with unsafe_file_fallback/kicad_lock_present. No write occurred; human editor recovery was requested per the PCB skill. Manufacturing exports remain stale.


## Protected input complete and refreshed quote candidate

- Saved/refilled DRC: 0 errors, 0 unconnected; one accepted fixed H1/H2 silk overlap warning. Native ERC: 0 errors, two known MCP25625 library mismatch warnings, four excluded tests.
- Native netlist parity: 213 nets, 572 logical ref.pin entries, zero mismatch.
- Both inner copper layers contain GND zones only, zero traces. Bottom contains only power/digital/CAN nets; all analog/RF/clock interconnects remain top.
- Outline: 24 edges with exactly coincident degree-two endpoints; direct DRC has no outline error.
- Gerber viewer: four copper layers, both mask/silk/paste layers and outline parsed and inspected. Drill inventory 456 PTH hits; no NPTH holes. No gross registration or artwork issue found.
- RF return screen: 20,570 samples, 190 misses confined to expected J9 signal PTH launch clearance; no non-ANT RF corridor gaps. This is a geometry screen, not EM certification.
- CAN_B 3.225mm crossover has only expected 0.8mm-radius endpoint antipads. Existing return stitches approximately 4mm away; accepted for prototype with CAN/EMC bench testing, without meanders or redundant matching vias.
- D8 replaced by U15 LM73100RPWR/C3210761, R46 and C116–C118. Correct RPW0010A land/paste geometry accepted through live scratch placement and native readback, then routed and verified on this board. DNC10 has solder lands only. Reference text moved clear of pads.
- 144 top-side assembly placements, matching BOM/CPL designators and embedded LCSC IDs. Live stock queries report stock for every assembly line; this is not a reservation or feeder-allowance check.

## Quote contract to confirm in JLCPCB preview

5 PCBs, 2 assembled; Pico and headers hand soldered. J9 through-hole MMCX is included in the assembly BOM and requires explicit assembly-process acceptance. H1/H2, J6/J7/J8, JP1/JP2, test points and mounting holes excluded from assembly. No separate customer stencil requested.

Requested construction: 4 layers, 1.6mm, JLC04161H-7628, outer 1oz/inner 0.5oz copper, ENIG, green mask/white silk. RF 50 ohm ±10%, F.Cu referenced to In1; nominal 0.358mm traces, 0.2104mm dielectric, 1.1mm coplanar ground gap. Confirm construction and tolerance with vendor; standard ±20% service does not meet this request. J9's five finished plated holes must be 0.84±0.05mm; confirm tolerance for this soldered connector. Source authority: JLCPCB capabilities and standard laminated structures pages, retrieved 2026-10-03; final order selections and CAM acceptance still pending.

Native CPL rotations are unchanged. Prior draft required clockwise90 corrections for U1/U4/U5/U10/U11/Y2 and 180 for U7/U8/U9/U12/U13/U14/Q3/Q4/Y1. Recheck these in the new preview; do not assume old portal corrections survived. U15 and resized C99 require fresh inspection. Remaining placeholder LED/D15 polarity and J9 process acceptance must be completed before order.

## Power and bench limits

Independent bounded review found no new prototype fabrication blocker. Known CAN and U8/U9 loads are ~312mA before Pico, tripler bias and auxiliaries. 0.5A is a screening load, not a proven maximum. At 35um copper, summing every +5V_CON/+5V branch gives a conservative 0.3155ohm tree bound; 0.5A causes 158mV before switch/contact/via/choke/temperature effects. LM73100 light-load maximum drop is about28.4mV. Static margin improves materially over SS14.

The provisional EPS minimum/ripple/transient limits, if stacked, give only4.55V before PCB loss and cannot guarantee the CAN/ADL5602 4.5V minimum. Measure minimum voltage at U1/U4 VDDA and U8 during startup, TX/RX changes and dual-CAN traffic; establish the real source envelope. Use a current-limited bench supply: LM73100 fast-trip is not a tailored 0.5A current limit. Verify power ramp/reverse feed, rail heating, CAN termination topology, max-bitrate error counters and RF/EMC performance. Prototype RF tuning/gain/spectrum/sensitivity remain hardware tests.

## Files

`transceiver-preview-gerbers.zip` contains only current Gerbers, job and drill files. `assembly-review/BOM.csv` and `CPL.csv` are the matching preview inputs. `manifest.json` records source/output hashes and sizes. Raw exports and evidence are retained for review. Do not order until vendor/CAM/placement checks close.

## Fresh vendor preview result — 20:12 local

JLCPCB draft `9a764d19c51247f089abcdbb2f6229cb` has current Gerber geometry and corrected BOM/CPL. All 144 placements matched and are selected, including all 20 C1525 decoupling capacitors (initially deselected by the portal; explicitly restored). The quote shows PCB $94.96 + assembly $227.28 = **$322.24**, before shipping/taxes/final checkout adjustments. Quantity: 5 PCBs, 2 assembled top side. No order/payment and no Save to Cart action performed.

Reapplied per-component CW90 corrections to U1/U4/U5/U10/U11/Y2; 180 corrections to U7/U8/U9/U12/U13/U14/Q3/Q4/Y1. C99 placement aligns with its new0805 pads. U15's displayed pin1 marker aligns with the PCB marker at upper-right, but its generic QFN rendering does not reproduce RPW0010A geometry: exact package/pin1/paste engineering approval remains required. Prior LED placeholder/polarity and J9 precision-hole/assembly-process approvals remain open; preview price is not fabrication acceptance. Production-file and parts-placement confirmation were enabled with automatic confirmation disabled. Assembly terms were already checked from the user's prior acceptance.

PCB remark requests J9's five0.84±0.05mm soldered MMCX holes and50ohm±10% top/In1 construction. The precision-hole option is only a quoted process request; the connector is not press-fit. Both unusual requirements need vendor CAM approval.

**Outcome: goal of a refreshed preliminary quote achieved. Manufacturing release remains INCOMPLETE pending vendor engineering/placement acceptance.** See `preview/jlc-quote.jpg`. Bare peer review: `~/Desktop/transceiver_review_20261003_2008.zip`. No backup directories included.
