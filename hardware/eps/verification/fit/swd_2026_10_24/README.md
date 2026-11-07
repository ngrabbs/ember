# SWD-stage footprint inventory

2026-10-24. The independently exported318-part root assigns314 footprints across39 exact footprint types. Four old placeholders remain unassigned: J101,J102,R106,R107. `calculate.py` checks all prior footprint-source hashes before reuse and adds fresh Tag-Connect/TSSOP courtyard queries. `eps_rev_b_at_swd.xml`, `courtyards.csv` and `results.json` bind counts and arithmetic to this source state.

The sum of footprint courtyard bounding rectangles is5013.0528 mm²,58.0214% of the nominal96×90 mm rectangle. Additional known inverter/TMUX/supervisor reservations total9.8344 mm², giving5022.8872 mm². This is inventory arithmetic, not placement, routing, thermal or full-EPS fit acceptance. Header pairs, mating envelopes, RBF, unfinished blocks, board-edge/hole exclusions, capacitor height, battery holder and service-cable access remain additional work.

The Tag footprint has six contacts and three NPTH holes; its stock courtyard omits required central routing/other-signal and cable/clip reservations. Reserve TMUX7.70×5.90 mm and supervisor3.86×4.04 mm, retaining the accepted stock-land deviations. The separate stack-interface reconciliation records the confirmed16 mm facing-surface gap and user-approved5.08 mm spacing exception; it does not prove all tolerances or peer CAN compatibility. No native PCB mutation occurred.

Reproduce with `python3 calculate.py` from this folder. Historical query files remain authoritative only while their recorded source-file hashes match.
