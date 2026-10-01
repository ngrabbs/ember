# Comms open work

[Comms home](README.md) · [Design overview](design/overview.md)

**Status consolidated September 21, 2026 from existing records; no new hardware
checks performed.** The low-power TX architecture is settled. The latest recorded
layout check reports 0 errors, 1 header-silkscreen warning, and 0 unconnected items;
RF qualification and sourcing remain incomplete.

## Resolve before release

- [ ] **U9 replacement:** qualify TQP3M9036 as a candidate, not a package-only swap.
  Verify the manufacturer land pattern, exposed-paddle mapping, loaded RF response,
  stability, noise, and receiver/mixer headroom. Review a post-LNA attenuation
  provision and exact stocked parts. [Preparation](design/analysis/u9_implementation_preparation.md)
- [ ] **L16:** select with the final U9 bias network. The present 220 nH
  0805HP-221XJRC is a prototype choice; impedance under bias, isolation, stability,
  and the historical SRF requirement remain unresolved. [Audit](verification/components/l16_footprint_acceptance.md)
- [ ] **D15:** qualify an available bidirectional RF protection part against measured
  peak TX power, allowed mismatch, capacitance, package, and ESD ratings.
  [Candidates](bom/replacement_candidates.md)
- [ ] **J9:** obtain the Molex 73415-1471 sales drawing; verify hole pattern,
  protrusion/retention on the planned 1.6 mm board, and RF launch behavior.
  [Recorded geometry](design/analysis/u9_circuit_screen.md#j9-verification-status)
- [ ] **Procurement:** close the J9/L16/D15 ordering fields and U9 replacement;
  recheck every exact populated part against live JLCPCB stock for the actual build
  quantity plus allowance. Preserve J6/J7/J8 as DNP. [Sourcing](bom/README.md)

## Qualify the RF and power paths

- [ ] Define measured acceptance budgets and record available instruments.
- [ ] Measure all four filters; compare existing 9.1 pF tuning with 8.2/7.5 pF
  candidates. Resolve exact capacitor RF models and full tolerance/loading effects
  before selecting new values. [Worksheet](bringup/rf_prototype_checklist.md)
- [ ] Measure TX power, spectrum, XOR drive quality, and pulse-shaping behavior;
  the ADL5602 compression figure is not a clean antenna-output specification.
- [ ] Verify U10 LO drive under actual loading, RX gain/sensitivity/blocking,
  T/R switching, transmitter leakage, and receiver exposure.
- [ ] Qualify L15/L16 bypass/isolation and amplifier stability over intended supply
  and temperature conditions; verify C103/C104 effective capacitance and regulator
  stability. [Capacitor selection record](bom/evidence/remaining_field_completion.md)

## Close the physical and verification record

- [ ] Confirm fabrication stackup and impedance; check the J9 launch and physical
  stack fit. U10 CD636 height/3D clearance remains open.
- [ ] Correct stale schematic annotations, including baseband filter Q/cutoff and
  any remaining VHF references. [Baseband/header record](verification/baseband_and_header_review.md)
- [ ] Regenerate the native netlist and BOM after ordering-field changes. Rerun
  native ERC, DRC, and net parity after accepted replacements; preserve documented
  exclusions without treating them as RF or mechanical qualification.
- [ ] Generate a new, reviewed release bundle only after the above gates close.
  Existing Rev-A manufacturing files are historical.

Component candidates, old stock counts, and screening results are evidence for
this work, not completed substitutions or guaranteed performance.
