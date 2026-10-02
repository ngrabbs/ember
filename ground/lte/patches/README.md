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

## Msg4 retry candidate

`oai-lte-m-msg4-retry.patch` adds a bounded FDD CE-mode-A Msg4 retry path for
the bench's single MPDCCH/PDSCH/PUCCH repetition configuration. It preserves
the original MAC transport block and NDI, resends RV 0 for Chase combining,
waits for a valid Type2-common MPDCCH opportunity, and schedules PDSCH and
feedback again. The existing MAC limit allows four total transmissions.
Feedback is retained separately because MAC round 8 means either ACK or
exhausted retries; exhausted BL/CE attempts are released rather than configured
as successful. The new lifecycle helper is called by the production scheduler.

Apply after the Msg3 cleanup patch, from the OAI checkout:

```sh
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-msg4-retry.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-msg4-retry.patch
cmake --build build-lte --target lte-softmodem -j2
cmake -S openair2/LAYER2/MAC/tests -B build-emtc-tests -GNinja
cmake --build build-emtc-tests
ctest --test-dir build-emtc-tests --output-on-failure
```

Both patches are already applied on the Pi. Reverse the Msg4 patch before
reversing Msg3 when restoring the baseline. No upstream commits or pushes
were made.

The standalone CTest test calls the production action helper with 11 cases,
including ACK, NACK, DTX, waiting, and exhausted retries. It does not test PHY
decoding, encoded payload equivalence, or timing over RF. The bench recorded
a real Msg4 retry followed by ACK and RRCConnectionSetupComplete. A subsequent
trial reached accepted SIM authentication and NAS Security Mode Complete.
The exhaustion decision has unit coverage; its resource-release calls were not
unit-tested, and exhausted retries were not exercised over RF.

This remains an experimental candidate: all three radio trials aborted on
downlink-context exhaustion before Attach Complete. Neither CE-mode-B, TDD,
multiple repetitions, RV cycling, nor a complete telemetry bearer is validated.
See [Msg4 and authentication results](../results/2026-10-02-msg4-authentication.md).
