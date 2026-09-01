# EPS Interfaces

## Scope

This document defines EPS external interfaces and integration assumptions for
the current architecture baseline.

## Power Interfaces

| Interface | Direction | Nominal | Status | Notes |
|---|---|---|---|---|
| `SOLAR_IN` | In | Panel-dependent | In progress | 3S/3S2P configuration under evaluation |
| Battery bus (2S Li-ion) | Internal/Out | ~7.2 V nominal | In progress | 2S2P LG MJ1 baseline pack |
| `5V_RAIL` | Out | 5.0 V | Planned | Via TPSM5D1806 integrated path, provisional <= 2.0 A budget |
| `3V3_RAIL` | Out | 3.3 V | Planned | Via TPSM5D1806 integrated path, provisional <= 2.0 A budget |
| `SYSTEM_LOAD` | Out/Internal | Unregulated bus path | In progress | Present in schematic labeling |

## Control and Telemetry Interfaces

| Signal | Direction | Function | Status |
|---|---|---|---|
| `SCL` | Bidirectional | Charger telemetry/control bus clock | Present in schematic |
| `SDA` | Bidirectional | Charger telemetry/control bus data | Present in schematic |
| Charger status fields | Out | Voltage/current/charge-state observability | In progress (validation) |
| Battery temperature sense | In | Charge safety/thermal behavior | In progress (value closure pending) |

## Interface Assumptions

- System consumers primarily use regulated 5 V and 3.3 V rails
- EPS telemetry will be consumed by internal housekeeping unit firmware
- Provisional integration ceiling is 2.0 A per regulated rail until budgets close
- Protection and fault isolation details will be finalized before release freeze

## Pending Interface Closure Items

- Per-subsystem current allocation table within provisional rail ceilings
- Power-on sequence and brownout response behavior
- Rail enable/disable ownership (EPS autonomous vs internal housekeeping unit commanded)
- Final connector and pin-level interface map

## Cross-References

- EPS architecture: `hardware/eps/design/overview.md`
- System integration interface file: `system/interfaces/power_interfaces.md`
