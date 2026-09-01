# EPS Architecture Overview

## Scope

This document defines the baseline Electrical Power System (EPS) architecture
for the current build, including source path, storage path, conversion path,
and integration intent.

## System Goals

- Harvest and condition solar input for battery charging and system load support
- Maintain stable spacecraft rails for communications, controller, and payload
- Provide observable battery/charger telemetry for fault handling and operations
- Support safe operation across sunlight and eclipse-like power conditions

## Baseline Architecture

```text
Solar Array (SM141K10TF, 3S/3S2P eval)
    -> LTC4162 MPPT Charger/PowerPath
        -> 2S2P Li-ion Battery (LG MJ1)
        -> System Load Bus
            -> TPSM5D1806 Dual Buck
                -> 5 V Rail
                -> 3.3 V Rail
```

## Architecture Elements

### Source and Charge Path

- Primary source is a panel configuration based on SM141K10TF cells
- LTC4162 handles charging behavior and source/battery path management
- MPPT behavior is a core validation item for realistic illumination changes

### Battery Path

- Baseline pack is 2S2P LG MJ1 18650 Li-ion
- Final protection and balancing implementation remains open
- Thermal sensing network is present but component values still require closure

### Distribution and Regulation Path

- Target regulated rails are 5 V and 3.3 V via TPSM5D1806
- Regulator behavior is currently treated as a validated module-level path
- Fully integrated EPS rail distribution is in progress

## Operating Modes (Design Intent)

### Sunlit Charge + Load Support

- Solar input powers system load while charging battery when margin exists

### Eclipse / Battery-Only Operation

- Battery supplies system load through regulated rails

### Safe/Recovery Power State

- Reduced load profile with priority rails and telemetry retention
- Provisional policy: keep 3.3 V control/telemetry path active, gate 5 V loads
  unless explicitly required for recovery operations

### Safe-Mode Entry Triggers (Provisional)

- Battery voltage below mission-defined low-voltage threshold
- Repeated brownout/reset behavior over short interval
- Over-temperature indication at charger or regulator path
- Persistent power-path fault indication from EPS telemetry

## Key Open Decisions

- Final battery protection strategy (charger-centric baseline vs independent BMS)
- Thermistor and resistor network values for target battery pack behavior
- EPS startup sequencing and load-shedding policy under brownout conditions
- Integration-level current budget closure per subsystem

## Protection Strategy (Current Direction)

- Current phase direction is charger-centric protection via LTC4162 behavior,
  with supplemental fuse-level protection at source/load boundaries
- Independent BMS remains a deferred option if integration testing shows the
  need for additional pack-level fault isolation

## Related Documents

- Interface definitions: `hardware/eps/design/interfaces.md`
- Bring-up plan and acceptance criteria: `hardware/eps/bringup/phase1_validation.md`
- System power interface context: `system/interfaces/power_interfaces.md`
