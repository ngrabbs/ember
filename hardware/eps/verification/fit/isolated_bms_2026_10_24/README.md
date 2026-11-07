# Isolated-BMS-stage courtyard inventory

2026-10-24. The frozen275-part integration export has270 assigned footprints across36 types. Their front-courtyard centerline bounding rectangles total **4687.12mm²**, or **54.25%** of the illustrative96×90mm board rectangle. The new32 parts add approximately274.78mm² over the UART-stage inventory. This is an area inventory, not a placement, routing, thermal or mechanical fit pass.

J100/J101/J102 and R106/R107 remain five older unselected placeholders. Physical stack connectors, their mating/harness envelopes, mounting/outline exclusions, battery holder, RBF mechanism and unfinished EPS blocks still need space. The16mm reported top standoff does not establish usable component height or clearance.

`calculate.py` reuses the earlier33 footprint readbacks **only after comparing every current footprint source hash with its recorded UART-stage hash**. Three independently refreshed Konnect courtyard queries cover the approved TPS2553/UCC33020 and accepted LT3014 footprints. Every assigned type is represented. The source is a fresh independent whole-root CLI export, checked against the integration owner's component/net blocks. New queries are in `new_footprint_queries.json`; source hashes and exact counts are in `results.json`; `courtyards.csv` lists the rectangle contributions. No CAD or PCB geometry was changed by this calculation.
