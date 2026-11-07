# EMBER bench dictionary and codec

For day-to-day commanding, responses, displays and replay, start with the
[Yamcs operator guide](../../docs/user/yamcs.md).

[Contract](../../system/protocols/ember_bench_v1.md) · [Ground checklist](../../system/ground_station/TODO.md)

`dictionary.json` is the machine-readable bench subset of Dustin's operation
IDs. `codec.py` is a Python-standard-library encoder/decoder with no radio,
dispatch or flight authorization. `simulator.py` implements the software
GROUND_TEST endpoint. The [isolated Yamcs starter](../yamcs/HISTORY.md) runs EMBER alongside
the upstream sample; `generate_mdb.py` generates its
telemetry containers, command definitions and Java wire offsets from the JSON.

From the repository root:

```sh
python3 -m unittest discover -s tests/ground -v
python3 ground/ember/codec.py encode ground/ember/set_period.json
python3 ground/ember/codec.py decode 1900c000001f010000300102112233440000000155667788000003e800060001000007d0829b
```

`set_period.json` requests 2000 ms using parameter 1. Encoding intentionally
permits structurally valid invalid argument values so rejection tests can
exercise the endpoint. Call `validate_arguments(decode(packet))` for range
and enum checks; structural decode alone does not authorize execution.

`vectors.json` records literal packets and expected fields for cross-language
firmware work. The tests verify CRC against the standard check value, fixed
wire bytes, corruption, framing mismatches, sequence wrap boundaries,
transaction identities, and invalid parameter handling.

`session.py` records a bounded HEARTBEAT/POWER_STATUS archive window from Yamcs
and replays its validated packets locally with recorded receive times and
source context. See [session recording and replay](SESSIONS.md)
for commands, the demonstrated 60-packet session, and quality/time limitations.

## Shared command engine and historical USB tools

`generate_c.py` generates wire constants from the same dictionary. The portable
[C command engine](../../firmware/shared/ember_protocol/README.md) serializes
fields explicitly and retains the bounded command/result cache. Active IHU
uses its diagnostic RF PING handler; `tests/ground/test_firmware.py` compiles
the engine on the host and independently decodes results with the Python codec.
The active RF command allowlist is narrower than the generic engine's handlers.

The standalone USB Pico application and its C-only USB framing were removed.
Python `framing.py`, `usb_bridge.py` and `usb_probe.py` remain test/diagnostic tools
for the historical binary USB protocol; they are not the operational IHU text
console bridge. Dated hardware results remain in
[USB validation](../history/2026-10-01/usb_validation.md). Use
[`payload_bridge.py`](payload_bridge.py) for the current sole-owner IHU serial
bench connection and its payload commands/EPS forwarding.

## Real IHU EPS observations

The shared station uses the single-owner IHU serial bridge. It polls
`eps json` and forwards POWER_STATUS to the bench instance. See
[serial ownership and EPS](../yamcs/OPERATIONAL.md#serial-ownership-and-eps)
and the [packet contract](../../system/protocols/eps_power_status_v1.md).
The legacy `eps_bridge.py` and UDP10017 setup are documented in the
[retired UART adapter record](../history/2026-10-01/eps_yamcs_setup.md).

[Optional SDRB CAN adapter](../../system/interfaces/sdrb_adapter.md) validates native IHU packets without owning RF; [current workstreams](../../system/sdrb/TODO.md).
