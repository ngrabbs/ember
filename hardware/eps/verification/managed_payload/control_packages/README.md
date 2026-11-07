# Stock control and protection contact verification

2026-10-24. Six selected parts were checked against their manufacturer pin
maps, then placed in a disposable schematic/board through Konnect. No real
EPS circuit, PCB, library or project setting was changed. `verify.py` preserves
all227 prior native files and permits exactly the three new fixture sources.

| Fixture | Proposed EPS ref | Exact part | Development footprint |
| --- | --- | --- | --- |
| U1 | U1400 | TPS26630RGER | Stock RGE24/EP2.7, **without** embedded vias |
| U2 | U1411 | SN74HCS08PWR | Stock TSSOP14, full7.70×5.90mm reservation |
| U3 | U1412 | 74HC74PW,118 | Same TSSOP14 reservation |
| U4 | U1413 | SN74LVC2G08DCUR | Stock VSSOP8,4.56×2.90mm reservation |
| U5 | U1414 | SN74LVC1G32DBVR | Stock SOT23-5 hand lands,4.76×4.05mm reservation |
| D1 | D1400 | BAS116H,115 | Stock SOD123F, cathode1 left/anode2 right |

The prior [TPS3839 supervisor](../../controller_rev_b/swd_interface_candidate/README.md)
and [SN74LVC1G14 inverter](../../controller_rev_b/can_branch_parts/README.md)
exact-part maps remain applicable. TPS3700 construction approval remains
outstanding; it is not replaced by a fake interface or included in this fixture.

Electrical/structural evidence: all68 physical leads,72 raw pad objects,
14 placed symbol units and six complete sourcing records are checked.
`physical_map.csv` joins each manufacturer function to its actual symbol pin,
type and pad geometry. CLI XML has68 unique endpoints and65 nets. Three
intentional eFuse stacks join IN1/2, OUT17/18 and GND8/EP25; six hidden NC
contacts remain represented in XML. No schematic wires or fake NC markers were
added. The deliberately unwired fixture reports97 ERC errors:59 unconnected,
27 undriven inputs and11 undriven power inputs, with zero warnings. Generic
fixture ignored-check defaults remain recorded; this is not a clean circuit.

The symbol uses LS08 **functional geometry**, with the actual HCS identity,
description, source and visible Schmitt-input warning. No LS/HC substitution
is allowed. PGOOD16 retains its stock generic output type despite the actual
open-drain function. These limitations are explicit, not hidden by ERC changes.

The eFuse default thermal-via footprint has nine0.20mm drills below the
configured0.30mm minimum. Its selected stock no-via alternative has25 numbered
pads and four blank paste-only windows, with no holes. This leaves PCB thermal
vias to be designed separately. Stock peripheral lands differ from TI's
example, and the rounded exposed-pad paste apertures cover62.25% versus TI's
78% example. Assembly, stencil/voiding, thermal and SOA acceptance remain open.
Full placement rectangles supplement notched stock courtyards for worst
body/flash clearances; they do not modify the libraries.

Actual visual inspection was independent: every final schematic page/detail,
all six numbered board views, combined board, individual layer strips and
close eFuse paste/mask views were opened. Overlays are query-derived, not
native artwork. Initial review caught label collisions and a title-block
intrusion; both were corrected. Board Values still show overlapping generic
package identifiers, so the board is a contact fixture, not an assembly drawing.

The field repair used an **existing local Konnect MCP build**, through its real
stdio server and discovered `set_schematic_field_presentation` tool. Read-only
discovery, binary hash, exact schema, dry-run/apply responses, before/after
presentation items and CLI graph are retained. All metadata, pins, UUIDs,
instances and connectivity are preserved; only field presentation changed
after the separate OR placement fix. No source patch, native text write,
installation or client configuration change was needed. The cached connection's
older capability limits remain historical evidence; this new route verifies
position/visibility edits, not every untested presentation feature.

Sources: [TPS2663 SLVSE94G](https://www.ti.com/lit/ds/symlink/tps2663.pdf),
[HCS08 SCLS778D](https://www.ti.com/lit/ds/symlink/sn74hcs08.pdf),
[HC74 Rev9](https://assets.nexperia.com/documents/data-sheet/74HC_HCT74.pdf),
[2G08 SCES198N](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf),
[1G32 SCES219W](https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf),
[BAS116H Rev3](https://assets.nexperia.com/documents/data-sheet/BAS116H.pdf).
TI local PDF hashes and inspected pages are recorded; Nexperia PDFs returned403
to the direct downloader but rendered successfully in Chrome. Actual browser
page screenshots establish the inspected pin/mechanical drawings. Package
mapping does not establish circuit timing, brownout, reverse blocking, fault
cutoff, MOSFET survival or hardware/flight qualification.
