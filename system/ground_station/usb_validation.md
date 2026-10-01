# USB hardware validation — 2026-10-01

[Setup](usb_bench_setup.md) · [Checklist](TODO.md)

Pi5 `ember-ground` (`192.168.1.251`) runs Yamcs 5.13.0 and the host bridge.
A USB-powered RP2040 Pico B2 / 2 MiB flash, ID `E663682593753535`, runs the
standalone `firmware/usb_bench` build from `feature/ground-station-usb`.
The EMBER simulator is stopped; `myproject` is retained. This demonstrates
actual hardware command/telemetry transport over USB, not RF acceptance.

## Build and preservation

- Release build passes in m75q `amsat-dev-x86`, SDK2.1.1, GCC ARM14.2.1,
  `PICO_BOARD=pico`, `-Wall -Wextra -Werror`.
- Final UF2 SHA256: `92d60d31b589e46ddd4401887328b7b231b8c567287d93e11a668ac97c39b4d4`.
- ELF size: text 38,584 bytes, data 0, BSS 23,212 (does not include runtime stack).
- `picotool load -v` verified flash and rebooted into application mode.
- Previous `rp2040-si5351-sig-gen` full flash backed up before replacement;
  [inventory](lab_inventory.md) records both copies and hash.

## Automated evidence

16 host tests pass, including compilation of the actual C protocol and framing
core and independent Python decoding, literal wire/CRC checks, duplicate
semantics, invalid/truncated packets and COBS boundary/resynchronization tests.

Direct hardware `usb_probe.py --reset-test` passes:

- SET_PARAMETER2000 accepted/completed; exact duplicate returns cached reports
  and does not increment accepted count. Changed argument with the same
  identity rejects TRANSACTION_CONFLICT and retains2000.
- Status reports accepted count2 after the unique SET and status query.
- Invalid99 rejects INVALID_PARAMETER; unknown command rejects UNKNOWN_COMMAND.
- Corrupt CRC is discarded without a result. A300-byte stream frame and a
  partial frame missing its delimiter recover at the following delimiter;
  subsequent PING completes. COMM_STATUS counts CRC/dropped frames.
- Endpoint reset changes boot ID, restores1000, clears cache/counters; first
  status command reports accepted count1. Initial final-build boot3132296766.

Full Yamcs `ember_smoke.py --transport usb --fault-test` passes on the Pi:

- SET_PARAMETER1000 transaction `(903294082,9)` accepted and completed;
  archived heartbeat uptime intervals `[1001,1000]`ms.
- SET_PARAMETER2000 transaction `(903294082,10)` accepted and completed;
  archived heartbeat intervals `[2000,2000]`ms.
- PING, REQUEST_STATUS and REQUEST_TELEMETRY return correlated results/data.
- Invalid period rejects INVALID_PARAMETER; the valid setting stays in effect.
- Suppressed returned packets produce TIMEOUT / UNKNOWN, never success or
  rejection; no automatic retry occurs. Original1000ms restored afterward.

The bridge is enabled and active; the starter preserves USB Compose selection.
With the bridge running, a further Pico reboot produced disconnect/reconnect
logs for the same identity; the full Yamcs command/telemetry smoke passed again.
Full Pi reboot was verified for the earlier starter; a full reboot of this
expanded USB stack is still a follow-up check. Archive retention/backup,
events, durable retries, ground-restart pending-history recovery and late
result reconciliation remain open. TX counts mean handed to the SDK writer,
not a radio acknowledgement or proof of delivery.
