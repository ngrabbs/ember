# Power Interfaces

## Purpose

Capture power rail interfaces between EPS and all dependent subsystems.

## Baseline Rail Set

- 5 V regulated rail (distribution target, provisional <= 2.0 A)
- 3.3 V regulated rail (distribution target, provisional <= 2.0 A)
- Internal battery/load path for EPS conversion stages

## Integration Items to Close

- Current budgets per subsystem within rail ceilings
- Startup sequencing dependencies
- Brownout behavior and load shedding policy
- Fault isolation strategy

## Detailed EPS Interface Source

See `hardware/eps/design/interfaces.md` for current EPS-side interface mapping.
