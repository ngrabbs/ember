# Power interfaces

[System guide](../README.md) · [Canonical pin map](cskb_pinmap.md)

**Status: documented rail allocation; current budgets and protection remain open.**

| Rail | Documented use | Limit/status |
|---|---|---|
| `+5V` | Regulated stack supply | Provisional ≤2.0 A distribution budget |
| `+3V3` | Regulated stack supply | Provisional ≤2.0 A distribution budget |
| `VBAT` | 6.0–8.4 V battery bus; payload local 5 V converter; comms monitors only | Payload consumption exception is defined in the pin map |

The payload carrier's local converter is gated by `PAYLOAD_EN`; its main load
is not supplied from stack `+5V`. Parallel rail pins share current and do not
establish independent redundant supplies.

**Open:** per-subsystem budgets, startup order, brownout/load shedding, and fault
isolation. See [EPS interfaces](../../hardware/eps/design/interfaces.md) for the
EPS-side design record and the pin map for authoritative stack assignments.
