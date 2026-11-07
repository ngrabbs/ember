# UART-stage footprint courtyard budget

2026-10-24. The current 243-part UART integration export has 238 assigned footprints across 33 footprint types. Their courtyard centerline bounding rectangles sum to **4412.34 mm²**, about **51.07%** of the illustrative 96 × 90 mm board rectangle. This is an inventory budget, not placement, routing, thermal or mechanical fit acceptance.

Five older placeholders still lack footprints: J100/J101/J102 and R106/R107. Other unfinished EPS blocks are not included. Connector mating/harness envelopes, usable board outline, battery holder, mounting and upper-board exclusions can consume additional space; a 16 mm top standoff alone does not establish clearance.

The input is the final UART checkpoint XML. Thirty-one earlier footprint readbacks were reused only after their current source-file hashes matched the recorded BMS-stage hashes. Two new stock footprint readbacks come from the UART disposable physical-map checkpoint and were also independently queried. `calculate.py` checks every footprint type is represented and records current source hashes. No CAD geometry was modified by this calculation.
