# EMBER mode table

Draft 0.1 • September 19, 2026 • Proposed behavior for team review

Start here. This table says what EMBER does. The [transition table](02-transition-table.md) says when it changes modes. The [permission matrix](03-permission-matrix.md) says what may block an action.

## Relationship to existing architecture

These are working proposals, not approved flight requirements. The [system overview](../system_overview.md) assigns system orchestration to the IHU; use that as the starting point for mode-manager ownership. Its earlier “high-duty mode” is treated here as scheduled activity within NOMINAL, pending team review.

The [existing inhibit design notes](../inhibit_and_deployment.md) record prototype jumper decisions. IHU `JP1` disables the watchdog; it is not the proposed software test-mode selector. EPS `JP_RBF`, `JP_INH1`, and `JP_INH2` have separate power/inhibit roles. Whether to add a dedicated test-mode input remains open. Existing timer values and inhibit-count interpretations need reconciliation with the eventual mission requirements before implementation; these tables intentionally leave those values undecided.

## Two configurations, five software modes

The proposed test jumper selects **GROUND TEST** when installed and **FLIGHT** when removed. Read and latch it at boot; changing it requires a reset. Show the selected configuration in console output and telemetry. Jumper polarity and wiring remain to be designed.

Ground test uses the same modes, but suppresses automatic deployment and allows deliberate test commands. Any simulated timing or deployment results stay separate from flight records. Flight configuration alone does not permit transmission or deployment.

| Mode | Purpose | Power and housekeeping | Payload | Radio | Deployment |
| --- | --- | --- | --- | --- | --- |
| **BOOT** | Establish a known starting point after every reset. | Keep controlled outputs off; read configuration, reset cause, health, and saved flight history. Start essential supervision. | Off. | Transmitter off; initialize command reception when permitted. | Off. |
| **STARTUP** | Handle first release, required waits, and any initial deployment. | Monitor energy and health; qualify release; track separate RF and deployment delays. | Off. | Receive when permitted; transmit only after all RF permissions pass. | Only through the permission checks and bounded sequence below. |
| **COMMISSIONING** | Check that the spacecraft and payload work before routine use. | Monitor health; perform planned checkout steps. | Individual commanded checks. | Command reception and limited telemetry, subject to permissions. | No automatic repeat; any retry needs an approved procedure. |
| **SAFE** | Preserve energy and a route to recovery. | Essential monitoring; shed nonessential loads. At critically low energy, the power system may shut down the computer. | Off. | Listen when affordable; brief health telemetry only if permitted. | Off. |
| **NOMINAL** | Perform the EMBER mission. | Schedule work within power, temperature, and storage limits. | Capture → process → store → idle. | Listen → bounded transmit → listen, subject to permissions. | Off. |

**Stowed/inhibited** is a physical condition before software can run, not a sixth software mode. End-of-mission behavior will be added when mission requirements are defined.

## Keep the first version small

- One mode manager owns mode changes. Subsystems report status and request actions.
- Power protection can remove power regardless of the software mode.
- Radio and payload sequences run inside the selected mode; they do not create more spacecraft modes.
- Initial conservative scheduling: do not overlap payload capture/processing with transmission until the power budget and tests support it.
- Every mode change reports the previous mode, new mode, and reason.

## First team decisions

1. Which controller runs the mode manager, and which functions remain available if it fails?
2. Which loads can the power system switch off independently?
3. What deployables and release inputs will EMBER actually have?

This draft does not assume active attitude control. Add an observation-readiness check once pointing needs and capabilities are known.
