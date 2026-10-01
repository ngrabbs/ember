# EMBER Ground Test
**Status:** Draft 0.1

Ground Operations & Test must support development before the complete RF system is available.

## Architecture
```text
                 +---- Wired Test Connection ----+
                 |                               |
Ground Console --+                               +--> EMBER
                 |                               |
                 +---- Ground / RF Connection ---+
```

Where practical, the same logical commands and telemetry should be used for wired and RF communications.

EMBER currently distinguishes GROUND TEST and FLIGHT configurations. Test-only commands require the appropriate GROUND TEST configuration.

## Test Objectives
- Command creation, transmission, reception, and validation
- ACK/NACK responses
- Sequence-number matching
- Mode permissions and transitions
- Telemetry generation and decoding
- Fault/event reporting
- Command/telemetry logging

## End-to-End Path
```text
Operator
 |
Ground Console
 |
Command Interface
 |
Communications Path
 |
EMBER
 |
Command Execution
 |
Telemetry Response
 |
Ground Console
 |
Operator
```

## Verification Progression
Testing progresses from simulated command/telemetry, to wired EMBER testing, to Ground/Flight Communications integration, and finally RF end-to-end testing. Initial verification covers valid commands, NACK handling, mode permissions, timeouts, duplicate-command protection, telemetry/events, session logging, wired operation, and RF operation. Detailed test cases are defined in `09-command-telemetry-protocol.md`.
