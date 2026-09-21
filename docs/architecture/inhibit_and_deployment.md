# Inhibit and deployment decisions

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
