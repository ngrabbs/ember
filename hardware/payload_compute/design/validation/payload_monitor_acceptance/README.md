# Disposable voltage-monitor study

2026-10-04. Bounded REF3425IDBVR / LM2903BIDR circuit implemented through
Konnect. [Schematic preview](payload_monitor_acceptance.png),
[KiCad project](payload_monitor_acceptance.kicad_pro),
[exported circuit](payload_monitor_acceptance.net), and
[final query/check evidence](payload_monitor_acceptance-accepted-library-evidence.json).

The reference is powered/enabled by AON 3.3 V. Its force and sense outputs
are tied locally. Independent module-5-V dividers feed the two comparator
inputs with opposite polarity, so either voltage fault pulls `5V_WINDOW_OK`
low. Both open-collector outputs share one 10 kΩ AON pull-up. Comparator
supply is `VIN_SELECTED`, not 3.3 V; source qualification must guarantee
its operating range before arming the module.

Checks: direct KiCad ERC zero errors/warnings; zero floating wire endpoints,
unconnected pins, shorted named nets or heuristic orphans. All eight exported
nets match exact intended membership. All 14 physical leads match accepted
symbol functions, footprint geometry/layers and live front-side pad positions.
Final schematic and refreshed footprint renders were visually inspected.
Run `python3 hardware/payload_compute/design/validation/check_monitor_study.py`
from the repository to check saved evidence. Refresh exports and queries after
changes; this script does not independently run ERC or query live KiCad.

The PCB contains only two disposable IC footprints with no electrical net
assignments, routing or outline. It proves package orientation/geometry and
does not implement this circuit. Scratch reference labels need final placement.
No fabrication outputs should be generated from this project.

See [physical pin maps](../../monitor_library_acceptance.md) and
[threshold budget and qualification gates](../../precision_monitor.md).
Exact precision resistor/capacitor MPNs remain unaccepted. DC thresholds are
allocated design corners, not measured limits. Reference startup, partial
power, noise, filter/response delay, receiver thresholds, fault-energy
containment and the external run latch still require design/qualification.
The monitor alone does not disconnect Jetson power or guarantee protection.
