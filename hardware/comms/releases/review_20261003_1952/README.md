# Current prototype quote candidate — 2026-10-03

Saved PCB SHA256: `30d1469b495c8cda3262c838be33fb9905050b31d02af1e93c481a076289a4c2`.

**Status: INCOMPLETE for production release; ready for the explicitly authorized preliminary vendor preview.** No order or payment is authorized. Prior quote packages are stale.

## Design evidence

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

## Final ordering-field correction

R26/R31 were 1k in the circuit but referenced C1152 (24k). Both schematic and PCB now embed stocked C11702 / 0402WGF1001TCE, 1k 1%, 0402. Corrected BOM exported through Konnect and reconciled against raw export. Native F8 preview changed only ordering fields and unit metadata; circuit/placement unchanged. Final board SHA256 `359b1a6b2e30d2f247964847e0e8a8f3fe3b1607eda6f39b96136c3928d8a7ba`. Fresh final-Gerbers export matches uploaded Gerber/drill geometry exactly after excluding generation timestamps; no repeat upload is needed. `raw/bom-corrected.csv` supersedes raw/bom.csv. DRC rerun: 0 errors/unconnected, same H1/H2 silk warning. Native ERC/netlist results remain applicable to unchanged electrical connectivity. New JLCPCB draft: https://cart.jlcpcb.com/smt-order/?pcbFileNo=9a764d19c51247f089abcdbb2f6229cb .

## Fresh vendor preview result — 20:12 local

JLCPCB draft `9a764d19c51247f089abcdbb2f6229cb` has current Gerber geometry and corrected BOM/CPL. All 144 placements matched and are selected, including all 20 C1525 decoupling capacitors (initially deselected by the portal; explicitly restored). The quote shows PCB $94.96 + assembly $227.28 = **$322.24**, before shipping/taxes/final checkout adjustments. Quantity: 5 PCBs, 2 assembled top side. No order/payment and no Save to Cart action performed.

Reapplied per-component CW90 corrections to U1/U4/U5/U10/U11/Y2; 180 corrections to U7/U8/U9/U12/U13/U14/Q3/Q4/Y1. C99 placement aligns with its new0805 pads. U15's displayed pin1 marker aligns with the PCB marker at upper-right, but its generic QFN rendering does not reproduce RPW0010A geometry: exact package/pin1/paste engineering approval remains required. Prior LED placeholder/polarity and J9 precision-hole/assembly-process approvals remain open; preview price is not fabrication acceptance. Production-file and parts-placement confirmation were enabled with automatic confirmation disabled. Assembly terms were already checked from the user's prior acceptance.

PCB remark requests J9's five0.84±0.05mm soldered MMCX holes and50ohm±10% top/In1 construction. The precision-hole option is only a quoted process request; the connector is not press-fit. Both unusual requirements need vendor CAM approval.

**Outcome: goal of a refreshed preliminary quote achieved. Manufacturing release remains INCOMPLETE pending vendor engineering/placement acceptance.** See `preview/jlc-quote.jpg`. Bare peer review: `~/Desktop/transceiver_review_20261003_2008.zip`. No backup directories included.
