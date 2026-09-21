# Ground Operations & Test - Subsystem Overview
**Status:** Draft 0.1

## Purpose
Provides the operator interface used to command, monitor, and test EMBER.

## Primary Responsibilities
- Ground operator console
- Interface electronics
- Controls and displays
- Command generation
- Telemetry decoding and display
- Command and telemetry logging
- Command dictionary
- Telemetry dictionary
- Ground test connection
- Ground operations and test procedures

## Working Architecture
```text
Operator
  |
Ground Operations Console
  |
Command / Telemetry Software
  |
Ground Interface
  |
Ground Radio / Modem
  |
Ground Antenna
  | RF Link
EMBER Antenna
  |
Flight Radio
  |
IHU / Spacecraft Management
  +-- Payload
  +-- EPS
  +-- Other Subsystems
```

## Responsibility Boundary
Ground Operations primarily defines the operator interface, command generation, telemetry presentation, logging, and ground testing.

Flight Communications primarily provides the flight radio, spacecraft antenna, RF hardware, RF transmission/reception, and associated signal conditioning.

Ground communications are shared. The final division of ground radio/modem, antenna, enclosure, console interface, packet transport, and link testing is TBD.

Spacecraft Management independently validates and executes spacecraft commands.

## Design Philosophy
Where practical, the same logical command and telemetry definitions should work over both wired development/test connections and RF communications.
