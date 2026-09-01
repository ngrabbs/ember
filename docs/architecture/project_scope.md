# Project Scope and Positioning

## Mission

EMBER detects actively flaming vegetation from orbit by its potassium emission
signature (766.5 / 769.9 nm) rather than by thermal infrared, and screens
observations onboard so that a low-rate UHF link returns detection reports
instead of imagery.

Full problem framing, prior art, and the competitive argument are held with the
capstone coursework; this repository carries the engineering record.

## Baseline Build

The baseline for the current build is:

- **Payload** — three narrowband NIR channels, onboard detection processing,
  compact detection reports (position, time, confidence)
- **Communications** — half-duplex UHF near 437 MHz (70 cm), discrete RF chain
  with Si5351A frequency generation and RP2040 control, plus the fixed ground
  station that receives it
- **Command and Data Handling** — RP2040 housekeeping unit under FreeRTOS;
  mode control, command authority, telemetry aggregation
- **Electrical Power System** — solar input, Li-ion storage, MPPT charge
  control, regulated rail distribution

Boards interconnect over the Pumpkin CubeSat Kit Bus (CSKB) H1/H2 stack headers.

## Validation Approach

Detection performance is scored against instrumented controlled burns, with the
payload carried over an active fire by an uncrewed aircraft so that detections
are compared against ground truth recorded on the same burn. Instrument-level
development and flight testing live in the payload instrument repository.

## Out of Scope

Direct-to-cell / NTN modem work was carried in earlier revisions of this
repository as an exploratory payload concept. It is superseded by the
potassium-line instrument and is no longer tracked here.
