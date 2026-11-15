# Ground release manifests

These October 17, 2026 records identify the files and Yamcs assets audited
for each release. Use a manifest from the release you intend to verify.
See the [ground quick start](../README.md) for current operations.

| Recorded release | Manifests |
| --- | --- |
| Two-instance Yamcs · fire-check 1.6.0 | [Flight `ember`](yamcs-flight-1.6.0.json) · [Serial `ember-bench`](yamcs-bench-1.6.0.json) |
| Two-instance Yamcs · dashboard cleanup | [Flight](yamcs-flight-dashboards-20261017.json) · [Bench](yamcs-bench-dashboards-20261017.json) |
| Two-instance Yamcs · initial split | [Flight](yamcs-flight-20261017.json) · [Bench](yamcs-bench-20261017.json) |
| Earlier Yamcs setups | [Shared deployment](yamcs-operational-20261017.json) · [Payload 1.3.0](yamcs-payload-1.3.0.json) · UHF [1.0.0](yamcs-uhf-1.0.0.json), [1.1.0](yamcs-uhf-1.1.0.json), [1.2.0](yamcs-uhf-1.2.0.json) |
| Bounded DBPSK receiver | [2.0.0](receiver-2.0.0.json) · [2.1.0](receiver-2.1.0.json) · [2.2.0](receiver-2.2.0.json) · [2.4.0](receiver-2.4.0.json) |
| Payload bench evidence | [Live validation record](payload-live-validation.json) |

## Verify Yamcs

From the repository root, compare the Pi's loaded mission database and display
assets against a recorded baseline. These examples use the 1.6.0 manifests.

```sh
python3 ground/yamcs/build_identity.py --url http://192.168.1.251:8090 \
  --instance ember --check ground/releases/yamcs-flight-1.6.0.json
python3 ground/yamcs/build_identity.py --url http://192.168.1.251:8090 \
  --instance ember-bench --check ground/releases/yamcs-bench-1.6.0.json
```

`MATCH` confirms the audited fingerprint. `DRIFT` means the deployed assets
differ from that snapshot. Use the [deployment guide](../yamcs/OPERATIONAL.md)
to check runtime paths and service health.

## Verify the bounded DBPSK receiver

Run from the root of the checkout used to receive packets.

```sh
python3 ground/bpsk/identity.py
python3 ground/bpsk/identity.py --check ground/releases/receiver-2.4.0.json
```

The first command prints the receiver version and file hashes. The second
compares them to the recorded 2.4.0 baseline. On the Pi, use
`systemctl show ember-fire-uplink --property=ExecStart --value` to see the
continuous UHF gateway's deployed entry point. The receiver manifests cover
the bounded `live.py` receiver.
