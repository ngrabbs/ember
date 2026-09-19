# EMBER transition table

Draft 0.1 • September 19, 2026 • Proposed behavior for team review

A transition is a change of mode. A condition is something that must be true before the change is allowed. Mode names match the [mode table](01-mode-table.md); action permissions are in the [permission matrix](03-permission-matrix.md).

## Main path

BOOT → STARTUP → COMMISSIONING → NOMINAL

Any running mode can enter SAFE when a serious problem is detected. A reset always returns to BOOT. A later reboot does not automatically replay first-flight actions.

| From → To | Trigger and required conditions | What happens | If conditions are not met |
| --- | --- | --- | --- |
| Unpowered → BOOT | Hardware permits power and supply is stable. | Hold transmitter, payload, and deployment enables off; read test jumper and saved history. | Remain unpowered; recovery belongs to the power system. |
| BOOT → STARTUP | Flight configuration; valid history shows initial startup is incomplete; essential checks pass. | Evaluate release and remaining waits. Resume only from trustworthy evidence. | Invalid history or failed essential checks → SAFE. |
| BOOT → SAFE | Ground-test configuration, invalid history, repeated resets, or an established-flight reboot. | Enter a restricted, observable state. Ground tests can then be deliberately selected. | Essential power protection still applies. |
| STARTUP → COMMISSIONING | Required waits complete and required deployment is verified, or the approved configuration has no deployable. | Save startup completion; begin checkout. | Stay in STARTUP while waiting; failed/unknown deployment after its bounded attempt → SAFE. |
| COMMISSIONING → NOMINAL | Checkout list passed, healthy resources, and ground approval. | Save commissioning completion; enable the mission scheduler. | Stay in COMMISSIONING; serious fault → SAFE. |
| Any running mode → SAFE | Critical fault, low-energy threshold, or ground safe command. | Stop payload and deployment outputs; stop or curtail TX according to permissions; record reason. | No ground approval is required to enter SAFE. |
| SAFE → STARTUP / COMMISSIONING / NOMINAL | Ground recovery command; fault cleared; resources stable for a recovery dwell time. | Select destination from validated history: startup incomplete → STARTUP; commissioning incomplete → COMMISSIONING; otherwise → NOMINAL. | Remain SAFE and report the blocking reason. Ground cannot override physical inhibits. |
| Any running mode → BOOT | Watchdog, brownout, or commanded reset. | Outputs return to their reset-safe state; boot rechecks history and permissions. | Repeated resets lead to SAFE when execution is possible. |

For the first version, SAFE exit requires ground approval. The team must check whether receiver power and ground contact availability make this workable; autonomous low-energy recovery may be added later.

## Three reset rules

1. **Waiting:** persist trustworthy progress without shortening required delays. If timing becomes uncertain, block the affected action and use an approved recovery policy. An ordinary reboot is not evidence of release.
2. **Deployment:** record an attempt before energizing the actuator; record confirmed completion separately. A reset between those events means **unknown outcome**, not “never attempted.” No automatic retry from that condition in this draft.
3. **Transmit stop:** a commanded TX-off latch survives reset. Only the defined authorized clear command releases it; normal health checks still apply.

Flight records needed initially: startup/commissioning completion, release/timer evidence, deployment attempts and result, TX-off latch, and reset history. Validate saved records; keep test records separate. Choose the storage implementation later.

## Values still to choose

| Item | Who supplies the answer |
| --- | --- |
| Release qualification and separate RF/deployment delays | Launch interface requirements and hardware design |
| Low-energy entry, higher recovery threshold, and recovery dwell | Power team, supported by tests |
| Deployment pulse duration and allowed attempts | Mechanism design and tests |
| Maximum TX burst, receive interval, and temperature limits | Communications and power teams |
| Repeated-reset limit and checkout checklist | Housekeeping and command/telemetry teams |

## First tabletop and bench checks

- Boot with jumper installed: visible GROUND TEST indication; no automatic deployment.
- Remove jumper while powered: no configuration change until reset.
- Simulate release and reset during each wait: no early RF or deployment.
- Reset during deployment: output turns off; unknown outcome does not trigger another automatic attempt.
- Lower available energy during payload work or TX: nonessential work stops; recovery conditions prevent rapid mode cycling.
- Set TX-off and reset: TX remains blocked.
- Corrupt a saved record: restricted recovery, with the reason observable through the available diagnostic path.

Use simulated loads for initial deployment tests. These checks start development; final launch verification must follow the mission's approved requirements and procedures.
