# Optional RLC/HARQ metadata trace

`oai-rlc-status-trace.patch` is temporary instrumentation relative to the pinned
OAI revision with all seven [production candidates](../patches/README.md)
applied. It records RLC entity/bearer mapping, PDU lengths, retransmission state,
decoded STATUS fields, and compact CE downlink HARQ feedback. It does not print
PDU payloads. Normal OAI debug logs can still contain subscriber identities and
authentication material; keep full logs private.

The Pi currently runs the restored, uninstrumented build. To reproduce tracing,
copy this patch to the Pi's work directory and run from the OAI source checkout:

```sh
git apply --check ../oai-rlc-status-trace.patch
git apply ../oai-rlc-status-trace.patch
cmake --build build-lte --target lte-softmodem -j3
```

Stage the desired config example from `../configs/oai/` in the Pi's runtime
configs directory, omitting `.example` from its filename. Use the existing
bounded [bring-up procedure](../BRINGUP.md) with
`enb.band13.emtc.ce300tx20rlctrace.conf` (RX gain 35) or
`enb.band13.emtc.ce300tx20rx25rlctrace.conf` (RX gain 25). Both use TX gain 69.75,
MAC info logging, and RLC/RRC debug logging. These are diagnostic profiles;
receiver gain and radiated power have not been calibrated.

Feedback values in this source are 1 ACK, 2 NACK, and 4 DTX. Separate Msg4 from
dedicated-bearer events before interpreting counts. The ordinary RA summarizer
cannot count its debug-only DTX lines with MAC info logging. STATUS fields are
logged before complete consistency validation; check subsequent state/SDU
delivery. Entity pointers may be reused after a context is removed.

After confirming Walter CFUN 0 and both network processes stopped, remove the
instrumentation and rebuild before normal tests:

```sh
git apply --reverse --check ../oai-rlc-status-trace.patch
git apply --reverse ../oai-rlc-status-trace.patch
git diff --check
cmake --build build-lte --target lte-softmodem -j3
```

This leaves all seven production candidates applied. Do not discard unrelated
source changes with `git reset` or `git checkout`. See the
[recorded results](../results/2026-10-02-rlc-status.md) for tested limits and the
remaining failure checkpoint.
