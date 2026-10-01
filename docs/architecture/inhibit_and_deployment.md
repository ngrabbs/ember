# Inhibit and deployment decisions

<<<<<<< HEAD
[Architecture](README.md) · [Operations draft](operations/README.md)

**Status: prototype decisions recorded April 15, 2026; flight design unresolved.**
This page separates the selected prototype behavior from the earlier design
options. It does not establish launch compliance or verified circuit behavior.

## Prototype decisions

| Jumper | Owner | Installed | Removed |
|---|---|---|---|
| `JP1` | IHU | Watchdog disabled | Watchdog enabled |
| `JP_RBF` | EPS | Main bus inhibited | Main bus enabled |
| `JP_INH1` | EPS | TX and burn-wire inhibited | This inhibit released |
| `JP_INH2` | EPS | TX and burn-wire inhibited | This inhibit released |

All four are 1×2 prototype headers. `JP1` is **WDT Disable (Bench)**, not an
RBF or the proposed software test-mode selector. The selected RBF approach is a
mechanical jumper with no RBF-state telemetry in v0.1. The second TX inhibit is
hardware (`JP_INH2`), not a firmware arm. The charge path is intended to remain
available while RBF inhibits the main bus.

**Required prototype behavior:** either installed inhibit jumper must block TX
and burn-wire operation. Verify this against the actual circuit. The original
notes also call the jumper arrangement “series”; that shorthand is not enough
to specify wiring with the stated closed-contact inhibit behavior.

## Implementation boundaries

- EPS owns power inhibition and the proposed deployment-detect path; IHU owns
  system orchestration in the architecture. Final timer ownership remains open.
- The older timer proposal assumes an EPS MCU and persistent storage, while the
  [interconnect baseline](../../system/interfaces/board_to_board.md) describes EPS
  as charger/regulation hardware without a full digital node. Resolve this before
  implementing deployment timing.
- `DEPLOY_DETECT_FC` has **no allocated stack pin**. Assign it in the
  [canonical pin map](../../system/interfaces/cskb_pinmap.md) before routing it;
  polling over I2C was an alternative in the original discussion.
