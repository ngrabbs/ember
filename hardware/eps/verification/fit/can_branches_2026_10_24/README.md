# CAN-branch-stage footprint inventory

2026-10-24. The fresh independent305-part root export has300 assigned footprints across37 types. Front-courtyard centerline bounding rectangles total **4882.04 mm²**, or **56.51%** of the illustrative96×90 mm rectangle. That includes the30 new CAN branch parts. J100/J101/J102 and R106/R107 remain the five older unselected placeholders.

The inverter stock courtyard needs extra layout allowance for its full permitted flash envelope: reserve4.76×4.05 mm per device. This adds4.284 mm² beyond their two stock bounding rectangles, giving4886.33 mm² including that allowance. This is still not a placed/routed board or mechanical-fit pass; physical stack connectors, mating envelopes, mounting/outline exclusions, battery holder, RBF and other unfinished blocks remain outside this inventory.

`calculate.py` reuses the earlier36 footprint readbacks only after every current source hash matches the recorded source hash, and adds a fresh Konnect courtyard readback for the stock inverter footprint. The complete assigned-type set is checked against the exported graph. `eps_rev_b_at_can_branches.xml` is the unchanged fresh independent CLI export used by the root graph verifier; `results.json` retains its exact hash and all37 footprint source hashes. `courtyards.csv` preserves per-type contributions. No actual PCB geometry or library changed.
