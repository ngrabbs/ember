# EMBER bench dictionary and codec

For day-to-day commanding, responses, displays and replay, start with the
[Yamcs operator guide](../../docs/user/yamcs.md).

[Contract](../../system/protocols/ember_bench_v1.md) · [Ground checklist](../../system/ground_station/TODO.md)

`dictionary.json` is the machine-readable bench subset of Dustin's operation
IDs. `codec.py` is a Python-standard-library encoder/decoder with no radio,
dispatch or flight authorization. `simulator.py` implements the software
GROUND_TEST endpoint. The [Yamcs lab](../yamcs/README.md) now runs an `ember`
instance alongside the upstream sample; `generate_mdb.py` generates its
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
source context. See [session recording and replay](../../system/ground_station/telemetry_sessions.md)
for commands, the demonstrated 60-packet session, and quality/time limitations.

## USB hardware endpoint

`generate_c.py` generates C wire constants from the same dictionary. The
standalone [Pico application](../../firmware/usb_bench/README.md) serializes
fields explicitly and implements the command subset and last-64 cache.
`tests/ground/test_firmware.py` compiles the actual C protocol/framing core on
the host and decodes its output with the Python codec; a host C compiler is
required for those tests.

`framing.py` and firmware C framing implement COBS with a zero delimiter,
bounded to 240 decoded bytes / 242 stream bytes. `usb_bridge.py` requires
pyserial and an exact stable device path, forwards valid packets between USB
and Yamcs UDP, reconnects only that identity and never automatically retries
an uncertain command. `usb_probe.py` checks hardware duplicates, conflict,
invalid/unknown commands, CRC, oversized/partial frames and optional reset.
Stop the bridge before direct probing; its exclusive serial port cannot be
shared. See [USB setup](../../system/ground_station/usb_bench_setup.md).

## Real IHU EPS observations

`eps_bridge.py` exclusively polls `eps json` on the IHU UART adapter and sends
POWER_STATUS (0x10) to Yamcs UDP 10017. This is explicitly a Pi-generated
wrapper; there is no EPS uplink or charger configuration path. The dictionary
adds signed i32 fixed-point engineering fields, all 19 raw words, readout
quality/age and bridge provenance. Yamcs scales engineering values and marks
unavailable sentinels INVALID. See the [packet contract](../../system/protocols/eps_power_status_v1.md)
and [Pi setup/validation](../../system/ground_station/eps_yamcs_setup.md).
