---
markmap:
  initialExpandLevel: 4
---
# CubeSat Hardware Memory Map

## Document Purpose

This memory map captures hardware decisions, alternatives, and rationale in a
single place for design reviews and traceability.

## Status Legend

- Selected: baseline component or architecture
- Candidate: viable option still under evaluation
- Deferred: valid option intentionally not in current baseline

## Communications Subsystem

| Item | Status | Role | Reference | Notes |
|---|---|---|---|---|
| Discrete amateur-band TX/RX board | Selected | Baseline communications architecture | [`hardware/comms/design/overview.md`](comms/design/overview.md) | UHF downlink and VHF uplink split |
| RP2040 control path | Selected | Timing, framing, and board control | [`hardware/comms/design/overview.md`](comms/design/overview.md) | Central control for TX/RX sequencing |
| Si5351A clock generation | Selected | Shared RF clock source | [`hardware/comms/design/overview.md`](comms/design/overview.md) | Used across TX and RX paths |

## Electrical Power System (EPS)

| Item | Status | Role | Reference | Notes |
|---|---|---|---|---|
| SM141K10TF solar panel | Selected | Primary EPS energy source | [SM141K10TF link](https://www.digikey.com/en/products/detail/anysolar-ltd/SM141K10TF/14311415) | Evaluate final 3S/3S2P implementation against load profile |
| 2S2P LG MJ1 pack | Selected | Battery storage | [`hardware/eps/README.md`](eps/README.md) | Protection and balancing details still open |
| LTC4162 charger | Selected | Charge control with MPPT and telemetry | [LTC4162 link](https://www.digikey.com/en/products/detail/analog-devices-inc/LTC4162EUFD-LADM-PBF/9446107) | Baseline charger path |
| LTC4162 DC2038A eval board | Selected | Bring-up and validation platform | [DC2038A-A link](https://www.digikey.com/en/products/detail/analog-devices-inc/DC2038A-A/9996133?s=N4IgTCBcDaICIGEwAYDMAOAggWkyAugL5A) | Used for early bench characterization |
| BQ24650 | Candidate | Simpler charger alternative | [`hardware/hardware_vendors.md`](hardware_vendors.md) | Lower complexity, reduced telemetry |
| LTC4015 | Candidate | Feature-rich charger alternative | [`hardware/hardware_vendors.md`](hardware_vendors.md) | Higher integration complexity |
| LT3652 | Deferred | Pseudo-MPPT charger option | [`hardware/hardware_vendors.md`](hardware_vendors.md) | Not preferred for current baseline |
| TPSM5D1806 module | Selected | Primary buck regulation | [TPSM5D1806 link](https://www.digikey.com/en/products/detail/texas-instruments/TPSM5D1806RDBR/14004345) | Dual rail target for 5 V and 3.3 V buses |
| TPSM5D1806 EVM | Selected | Regulator validation hardware | [TPSM5D1806EVM link](https://www.digikey.com/en/products/detail/texas-instruments/TPSM5D1806EVM/13563013?s=N4IgTCBcDaICoAUDKBZArAEQIwA4AMAbCALoC%2BQA) | Supports rail and thermal characterization |
| LM25116, MP2307, TPS5430, TPS62125, AP63205 | Candidate | Regulator alternatives | [`hardware/hardware_vendors.md`](hardware_vendors.md) | Held for trade studies and contingencies |
| LM2596 | Deferred | Legacy regulator fallback | [`hardware/hardware_vendors.md`](hardware_vendors.md) | Larger footprint and older performance profile |
| 10k NTC thermistor | Selected | Charge thermal feedback | `hardware/eps/kicad/eps.kicad_sch` | Required for robust charging behavior |
| Inline fuse/polyfuse | Candidate | Input/output protection | [`hardware/eps/README.md`](eps/README.md) | Final protection architecture pending |
| Dedicated 2S BMS | Candidate | Battery safety layer | [`hardware/eps/README.md`](eps/README.md) | Include if needed after integrated safety review |
| USB-to-I2C adapter | Selected | Telemetry logging support | [`hardware/eps/bringup/phase1_validation.md`](eps/bringup/phase1_validation.md) | Useful for charger register visibility |
| Adjustable electronic load | Selected | Bench load and transient testing | [`hardware/eps/bringup/phase1_validation.md`](eps/bringup/phase1_validation.md) | Core bring-up instrument |

## Mechanical and Integration References

| Item | Type | Reference | Notes |
|---|---|---|---|
| Main 1U structure assembly | CAD reference | [Onshape model](https://cad.onshape.com/documents/f54077faa9eaef25e1f615dc/w/05a52062e76f7bd3695dddef/e/5aa71494ffb6396194e6798c?renderMode=0&uiState=684049080496457e60637a0b) | Integration and envelope checks |
| 2S2P battery holder | Development aid | [Thingiverse model](https://www.thingiverse.com/thing:456900) | Development and bench packaging reference |

## Open Items

1. Finalize battery protection and balancing implementation strategy
2. Lock EPS rail targets and current budgets from integrated subsystem loads
