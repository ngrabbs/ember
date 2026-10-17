# Ground release identities

Operational update (October 17, 2026): select `ember` / `realtime` for USB,
EPS UART, LTE, UHF and payload. [Shared deployment and history access](../yamcs/OPERATIONAL.md).
Older isolated-instance setup/proof instructions below are historical; use
operational preparation for the running Pi.

Current baselines:

| Component | Version | Verification |
| --- | --- | --- |
| Yamcs upstream server | 5.13.0 | Running `/api` server version/revision |
| EMBER UHF definitions + shared dashboards | 1.2.0 | `yamcs-uhf-1.2.0.json` |
| Live UHF receiver | 2.2.0 | `receiver-2.2.0.json` |

These are separate from COMMS MCU firmware 0.24.0. Receiver 2.0.0 is the first
semantic release of pipeline v2, with content identity added; wire format and
DSP behavior are unchanged. `receiver_version: 2` remains the pipeline field
for old consumers. `receiver_build` contains the release and SHA-256 manifest
in every new session/result JSON and READY message.

From the repository root, verify an installation before a demo:

```sh
python3 ground/yamcs/build_identity.py --url http://192.168.1.251:8090 \
  --check ground/releases/yamcs-uhf-1.2.0.json
python3 ground/bpsk/identity.py --check ground/releases/receiver-2.2.0.json
python3 ground/bpsk/live.py --version
```

Run the receiver commands **on the host/copy used for reception**. `--version`
does not open the radio or require output arguments. The identity-only command
uses the standard library. A MATCH means exact audited content, not merely an
unchanged version label. Changed receiver files produce a different hash and a
nonzero check result; changing a version string alone cannot conceal drift.

The Yamcs manifest hashes the **loaded** `/ember` parameters, containers,
commands and algorithms returned by its MDB API, plus every dashboard/script
object in the shared `ember_displays` bucket. This includes LTE's display but
only the selected **ember-uhf** instance's definitions. It does not certify LTE
or USB instance definitions, Java binaries, Docker images, server configuration,
OS/runtime libraries, or flight firmware. Audit those separately when changing
the deployment. Receiver file identity includes live.py, modem.py, codec.py,
dictionary.json, VERSION and identity.py; the existing capture report also
pins the FPGA image. Python/UHD/NumPy versions are not part of that file hash.

Team members using the same server share those assets. Separate servers should
pass the same checked-in manifest. Ground-Build.opi is a dated audit snapshot,
not a live drift detector. Rerun `--check` after deployment, after manual edits,
and before the demo. Reload browser pages after asset changes. Its own page
and manifest are excluded from the asset hash to avoid circular fingerprints.

For an intentional new release: review and test the changes, increment the
component version, generate a new manifest (do not replace an old release),
compare it against the deployed installation, then commit the manifest and
source together. For example, use `--release 1.1.0 --output ...` for a new
Yamcs snapshot; `--publish` uploads only Ground-Build.opi and ground-build.json.
It does not replace the team's operational dashboards or definitions. Keep
release manifests in Git; the commit identifies the associated source revision.

## Validated CAN-addressing migration — October 17

Receiver 2.1.0 and Yamcs assets 1.1.0 are deployed and match their manifests.
The UHF MDB adds LTE_CAN_FIRMWARE and LTE_MODEM_FIRMWARE, with two corresponding
firmware dashboards and LTE-Firmware.par. The existing dashboards are unchanged.
The USB/LTE instance MDBs remain unchanged; the shared Java WireProfile was
rebuilt with the additive message definitions. Upstream Yamcs remains 5.13.0.

The 120-second receive session recovered and forwarded all six transmitted
packets: COMMS identity, both LTE identities, heartbeat, system status and EPS
POWER_STATUS. Every packet matched the COMMS transmit log and Yamcs archive
byte-for-byte; receiver errors were empty. Both LTE displays were visually
checked against the real RF observations (Feather 0.8.0, Walter 0.3.0, clean
source 9fcb020). RF was stopped with TX=0 and clock outputs verified disabled.
This is a bounded migration check, not a new long-duration reliability test.

Deployment reproduction: generate MDB and WireProfile.java with
`python3 ground/ember/generate_mdb.py /tmp/ember-mdb`. For the UHF instance,
copy ember.xml to ember-uhf.xml and retain POWER_STATUS's DefaultRateInStream
minimumValue=0.03333333333333333 (30-second expected interval); all other
containers remain generated unchanged. Install that UHF file and WireProfile,
restart/recompile Yamcs, and run install_displays.py. Preserve other instance
MDBs/configuration, archive volumes and previous release manifests. Back up
runtime sources and receiver files before deployment. Confirm --check against
both manifests after installation; publish Ground-Build only after that audit.

## Device discovery release

Receiver2.2.0 and Yamcs UHF assets1.2.0 add DEVICE_STATUS (53), Devices.opi,
Devices.par and two display scripts. IHU0.9.0 adds a registry snapshot as the
fourth packet of each explicit UHF run cycle; COMMS0.24.0 admits it. LTE Feather
remains on0.8.0 and Walter on0.3.0; no LTE reflash is needed for this downlink.
The expected snapshot interval is90 seconds; IHU's device STALE threshold is
30 seconds. These represent different ages: the ground snapshot can expire
independently of the IHU's last verified response from a particular device.

October 17 environment split: `yamcs-flight-20261017.json` audits flight `ember`;
`yamcs-bench-20261017.json` audits serial `ember-bench`. Earlier operational and
transport manifests are retained as dated history, not current fingerprints.
