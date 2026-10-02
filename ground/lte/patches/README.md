# Experimental OAI patches

Base: `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`.
Pi source branch: `ember/lte-m-msg3-cleanup`. Source changes are preserved here
as a patch; EMBER does not vendor the OAI checkout.

`oai-lte-m-msg3-cleanup.patch` queues the temporary UE for the existing release
mechanism when OAI abandons an unsuccessful BL/CE Msg3. Previously that branch
only canceled MAC random access, leaving its PHY ULSCH context allocated.
The ordinary LTE maximum-retry branch already uses this release mechanism.
The patch does not add Msg3 retransmission or Msg4 retransmission support.

Apply from an unmodified pinned OAI checkout:

```sh
git switch -c ember/lte-m-msg3-cleanup
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-msg3-cleanup.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-msg3-cleanup.patch
cmake --build build-lte --target lte-softmodem -j2
```

Use `git apply --reverse` to remove the patch and rebuild before comparing
the baseline. Do not apply twice to the Pi: it is already applied there.

Validation: target rebuild and whitespace check completed; live bench logs
exercise the modified production path. Baseline MAC-debug run exhausted ULSCH
after eight BR responses with no BR contexts released. Patched run produced
11 responses and released ten BR contexts before encountering the separate
Msg4 retransmission assertion. This is limited bench evidence, not a long
duration regression or an LTE-M attach. The current minimal build registers
zero CTest tests; no automated unit-test coverage is claimed.

See [controlled results](../results/2026-10-02-walter-control.md).
