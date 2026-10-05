# Walter GNSS service through COMMS MCU

User requested investigation on 2026-10-02. Capability research and interface
proposal only: no GNSS service is implemented or hardware fix captured yet.
LTE telemetry bring-up remains the active bench task.

## Verified vendor capabilities

Walter/Sequans Monarch2 supports GPS and Galileo using snapshot GNSS.
LTE and GNSS share the radio; the vendor explicitly says they cannot operate
concurrently. The positioning example disconnects LTE before requesting a fix,
then reconnects to upload it. It requires a passive GNSS antenna and sky view.

Sources pinned to Walter Arduino commit
`c30b707f8d64b49daec80de6bccfc80c04e42d58`:

- [Positioning description and radio-sharing constraint](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/examples/positioning/README.md).
- [Fix fields, modes and status codes](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/src/WalterModem.h).
- [GNSS AT command implementation](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/src/proto/WalterGNSS.cpp).
- [Example acquisition and LTE disconnect sequence](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/examples/positioning/positioning.ino).
- [Passive antenna and hardware requirements](https://www.quickspot.io/documentation.html).

The fix event exposes latitude/longitude, UTC Unix timestamp, height (vendor
labels this above sea level), north/east/down velocity in m/s, horizontal
confidence estimate in meters, time-to-fix in milliseconds, satellite count,
and satellite identifiers/signal levels. Status differentiates READY, cancelled,
missing RTC and LTE concurrency. READY alone should not imply a valid position;
coordinates, timestamp and confidence require validation.

Sensitivity has low/medium/high modes. Acquisition supports cold/warm and hot
start; the API documents a100 km prior-position requirement for hot start and
automatic cold fallback when time/ephemerides are missing. This is not a
guaranteed acquisition time or performance in orbit.

GNSS commands include configuration (`AT+LPGNSSCFG`), single acquisition/cancel
(`AT+LPGNSSFIXPROG="single"` / `"stop"`), UTC read/set and assistance status/update.
Assistance includes almanac, real-time and predicted ephemeris. The example can
continue when an assistance update fails. Our private EPC does not establish
public assistance-server reachability or trusted UTC; check those separately.
Do not issue raw modem AT commands concurrently with the LTE state machine.

## Proposed IHU-facing service

```text
IHU -- CAN --> COMMS -- existing framed UART --> Walter GNSS service
IHU <-- CAN -- COMMS <-- existing framed UART -- correlated result
```

No additional physical IHU/Walter wires are needed. COMMS remains the controller
boundary. IHU owns requests and decides when to include navigation in downlink.
Walter owns GNSS/modem sequencing and a RAM cache of the last validated fix.

Suggested operations, with wire IDs/schema still to allocate:

| Operation | Behavior |
|---|---|
| GET_LAST_FIX(max_age_ms) | Immediate cached result, explicit valid/stale/no-fix state; does not interrupt LTE |
| START_FIX(deadline_ms) | Immediate accepted/BUSY response with acquisition identity; actual fix runs asynchronously |
| GET_FIX_RESULT(identity) | Pending/result/failed/cancelled with that acquisition identity |
| CANCEL_FIX(identity) | Stop only that acquisition and report its outcome |

A fix may take many seconds. Do not hold the current2-second UART or5-second
CAN request open waiting for it. START admission and acquisition completion are
separate. COMMS relays short correlated requests; IHU polls results without
blocking EPS reads. Include Walter boot ID and acquisition identity to reject
results from a previous boot, plus IHU transaction identity across the proxy.

Proposed result: status, per-field validity, fix UTC and UTC-valid flag, fix
age measured by Walter monotonic time, latitude/longitude, height with stated
datum, N/E/down velocities, confidence, satellite count and time-to-fix.
Use fixed-point wire fields with explicit units and invalid sentinels; the compact
result fits the existing240-byte envelope without a satellite-detail array.
Never represent missing position as valid0/0, or return an old fix as fresh.

Initially reject START_FIX while LTE is active/sending. Between LTE windows:
release the modem from reset, explicitly enter the vendor-required minimum
cellular operational mode, configure/validate GNSS time, acquire with a deadline,
cache the result, then stop GNSS and return to the radio-off state. A later LTE
session may downlink the cached fix. GET_LAST_FIX can use the application cache
while LTE is active; it does not need the modem UART.

## Bench and spacecraft TODO

- [ ] Confirm current UE8.2.1.0 GNSS commands/status behavior on hardware.
- [ ] Capture a bounded outdoor/sky-view fix using the existing passive antenna.
- [ ] Verify no-fix, bad/unknown UTC, stale cache, cancel, reset and timeout paths.
- [ ] Allocate service IDs/result schema and add correlated CAN/UART handling.
- [ ] Demonstrate IHU-requested acquisition and cached result over the current wires.
- [ ] Downlink a GNSS result with provenance and quality to an isolated ground display.
- [ ] Measure acquisition time, energy and LTE reconnect cost.
- [ ] Verify actual modem altitude/velocity/dynamic limits and height datum with
      vendor documentation before relying on it for spacecraft navigation.

No maximum altitude or velocity has been established in the reviewed sources;
do not infer orbital capability from the available height/velocity fields.
