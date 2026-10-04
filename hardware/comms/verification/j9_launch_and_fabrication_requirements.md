# J9 connector, RF exceptions and fabrication requirements

Reviewed October 3, 2026. Scope: connector footprint/grounding, the remaining
clock/IF route exceptions, and a proposed fabrication specification. This is not
a complete manufacturing release or an accepted vendor order.

## J9 mechanical and sourcing evidence

The manufacturer drawing **SD-73415-147, revision C5, sheet 1**, dated August 31,
2021, was obtained from [LCSC's manufacturer PDF](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2407081140_MOLEX-734151471_C588477.pdf).
[Preserved drawing](../datasheet/Molex_734151471_SD-73415-147_C5.pdf).

| Item | Drawing | Saved PCB | Finding |
|---|---|---|---|
| Signal and four ground holes | Diameter 0.84 ±0.05 mm | 0.84 mm nominal | Nominal match; require finished-hole tolerance in fabrication |
| Ground-hole square | 2.54 mm, centers ±1.27 mm from signal | 2.54 mm; offsets ±1.27 mm | Match |
| Copper pad diameter | No pad diameter specified on sheet 1 | 1.24 mm | Nominal annular ring 0.20 mm |
| Body height above mounting face | 4.42 ±0.13 mm | Vertical footprint | Reserve at least 4.55 mm plus mating-cable envelope |
| Ground lead length | 3.02 ±0.13 mm | Planned 1.6 mm PCB | Nominal protrusion 1.42 mm |
| Signal lead length | 2.91 ±0.13 mm | Planned 1.6 mm PCB | Nominal protrusion 1.31 mm |

With an assumed board thickness range 1.44–1.76 mm, ground protrusion is
1.13–1.71 mm and signal protrusion 1.02–1.60 mm, before solder fillets. Thus the
older catalogue's 2.4 mm recommended board thickness does not imply insufficient
lead length on this 1.6 mm board. It does not establish mechanical retention or
stack fit by itself. The user confirmed on October 3 that this is the top board in the stack,
with no board above it, and the installed MMCX connector already clears
perfectly with ample room. The stack uses 16 mm standoffs. Connector clearance
is closed based on the user's physical fit confirmation; no CAD envelope
measurement is needed to keep this as an open issue. Support cable loads during testing. Do not change board thickness to
2.4 mm merely to match that catalogue recommendation; that changes RF stackup.

The live [JLCPCB C588477 page](https://jlcpcb.com/partdetail/MOLEX-734151471/C588477)
identified MOLEX 734151471, Plugin, Extended, wave soldering, Economic and
Standard assembly. Observed stock: 7,269; **available order quantity: 7,018**;
minimum 1. This exceeds the two-board assembly requirement, but is not a
reservation. Recheck in the actual order. JLCPCB states parts purchased into its
assembly library cannot be shipped separately. J9's ordering fields are now embedded in the schematic and PCB and included
in the current review BOM.

## J9 RF launch

Live pad query confirms center pin ANT and all four surrounding pins GND.
Read-only saved geometry verifies all four plated ground pads have surrounding
filled In1 and B.Cu ground at every one of 16 test directions, 0.65 mm from each
pad center. Top-pour contact is less extensive because of the local clearances;
the plated ground pins provide the direct vertical reference connections.
No additional via fence inside the connector footprint is justified by this check.

The ground clearance around the signal PTH is intentional, not missing GND to be
filled. Retain the manufacturer's nominal hole pattern. The 0.358 mm ANT route
is a microstrip until it reaches the larger pad/barrel; that launch is not a
uniform 50-ohm line. At 435 MHz the nominal 1.6 mm board traversal is only about
1.7 degrees even using Er=4.4 for a rough propagation-length estimate, but this
alone does not bound its lumped capacitance/inductance or return loss. Retain it
for the prototype and measure the connector/launch contribution with an
appropriate VNA fixture or de-embedded measurement. No claimed S11 acceptance.

## Remaining clock and IF sections

- CLK0 is now entirely on F.Cu over In1 GND. Its centerline is covered; the
  previously recorded outer-corridor misses near R3/I2C_SDA remain a local
  discontinuity. R3 is an existing 0-ohm series position for waveform tuning.
  Do not install a 50-ohm shunt load on the CMOS output. Establish drive strength,
  loaded waveform and overshoot during bring-up before selecting damping.
- Short CLK1 and U14 pad escapes are not uniform microstrip geometries. Retain
  the current connectivity and validate loaded clock/gate waveforms; changing
  every small pad escape to 0.358 mm is not by itself impedance qualification.
- Native netlist: U10 IF pin 2 and R34 pin 1 share Net-(U10-IF); R34=51 ohms
  returns to GND. C99=100 nF AC-couples that node to RX_IF. RX_IF then feeds
  R20=22 kohms, the R38=100 kohms bias path, and TP5. The documented receive
  architecture uses baseband filtering (about 2.12 kHz ideal -3 dB bandwidth).
  Its 10.353 mm bottom segment is therefore not a 435 MHz transmission-line
  matching requirement. Retain it; check noise pickup and mixer-product rejection
  on the prototype. Firmware LO offset must keep the wanted signal in the actual
  baseband passband. This does not independently qualify mixer termination at
  unwanted RF/sum frequencies.

## Proposed fabrication specification

This is an engineering requirement, not a placed order. The order preview and
vendor acceptance must agree before release.

| Parameter | Required or proposed selection |
|---|---|
| Quantity | 5 bare PCBs, 2 assembled, user selected |
| Laminate | JLC04161H-7628; four-layer FR-4; no silent stackup substitution |
| Nominal thickness | 1.6 mm; calculator labels stackup 1.59 mm ±10% |
| Copper | Outer 1 oz, inner 0.5 oz |
| Layers | F.Cu signals/GND, In1.Cu reference GND, In2.Cu power, B.Cu signals/GND |
| Top reference spacing | 0.2104 mm finished prepreg to In1 |
| RF line request | 50 ohms ±10% (45–55 ohms), F.Cu referenced to In1 |
| Nominal RF width | 0.358 mm; vendor calculation 14.12 mil = 0.358648 mm |
| Top coplanar ground | Existing 1.1 mm zone clearance; preserve layout geometry |
| J9 finished holes | 0.84 ±0.05 mm per connector drawing; vendor confirmation required |
| Finish / mask | Proposed ENIG / green; not yet selected in order |
| Assembly | Top-side SMT plus J9 wave-solder service if accepted; verify full placement inventory |
| Hand assembly / DNP | Pico and headers hand soldered; J6/J7/J8 remain DNP |
| Stencil | No separate customer stencil assumed; confirm service handling |
| Panelization | Vendor process requirement pending actual order preview |

[JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) lists
±10% impedance tolerance. Its [stackup guide](https://jlcpcb.com/help/article/multi-layer-pcb-standard-laminated-structures),
updated September 9, 2026, instead describes free testing at ±20% and chargeable
precision testing. Do not equate free testing with our ±10% requirement. Select
and obtain confirmation of the appropriate service; prices and service tier are
not accepted here. Sources retrieved October 3, 2026.

The saved core Er is 4.43 rather than the public JLC value 4.6. The selected
vendor stackup is authoritative for fabrication; reconcile metadata before final
export. This core difference does not alter the top-to-In1 spacing. Vendor pages
also differ in how they describe finished outer copper; use the selected stackup
and calculator together rather than combining dimensions from different tables.

## Status

J9 nominal footprint and lead reach are verified; exact current JLC candidate is
identified. Connector clearance is closed: the user confirmed the installed MMCX fits,
with this board at the top of the stack and no board above. Ordering-field
entry is complete. The
latest saved DRC is 0 errors / 0 unconnected / one known H1/H2 silk warning;
this pass made no copper or schematic changes and did not rerun unchanged DRC.
A local manufacturing candidate has since been exported and reviewed.
Overall release remains INCOMPLETE pending service acceptance, final stock and
assembly preview. See [current fabrication notes](../releases/review_20261003_1230/fabrication-notes.md), including the specific J9 precision-hole request.
