# BMS-stage footprint area budget

2026-10-24. The 233-part development root has 228 assigned footprints spanning 31 types. Fresh Konnect queries for every assigned type give **4317.27 mm²** when each footprint's front courtyard is replaced by its axis-aligned centerline bounding rectangle and multiplied by its count. This is **49.97%** of an illustrative 96 × 90 mm board rectangle.

The charger-stage sum was 3916.20 mm² for 187 parts; this stage adds 401.07 mm² by the same arithmetic. This is an area budget, not placement, routing, thermal or mechanical fit acceptance. No real PCB geometry was changed. It excludes spacing between functional blocks, routing channels, mounting holes/edge exclusions, battery-holder/RBF interference and the unfinished circuitry.

J100/J101/J102 still lack selected debug/CAN connector footprints, and R106/R107 are logical DNP termination placeholders. The full stack headers are not integrated. RBF, managed payload distribution, final bus isolated power and remaining fault containment are also absent. DNP status is metadata, not an accepted native assembly-variant implementation.

[Results](results.json), [courtyard table](courtyards.csv), [frozen exported netlist](eps_rev_b_at_bms.xml) and [all 31 fresh readbacks](footprint_readback.json) preserve this calculation. `python3 calculate.py` regenerates the JSON/CSV and checks the expected 233 physical references, 228 assigned footprints and five missing references. The source netlist hash and every actual footprint-file hash are recorded in the result. All shapes are reduced to bounding rectangles; overlap and unallocated usable area are not solved by this sum.
