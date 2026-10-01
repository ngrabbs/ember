# EMBER Ground Operations & Test

**Status:** Draft 0.2

The Ground Operations & Test subsystem provides the operator-facing interface used to monitor, command, and test EMBER.

EMBER is designed to operate autonomously during normal mission operations. Ground Operations monitors spacecraft health and mission activity, receives periodic telemetry and event-driven messages, displays and logs significant events, and provides operator command capability for configuration, testing, recovery, manual operations, and on-demand information requests.

Ground communications are shared with Flight Communications, and the exact division of responsibilities will continue to be refined as the design develops.

## Design Documents

1. [Subsystem Overview](01-subsystem-overview.md)
2. [Command Dictionary](02-command-dictionary.md)
3. [Command Responses](03-command-responses.md)
4. [Telemetry & Event Dictionary](04-telemetry-dictionary.md)
5. [Ground Console](05-ground-console.md)
6. [Ground Test](06-ground-test.md)
7. [Subsystem Interfaces](07-interfaces.md)
8. [TBD Items](08-tbd-items.md)
9. [Command / Telemetry Protocol](09-command-telemetry-protocol.md)

## Related Operations Documents

- [Mode Table](../01-mode-table.md)
- [Transition Table](../02-transition-table.md)
- [Permission Matrix](../03-permission-matrix.md)

## Application Messaging Architecture

Ground Operations supports four primary application-level message categories:

- **Periodic Telemetry** - Routine spacecraft status generated automatically.
- **Event Messages** - Significant spacecraft or mission events generated automatically.
- **Operator Commands** - Operator-initiated requests for information, configuration, testing, recovery, or manual operations.
- **Command Responses** - ACK/NACK responses, requested information, and command-completion information.

Normal mission operation does not require continuous operator commands.

Examples of autonomous spacecraft messages include:

```text
HEARTBEAT
POWER_STATUS
PAYLOAD_STATUS
MODE_EVENT
FAULT_EVENT
FIRE_DETECTED
