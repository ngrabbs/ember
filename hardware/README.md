# Hardware

[Documentation home](../docs/README.md) · [Board interfaces](../system/interfaces/README.md)

| Board or instrument | Start here |
|---|---|
| Electrical power | [EPS](eps/README.md) |
| Solar panel | [PV panel](pv_panel/README.md) |
| Housekeeping computer | [IHU](ihu/README.md) |
| UHF radio | [COMMS](comms/README.md) |
| Jetson compute carrier | [Payload compute](payload_compute/README.md) |
| Optical instrument | [Narrowband camera project](https://github.com/ngrabbs/koenig_wildfire) · [Detection background](../docs/research/k_line_detection.md) |
| Experimental S-band transmitter | [S-band payload](payload_exp_sband_tx/README.md) |

The Jetson carrier and the Raspberry Pi camera setup are distinct development
configurations. Use the board's design and release records for the applicable
revision, bring-up procedure, and measured results.

## Shared conventions

- [CSKB pin assignments](../system/interfaces/cskb_pinmap.md) and [connector mechanics](../system/interfaces/cskb_mechanical.md)
- [KiCad schematic policy](conventions/kicad_schematic_policy.md) and [net naming](conventions/net_naming.md)
- [Fabrication rules, stackup, and impedance](conventions/kicad_jlcpcb_design_rules.md)
- [RF layout](comms/design/rf_layout_guidelines.md)