- Follow the proposed [reset rules](operations/02-transition-table.md#three-reset-rules)
  and [action permissions](operations/03-permission-matrix.md) during review.
  Stored uptime alone does not establish elapsed time across a power loss.

## Before a flight design is approved

| Open decision | Required resolution |
|---|---|
| Deployer and mechanics | Select deployer, switch placement, RBF access, and qualified parts |
| Flight switch polarity | Verify contact states and the change from prototype jumpers; update sensing and test both states |
| Independent inhibits | Confirm required number and independence against the mission's launch interface requirements |
| RF and deployment delays | Establish approved values, timing evidence, reset behavior, and timer owner |
| Persistent state | Define release evidence, attempt/result records, and recovery from uncertain history |
| TX/actuator gating | Define energy switching, bounded actuation, and reset-safe outputs |

The earlier **30-minute RF / 45-minute deployment** values and switch candidates
are historical proposals awaiting reconciliation, not approved flight limits.
The operations draft deliberately leaves these values open.

## Detailed references

- [EPS implementation guide](../../hardware/eps/design/schematic_guide.md)
- [IHU implementation guide](../../hardware/ihu/design/altium_ihu_schematic.md)
- [Original discussion and alternatives](history/inhibit_and_deployment_2026-04-15.md)
=======
Updated 2026-09-23. This document separates the CDS Rev. 14.1 requirements,
EMBER's proposed flight architecture, and the documented v0.1 bench circuit.
It is not a verification of the installed hardware or flight compliance.

See [Startup Sequence](startup_sequence.md) for the reusable Mermaid diagram.
EMBER has one burn-wire-released UHF antenna and fixed solar panels.

## Requirements baseline

The source is Cal Poly's **CubeSat Design Specification Rev. 14.1**, dated
2022-02-09, available from the [CubeSat information page](https://www.cubesat.org/cubesatinfo).
The assigned launch provider's requirements supersede the CDS (§1.4).

| Subject | CDS reference | Requirement |
|---|---|---|
| Stowed power | §§2.3.1–2.3.2 | Powered functions remain off from delivery to the launch vehicle through deployment. At least one deployment switch must electrically disconnect the power system from powered functions while actuated in the dispenser. Power sources include batteries and solar cells. |
| Switch re-actuation | §2.3.2.4 | Release followed by re-actuation must restore prelaunch state, including transmission and deployment timer resets. |
| RBF | §§2.3.4–2.3.5 | An inserted RBF pin cuts all power to the satellite. Access depends on the dispenser; removal before insertion is required when there are no access ports. |
| RF inhibits | §2.3.7 | At least three independent RF inhibits. An inhibit is a physical device between source and hazard; a timer is not an independent inhibit. The note discusses possible launch-provider reductions, not an automatic waiver. |
| Antenna release inhibits | §2.3.8 | At least three independent inhibits against unintended release of deployable structures, including the antenna. |
| Antenna delay | §2.4.4 | Wait at least 30 minutes after deployment-switch activation during dispenser ejection before releasing the antenna. |
| RF delay | §2.4.5 | Do not generate or transmit a signal earlier than 45 minutes after on-orbit deployment. Spacecraft power-on may occur immediately after deployment. |

Both delays use the ejection reference. Expiry permits further checks; it does
not require immediate actuation or transmission. These delays are attributed
to the CDS here, not to an unsupported FCC or ITU timing rule.

CDS §2.3.5 does not grant a blanket exception for keeping the charger powered
with RBF inserted. The document separately discusses permitted battery
protection circuitry (§§2.3.1.2, 2.3.6) and isolated RTC arrangements (§2.3.3).
Any retained powered circuitry needs review against the applicable requirements.

## Proposed flight allocation

| Board | Proposed responsibility |
|---|---|
| EPS | Connections to the structural RBF mechanism and dispenser switches; hardware interruption of power to powered functions; subsystem power distribution. |
| IHU | Startup supervision, elapsed-time tracking, health checks, burn request, and RF permission. Final timer ownership between EPS and IHU is open. |
| Transceiver | Local RF hardware barriers. Suggested location for antenna burn-wire driver and local release barriers if the antenna harness lands here; allocation remains open. |
| Payload | No deployment mechanism. Its power feeds must still obey spacecraft power isolation. |

Hardware inhibition must not depend solely on a processor reading a switch
and choosing to shut down. Status signals to the IHU supplement the hardware
path; they do not replace it. Connection names and stack pins remain subject
to the [CSKB pin map](../../system/interfaces/cskb_pinmap.md).

The removed RBF pin is not a remaining inhibit during launch. Two inputs
on one shared enable net are not automatically two independent physical
barriers. A firmware arm, GPIO command, or added logic gate alone does not
establish another independent inhibit. Analyze the actual energy paths,
controls, and common failures for both RF and burn-wire release. Shared
barriers may protect both hazards only if the analysis supports each path.

## Documented v0.1 bench circuit

The [EPS schematic guide](../../hardware/eps/design/schematic_guide.md)
describes these prototype controls. This is documentation of intent, not a
claim that the current design files or assembled boards have been verified.

| Control | Documented installed state | Documented removed state |
|---|---|---|
| EPS `JP_RBF` | Shorts the shared buck-enable divider to ground; disables the EPS +3V3/+5V bucks | Returns the bucks to normal UVLO control |
| EPS `JP_INH1` or `JP_INH2` | Either parallel jumper pulls shared `DEPLOY_ARMED` low | Both must be removed for `DEPLOY_ARMED` to rise |
| IHU `JP1` | Disables the STWD100 watchdog for bench work | Enables the watchdog |

`JP1` is **not an RBF or spacecraft safety inhibit**. Disabling a watchdog
is a bench convenience, not a general safe state.

The two `JP_INH` jumpers are parallel pull-downs, not two series energy
barriers or two latches. Their common net fans out to `COMMS_TX_EN` and
`BURN_EN`. The direct fan-out provides neither the flight waiting periods
nor a bounded burn pulse. Removing both jumpers must not be treated as a
complete flight deployment sequence.

`JP_RBF` disables the EPS bucks, not every possible power path. The charger
remains connected, and H2.45/H2.46 carry `VBAT` to the payload's local
converter in the interface documentation. Whole-spacecraft shutdown is
therefore **not established** by this jumper description. A flight design
must address raw battery feeds, solar feeds, and signal back-power paths.

## Flight implementation decisions still open

- Select the dispenser, switch count, parts, mounting, and RBF access arrangement.
  Do not treat earlier candidate parts as qualified without supporting evidence.
- Design hardware power interruption while any required deployment switch is
  actuated, covering every powered function and every supply path.
- Define contact polarity from the selected mechanism. A normally closed contact
  held open in the dispenser is one possible arrangement, not a mandated pinout.
  Simply swapping headers for switches does not establish compliance.
- Identify and verify three independent physical inhibits for RF and for antenna
  release under the applicable launch requirements. Do not count the removed RBF
  pin, a timer, or software alone toward the launch configuration.
- Allocate final `DEPLOY_ARMED`, deployment-status, RF-permission, and burn-command
  interfaces. `COMMS_TX_EN` and `BURN_EN` are prototype guide names; final signal
  semantics, drivers, default states, and pins need definition.
- Assign timer ownership. Switch re-actuation resets the prelaunch state and both
  timers. For an ordinary processor reset, use a validated elapsed-time recovery
  method or conservatively restart the delays; a stored uptime timestamp alone
  does not measure time across resets. Preserve burn-attempt history as needed
  to avoid unintended repeated burns.
- Define tested burn pulse limits, retry limits, cooldown, antenna-open sensing,
  and the policy if deployment is unconfirmed. See the startup diagram.
- Establish ground handling that prevents burn or RF activation after RBF removal
  and before dispenser insertion. RBF removal alone is not proof of ejection.

## Verification before flight use

Demonstrate RBF and deployment-switch power isolation on all supply paths;
verify individual inhibit barriers and relevant common failures; verify the
30-minute antenna and 45-minute RF delays; re-actuate deployment switches
throughout startup to verify shutdown and timer reset; and test brownout,
reset, failed burn, and antenna-unconfirmed behavior. These are outstanding
verification tasks, not results of this documentation cleanup.
>>>>>>> 9c995a2639f573ef259ec2b0bffde1811a4cdc81
