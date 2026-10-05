# Disposable main-power circuit study

Created 2026-10-04 through Konnect. **Not a fabrication project.**
This project tests the candidate LMR51460 symbol/footprint and presents the
proposed main 5 V circuit separately from the existing carrier hierarchy.
Its PCB contains only a disposable footprint instance, with no routing or
board outline. Its schematic is a complete regulator block with external
input, enable and always-on supply assumptions, not the full power system.

- [Circuit source](payload_power_acceptance.kicad_sch)
- [Circuit render](payload_power_acceptance-circuit.png)
- [Exported connectivity](payload_power_acceptance-circuit.net)
- [Direct ERC result](payload_power_acceptance-erc.json): zero errors/warnings
- [Footprint detail](payload_power_acceptance-footprint-detail.png)
- [IPC-2581 geometry readback](payload_power_acceptance-readback.xml)
- [Symbol query](payload_power_acceptance-symbol-query.json)
- [Footprint query](payload_power_acceptance-footprint-query.json)
- [Physical acceptance record](../../lmr51460_library_acceptance.md): passed for the exact LMR51460 library

Wire-endpoint, component-pin, short and orphan checks also passed. The
exported topology check covers all 11 nets, including the three separate
SW leads, bootstrap across BOOT/SW, feedback divider and separate AGND/PGND
joined through NT1. The geometry check covers all 13 numbered electrical
pads, two paste-only features, dimensions, corner radii, front-side placement
and layer sets, converting IPC Y-up coordinates to KiCad Y-down.

Reproduce the export checks from the repository root:

```sh
python3 hardware/payload_compute/design/validation/check_power_study.py
python3 hardware/payload_compute/design/power_sizing.py
```

Power flags document the externally supplied selected input, ground,
always-on 3.3 V and regulated output after the passive inductor. They do not
prove those external circuits exist or make the full carrier safe. SW1 is
the ERC source representation; SW2/SW3 are explicit passive duplicate leads.

All passives remain sizing placeholders with no qualified MPN/footprint/BOM.
Feedback R1/R2 now use 10 kΩ / 1.91 kΩ, retaining the original nominal
voltage while reducing feedback-leakage error. Fresh ERC, connectivity and
render checks pass after this value-only change. See the
[precision-monitor study](../../precision_monitor.md) for the joint voltage
budget; the output bank is not qualified against its dynamic allowance.
The example output bank is 2×100 µF polarized plus 2×22 µF ceramic; it is
not authorization to add that bank on top of all existing module-side bulk.
Reconcile total effective capacitance and ESR before integration. The main
enable has a 100 kΩ external pull-down; fail-safe permission gating and the
independent 5 V voltage-window monitor are outside this disposable block.

The library default footprint and scratch instance now match. Konnect library
and live-pad queries pass the full physical comparison after the local repair.
The carrier power circuit still needs the implementation and qualification
listed above before integration or fabrication.
