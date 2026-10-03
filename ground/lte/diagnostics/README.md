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

## Dedicated CE scheduler and uplink context trace

`oai-ce-context-trace.patch` adds metadata for MAC SDU sizes/header offsets,
MPDCCH MCS/NDI/RV, PDSCH sizes and scheduled feedback time, the corresponding
PHY HARQ parameters, uplink HARQ activation, and pool ownership on exhaustion.
It leaves scheduling, cleanup and assertions unchanged. No payload bytes are
logged. `TRACE_UL_ALLOC` means activation when no matching **active HARQ mask**
exists; it does not imply allocation of new memory or a new persistent UE.

Apply both optional patches after the seven candidates and rebuild:

```sh
git apply --check ../oai-ce-context-trace.patch
git apply ../oai-ce-context-trace.patch
git apply --check ../oai-rlc-status-trace.patch
git apply ../oai-rlc-status-trace.patch
cmake --build build-lte --target lte-softmodem -j3
```

The recorded context trial clones the existing RX35 RLC-debug profile, changing
only MAC debug to info to reduce general logging. Targeted CE/context metadata
uses info logging; the older RLC metadata needs RLC debug. Keep PHY at its normal
logging level. Raw upstream logs remain private.

After the bounded run and confirmed modem OFF, reverse the RLC trace and then
the CE/context trace, rebuild, and compare the binary with the saved baseline.
The [context results](../results/2026-10-02-ce-context.md) record this restoration.

## PDCP security state trace

`oai-pdcp-security-trace.patch` logs ADD/MODIFY requests and the resulting bearer
security state: RNTI, SRB/DRB flag, bearer ID, action, requested mode, algorithm
IDs, activation flag and whether the RRC security container exists. It does not
log keys, key hashes, payloads or security-container addresses. Apply after the
production candidates and rebuild; it can be combined with the RLC trace.
Reverse the optional trace and rebuild after the bounded comparison. Full
upstream logs still belong in private storage.

Mode255 is the existing API's "leave security unchanged" sentinel. A newly
allocated PDCP entity starts with inactive security. A missing container alone
does not prove incorrect security when negotiated algorithms are null; correlate
with the selected algorithms, activation state and RRC stage.
