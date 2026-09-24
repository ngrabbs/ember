# EMBER Ground Test

**Status:** Draft 0.2

Ground Operations & Test must support development and verification before the complete RF system is available.

Testing should verify both operator-initiated command transactions and autonomous spacecraft-generated telemetry and event messages.

## Architecture

```text
                 +---- Wired Test Connection ----+
                 |                               |
Ground Console --+                               +--> EMBER
                 |                               |
                 +---- Ground / RF Connection ---+
