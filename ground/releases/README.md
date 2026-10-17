# Ground release identities

Current baselines:

| Component | Version | Verification |
| --- | --- | --- |
| Yamcs upstream server | 5.13.0 | Running `/api` server version/revision |
| EMBER UHF definitions + shared dashboards | 1.0.0 | `yamcs-uhf-1.0.0.json` |
| Live UHF receiver | 2.0.0 | `receiver-2.0.0.json` |

These are separate from COMMS MCU firmware 0.22.0. Receiver 2.0.0 is the first
semantic release of pipeline v2, with content identity added; wire format and
DSP behavior are unchanged. `receiver_version: 2` remains the pipeline field
for old consumers. `receiver_build` contains the release and SHA-256 manifest
in every new session/result JSON and READY message.

From the repository root, verify an installation before a demo:

```sh
python3 ground/yamcs/build_identity.py --url http://192.168.1.251:8090 \
  --check ground/releases/yamcs-uhf-1.0.0.json
python3 ground/bpsk/identity.py --check ground/releases/receiver-2.0.0.json
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
