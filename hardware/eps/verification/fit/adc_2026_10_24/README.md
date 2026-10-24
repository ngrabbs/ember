# ADC-stage footprint inventory

2026-10-24. The345-part ADC-stage root assigns341 footprints across39 exact footprint types. The four old unassigned placeholders remain J101,J102,R106,R107. All27 telemetry additions are included. `calculate.py` reuses the earlier saved Konnect courtyard queries only after checking every current footprint-source hash against the recorded source hashes. No new footprint or PCB geometry is authored.

The sum of courtyard bounding rectangles is5176.5668 mm²,59.9140% of the nominal96×90 mm board rectangle. Known inverter, two TMUX and two supervisor reservations add15.3848 mm², giving5191.9516 mm². The27 added parts account for163.5140 mm² of footprint rectangles before the extra reservations. These are area inventories, not placement, routing, thermal, full-EPS fit or a usable-area calculation.

Physical stack headers/mating envelopes, edge/hole exclusions, RBF, unfinished circuits, battery holder/cells, harness bends and service-cable access still require physical review. The16 mm clear facing-surface gap and5.08 mm EMBER header-spacing exception remain the accepted interface decisions. They do not determine the board underside clearance. The older STEP export is not evidence of the current printed holder's dimensions. No underside space is assumed available by this budget.

`eps_rev_b_at_adc.xml` and its recorded hash bind the inventory to the exported graph. Reproduce with `python3 calculate.py`; the script fails if the exact footprint queries, expected part inventory or source hashes no longer match. Historical inventory packets remain evidence at their recorded source states.
