# EMBER bench dictionary and codec

[Contract](../../system/protocols/ember_bench_v1.md) · [Ground checklist](../../system/ground_station/TODO.md)

`dictionary.json` is the machine-readable bench subset of Dustin's operation
IDs. `codec.py` is a Python-standard-library encoder/decoder with no radio,
dispatch or flight authorization. Live Yamcs still uses its upstream sample.

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
