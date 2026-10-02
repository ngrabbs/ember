# Experimental OAI patches

Base: `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`.
Pi source branch: `ember/lte-m-msg3-cleanup`. Source changes are preserved here
as cumulative patches; EMBER does not vendor the OAI checkout.
Current Pi state has all seven applied, in this order: Msg3 cleanup, Msg4 retry,
single-transmission RAR release, rejection lifecycle, CCCH wait, uplink HARQ selection,
and dedicated downlink retry MCS retention. Reverse
in the opposite order and rebuild to restore the baseline. No upstream commits,
pushes, or PRs were made.

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

Apply or reverse these only as part of the ordered set described above.

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

## Single-transmission CE-A RAR release candidate

`oai-lte-m-rar-release.patch` adds a per-HARQ one-shot flag when MPDCCH
explicitly identifies an RA-RNTI, CE mode A, and one PDSCH transmission.
After scrambling and modulation map that PDSCH, the production release helper
clears only its HARQ bit and consumes the flag. The context can then be reused.
UE MPDCCH assignments and ordinary LTE DCI clear the flag and retain their
existing feedback lifecycle. Classification uses nFAPI RNTI type, not a numeric
RNTI range, which could overlap UE identifiers. Repetitions and CE mode B are
outside this candidate's release scope.

Apply after the two MAC patches:

```sh
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-rar-release.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-rar-release.patch
cmake --build build-lte --target lte-softmodem -j2
cmake -S openair1/PHY/LTE_TRANSPORT/tests -B build-emtc-phy-tests -GNinja
cmake --build build-emtc-phy-tests
ctest --test-dir build-emtc-phy-tests --output-on-failure
cmake -S . -B build-lte -GNinja -DENABLE_PHYSIM_TESTS=ON
cmake --build build-lte --target dlsim -j2
ctest --test-dir build-lte -R '^physim.4g.dlsim.basic.test1$' --output-on-failure --timeout 180
# A shorter smoke check uses the same simulator with 50 rather than 1,500 frames:
(cd build-lte && timeout 60 ./dlsim -m=5 -g=F -s=-1 -w=1.0 -f=.2 -n=50 -B=50 -c=2 -z=2 -Tperf=60)
```

The release unit test calls the production helper and checks one-shot release,
consuming the flag, retaining UE HARQ, and preserving a different active HARQ
bit. It does not exercise waveform generation or MPDCCH classification.
All three patches apply sequentially to the pinned base. Temporary pool-owner
trace logging was removed before saving this patch. The eight-slot pool size
was not increased. See the RAR release bench record for observed behavior.

PHY regression remains unresolved: the standard 1,500-frame downlink CTest
hit the 180-second limit on the Pi. A reduced 50-frame run returned exit 255
with zero throughput; a 10-frame high-SNR check also returned exit 255.
Repeating that high-SNR check with the pinned, unmodified PDSCH routine
(the other candidate files and descriptor layout retained) produced the same
zero-throughput result. This isolates the release hook from that failure, but
is not a full unmodified-source comparison or a passing PHY regression.

## Reestablishment rejection lifecycle candidate

`oai-lte-m-reject-lifecycle.patch` applies after the three candidates above.
On a BL/CE Msg4 ACK, an active reestablishment-rejection timer means the
context remains unconfigured. The RA procedure completes and the existing
rejection timer handles resource release. This prevents rejected contexts from
being scheduled as established UEs without dedicated PHY configuration.
It does not repair the original UE's radio-link failure or implement successful
reestablishment. No standalone unit test covers this guard.

```sh
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-reject-lifecycle.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-reject-lifecycle.patch
cmake --build build-lte --target lte-softmodem -j2
```

See [RAR release results](../results/2026-10-02-rar-release.md)
for live observations and the unresolved simulator regression.

## Asynchronous first CCCH response candidate

`oai-lte-m-ccch-wait.patch` applies after the four candidates above. If RRC
has not provided the first Msg4 CCCH SDU, MAC waits for another valid MPDCCH
opportunity. After ten unsuccessful opportunities it releases the temporary
UE and cancels RA. A retry with an existing SDU still reuses its stored payload.
This follows the ordinary LTE path's bounded-wait policy, counting eMTC
MPDCCH opportunities rather than every subframe. No standalone unit test covers
the asynchronous RRC task or timeout release calls.

```sh
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-ccch-wait.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-ccch-wait.patch
cmake --build build-lte --target lte-softmodem -j2
```

These first five candidates apply sequentially to the pinned base. Reverse
CCCH wait before restoring the earlier four; reverse the sixth candidate below first.

## BL/CE uplink receive HARQ selection candidate

`oai-lte-m-ul-harq.patch` applies after the five candidates above. The dedicated
BL/CE scheduler and PHY receive path select HARQ process 0. MAC `rx_sdu`
previously recomputed the ordinary LTE process from frame/subframe, updating
processes 1 or 5 in the bench logs. It now uses process 0 when the UE template
identifies BL/CE, preserving legacy selection for ordinary LTE and the existing
unknown-UE/Msg3 path. This matches the current single-process implementation;
it does not implement multiple LTE-M HARQ processes or repetition support.

```sh
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-ul-harq.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-ul-harq.patch
cmake --build build-lte --target lte-softmodem -j3
cmake -S openair2/LAYER2/MAC/tests -B build-mac-tests -GNinja
cmake --build build-mac-tests
ctest --test-dir build-mac-tests --output-on-failure
```

Both registered MAC tests completed successfully. The new test calls the
production selector across all eight legacy process indices and four nonzero
CE resource types, with assertions enabled. It does not exercise the entire
receive callback or waveform. A bounded radio trial delivered ten numbered UDP
packets through GTP-U and SGi after a Service Request restored the bearer.
Initial context release and later uplink failure still occurred. This is the
first telemetry demonstration, not a stable-link qualification or proof that
this patch alone accounts for the improvement. All six patches reverse and
reapply in order. See [uplink and telemetry results](../results/2026-10-02-uplink-telemetry.md).

## Dedicated BL/CE downlink retry MCS retention candidate

`oai-lte-m-dl-retry-mcs.patch` applies after the six candidates above. At entry
to each UE's dedicated BL/CE scheduling path, load the saved HARQ-process MCS.
New transmissions still calculate their MCS from payload size. Previously the
function's local MCS started at zero and was not restored for retransmissions,
then overwrote the saved MCS and changed the PDSCH transport-block length.
This two-line change preserves the existing payload, NDI, and RV handling.

```sh
git apply --check /path/to/EMBER/ground/lte/patches/oai-lte-m-dl-retry-mcs.patch
git apply /path/to/EMBER/ground/lte/patches/oai-lte-m-dl-retry-mcs.patch
cmake --build build-lte --target lte-softmodem -j3
```

The target rebuilt and the incremental patch applied after the reconstructed
six-patch source. There is no new scheduler unit test covering MCS/TBS retention.
A bounded RF trial still reached SRB2 maximum retransmissions and released its
context. This is a code correction candidate, not a demonstrated stability fix.
All seven patches reverse/reapply in order and the 16 affected reconstructed
files match the Pi source.
See [repeatability and release trace](../results/2026-10-02-repeatability-release.md).
