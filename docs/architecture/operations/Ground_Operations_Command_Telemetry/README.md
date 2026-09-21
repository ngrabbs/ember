# EMBER Ground Operations & Test
**Status:** Draft 0.1

The Ground Operations & Test subsystem provides the operator-facing interface used to command, monitor, and test EMBER. Ground communications are shared with Flight Communications and the exact division will be refined as the design develops.

## Design Documents
1. [Subsystem Overview](01-subsystem-overview.md)
2. [Command Dictionary](02-command-dictionary.md)
3. [Command Responses](03-command-responses.md)
4. [Telemetry Dictionary](04-telemetry-dictionary.md)
5. [Ground Console](05-ground-console.md)
6. [Ground Test](06-ground-test.md)
7. [Subsystem Interfaces](07-interfaces.md)
8. [TBD Items](08-tbd-items.md)
9. [Command / Telemetry Protocol](09-command-telemetry-protocol.md)

## Related Operations Documents
- [Mode Table](../01-mode-table.md)
- [Transition Table](../02-transition-table.md)
- [Permission Matrix](../03-permission-matrix.md)

## Draft 0.1 Status
The application-level Ground Operations architecture is defined through the command/telemetry protocol. Remaining work is primarily interface resolution with Flight Communications, Spacecraft Management, EPS, and Payload, followed by implementation-level definition for Draft 0.2.

The logical command and telemetry definitions are intended to remain transport-independent where practical so the same application behavior can be exercised over wired development connections and the eventual RF link.
