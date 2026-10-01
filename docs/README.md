# EMBER documentation

Start with the mission and system overview, then follow the reference for your task.
**Baseline** describes the documented design, not verified hardware. **Draft** means
proposed behavior or values still needing agreement. **Historical** material records
past reasoning and must not be used as an implementation requirement.

## Start here

1. [Project scope](architecture/project_scope.md) — what we are building and how we will validate it.
2. [System overview](architecture/system_overview.md) — subsystem responsibilities, power, and data flow.
3. [Operating modes](architecture/operations/README.md) — proposed behavior, transitions, and permissions.

## Find what you need

| Task | Read |
|---|---|
| Wire a stack signal | [Canonical CSKB pin map](../system/interfaces/cskb_pinmap.md) |
| Choose stack connectors or spacing | [CSKB mechanical reference](../system/interfaces/cskb_mechanical.md) |
| Connect boards or define messages | [System interfaces and protocols](../system/README.md) |
| Understand prototype inhibits | [Inhibit and deployment decisions](architecture/inhibit_and_deployment.md) |
| Work on a board | [Hardware guide](architecture/hardware_overview.md) |
| Work on radio behavior | [Communications guide](comms/README.md) |
| Work on software | [Firmware guide](firmware/README.md) |
| Integrate and test the stack | [Integration plan](../system/integration/integration_plan.md) |
| Find background reading | [Research references](research/README.md) |
| Find unfinished work | [Project TODO](../TODO.md) |

## Where information belongs

- `docs/`: short explanations of architecture and decisions; links to deeper work.
- `system/`: shared interfaces, protocols, and integration plans.
- `hardware/` and `firmware/`: implementation details and subsystem bring-up.
- `analysis/` and `test/`: calculations, verification procedures, and evidence.

Keep each requirement or assignment in one authoritative document and link to it.
Start pages with their answer and status; put rationale, alternatives, and history
after the working reference or in a linked note. See the short
[editing guide](writing_guide.md).

[Repository home](../README.md)
