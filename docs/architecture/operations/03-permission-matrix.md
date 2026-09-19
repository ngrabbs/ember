# EMBER inhibit and permission matrix

Draft 0.1 • September 19, 2026 • Proposed behavior for team review

**A mode requests an action; permissions decide whether it may happen.** All required conditions must pass. Unknown required information blocks the affected action.

A **hardware inhibit** physically interrupts the energy path. A **software permission** is a decision in code. A timer or GPIO input alone is not an independent hardware inhibit. The test jumper selects behavior; it does not replace launch inhibits.

| Action | Hardware to identify or design | Software conditions | Proposed owner | Simple verification |
| --- | --- | --- | --- | --- |
| Power flight electronics | Required remove-before-flight and separation-switch power isolation; exact arrangement TBD. | Software cannot authorize power through a physical inhibit. | Power | Exercise each required inhibit and verify the specified loads remain unpowered. |
| Transmit RF | Required independent RF inhibits; transmitter enable held inactive during reset. | RF release/delay cleared; TX-off latch clear; allowed mode; enough energy; acceptable temperature; healthy radio; antenna condition acceptable for the RF design. | Communications, with power and mode-manager inputs | Request TX with each condition false in turn; verify no RF. Reset during TX; verify it stops. |
| Operate deployment actuator | Required actuator-energy inhibits and a design that bounds energization, including during processor failure. | Qualified release; deployment delay complete; STARTUP; sufficient energy; attempts available; no verified completion or unresolved previous attempt. | Housekeeping/mode manager; power enforces energy switching | Test against a simulated load: blocked requests stay off; allowed pulse ends; reset does not cause a repeat. |
| Power and run payload | Switched supply and fault protection. | NOMINAL, or explicit commissioning test; sufficient energy; acceptable temperature; storage available; observation conditions valid for capture. | Payload, with power and mode-manager inputs | Withdraw permission during work; verify controlled stop or power removal and a reported reason. |
| Enable ground-test commands | Test jumper with a defined electrical default. | GROUND TEST selected at boot; deliberate command for each test. TX and deployment still need explicit test authorization and applicable physical protection. | Housekeeping and command/telemetry | Verify jumper status is visible; removing it does not start flight actions; reset selects the new configuration. |

## Ground-test exception rules

- Test configuration starts in SAFE after BOOT.
- Test commands may exercise the same modes and subsystem sequences using separate test history.
- Shortened/simulated waits must be explicitly selected and visibly reported as test settings.
- Automatic physical deployment stays disabled in ground test. An actuator test requires a deliberate command and a controlled test setup.
- Before flight, verify flight configuration, cleared test overrides, and correctly initialized flight records. Removing the jumper alone is not the complete preparation procedure.

## What telemetry should explain

Report the configuration, spacecraft mode, last transition reason, and **why a requested action is blocked**. Examples: “TX blocked: release delay incomplete,” “payload blocked: low energy,” and “deployment blocked: previous attempt outcome unknown.”

Report commanded output and measured feedback separately where feedback exists. A software “off” command alone does not prove the hardware is off.

## Sources and boundaries

- [NASA CubeSat 101](https://www.nasa.gov/wp-content/uploads/2017/03/nasa_csli_cubesat_101_508.pdf), §§6.7 and 6.9.1: physical inhibits, timers, and day-in-the-life verification. Exact counts, delays, and acceptance criteria come from the mission interface requirements.
- [LibreCube remote-segment architecture](https://librecube.gitlab.io/reference_architecture/remote_segment/): essential recovery functions and saved context across processor resets.
- [AMSAT RT-IHU repository](https://gitlab.amsat.org/engineering/golf/rt-ihu), `main.c` boot sequence (local clone reviewed September 19, 2026). Umbilical/charger detection skips the initial waiting/deployment path and writes persistent state. EMBER's separate test history is a proposed difference, not a claim about RT-IHU.

This matrix identifies design work; it does not claim that the required hardware is already implemented or verified.
