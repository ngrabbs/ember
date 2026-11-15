# Flight operations draft

Proposed behavior for team review. The [IHU firmware guide](../../../firmware/ihu/README.md)
describes the implemented profiles. See the [inhibit and deployment design](../inhibit_and_deployment.md)
for physical inhibit and prototype jumper decisions.

## Modes

A single mode manager owns transitions. Subsystems report health and request
actions. Power protection can remove power independently. Radio and payload
sequences run within a mode.

| Mode | Purpose and controlled behavior |
| --- | --- |
| BOOT | Hold TX, payload, and deployment outputs off. Read configuration, reset cause, health, and saved history. |
| STARTUP | Qualify release and track independent RF and deployment delays. Enable actions only after their gates pass. |
| COMMISSIONING | Run commanded checkout with limited telemetry. Leave deployment retries to an approved procedure. |
| SAFE | Preserve energy and essential monitoring. Keep payload and deployment off. Listen when power allows and send brief health reports when permitted. |
| NOMINAL | Schedule capture, processing, and bounded radio activity within power, thermal, and storage budgets. Initially separate payload work from transmission. |

The proposed test input is sampled at boot. Ground tests use simulated
sequences and separate records. A change to the test input takes effect on
reset. Stowed and inhibited describes the physical state before software boots.

## Transitions and reset

| Transition | Proposed gate |
| --- | --- |
| BOOT → STARTUP | Flight configuration, essential checks pass, and validated history shows startup is incomplete. |
| BOOT → SAFE | Ground test, invalid history, essential check failure, repeated resets, or an established-flight reboot. |
| STARTUP → COMMISSIONING | Required waits and deployment verification are complete, or the approved design has no deployable. |
| COMMISSIONING → NOMINAL | Checkout is complete, resources are healthy, and ground approves. |
| Any active mode → SAFE | Critical fault, low energy, or a ground safe request. Stop payload and deployment and curtail RF as permissions require. |
| SAFE → recovery mode | Clear the fault, meet recovery thresholds and dwell, and obtain ground approval. Select the mode from validated history. |
| Any powered mode → BOOT | Watchdog, brownout, or commanded reset. Hold controlled outputs off while rechecking history and permissions. |

Retain validated startup and commissioning history, release and timer
evidence, deployment attempts and results, commanded TX-off state, and reset
history. If timing is uncertain after a reset, block the affected action.
Record a deployment attempt before energizing the actuator and record
confirmed completion separately. An interrupted attempt remains unknown and
requires review before retry. The commanded TX-off latch survives reset and
requires an authorized clear.

## Action gates

| Action | Required conditions |
| --- | --- |
| Power flight electronics | Hardware permits power after release. Software authorization cannot bypass a physical inhibit. |
| Transmit RF | Independent hardware inhibits clear. Release and RF delay qualified, TX-off latch clear, mode permits TX, and radio, antenna, energy, and temperature checks pass. |
| Energize a deployable | Actuator inhibits clear, release qualified, deployment delay complete, in STARTUP, enough energy, and no confirmed or unresolved attempt. Hardware bounds energization. |
| Run payload | NOMINAL or an explicit commissioning test, with power, thermal, storage, and observation checks satisfied. |
| Exercise ground-test actions | Test configuration selected at boot. Each test action is deliberate. Physical protection and explicit authorization still apply to RF and actuator tests. |

Block actions when required information is missing. Report configuration,
mode, transition reason, and the blocking condition. Report commanded state
and measured feedback separately when feedback is available.

## Proposed command capabilities

Consider mode selection, fault clearing, controlled recovery, payload checkout
and capture, retrieval of stored detections and logs, parameter changes, and
ground-only deployment tests. Set flight IDs, arguments, permissions, and
completion criteria after approval. See the
[Yamcs operator guide](../../../ground/yamcs/README.md) for lab operation.

## Open decisions and verification

- Resolve release inputs, inhibit arrangements, RF and deployment delays, and actuator pulse and attempt limits.
- Set energy and thermal thresholds, recovery dwell, RF duty limits, and the commissioning checklist.
- Choose persistent state storage, reset limits, event retention, and how recovery and command permissions are authorized.
- Verify reset during waits, TX, and simulated deployment. Exercise low-energy recovery, corrupt history, and each blocked action before approving flight behavior.
