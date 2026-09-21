# Spacecraft operations

[Architecture](../README.md)

**Draft 0.1 · September 19, 2026 · For team review.** These three tables describe
proposed behavior; they are not approved flight requirements.

1. [Modes](01-mode-table.md): what the spacecraft does.
2. [Transitions](02-transition-table.md): when it changes mode, including after reset.
3. [Permissions](03-permission-matrix.md): what must be true before an action is allowed.

Read all three before implementing the mode manager. Prototype jumper decisions
are in [inhibit and deployment](../inhibit_and_deployment.md); flight timer values,
inhibit arrangements, and the proposed test-mode input remain unresolved.
