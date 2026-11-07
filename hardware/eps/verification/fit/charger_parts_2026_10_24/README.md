# Charger-stage courtyard budget — 2026-10-24

This read-only update uses the 187-part charger-stage XML export and fresh
Konnect geometry queries for all 28 assigned footprint types. Run
`python3 calculate.py` to reproduce the CSV/JSON results from the saved export.
It makes no CAD changes. The input-netlist hash and footprint-source hashes
are recorded; this is a revision-specific budget, not a live full-EPS result.

**182 assigned footprints sum to 3916.20 mm² of courtyard centerline bounding
rectangles**, about 45.3% of an illustrative 96 × 90 mm rectangle. The
[previous 160-part checkpoint](../current_parts_2026_10_23/README.md) summed
to 3600.78 mm²; the 27 charger/controller additions add about 315.42 mm².
The five missing footprints remain logical debug/CAN connectors J100–J102
and DNP CAN termination resistors R106/R107.

These rectangles use the queried courtyard graphic centerline extents,
including circular test-point courtyards. They are not copper areas or a
minimum packing bound. No placement, rotation, routing, mechanical interference,
thermal-copper clearance or usable-face allocation was checked. A percentage
of a board rectangle does not prove fit.

The full BMS circuit, RBF/deployment switching, managed payload feed, CAN
branch containment and final stack headers remain outside this BOM. Those
parts, connector insertion/withdrawal access, mounting holes and battery-holder
clearance must be included before a full placement decision. The 16 mm top
standoff is a mechanical input, not an established component-height envelope.
No real PCB synchronization or layout was performed.
