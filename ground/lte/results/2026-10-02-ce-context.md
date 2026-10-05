# Dedicated bearer and context trace — 2026-10-02

One bounded trial delivered a real, native EPS POWER_STATUS packet through
IHU → CAN → COMMS → Walter → LTE-M → LibreSDR/OAI → EPC → Yamcs. Sequence4,
IHU boot536364973, all128 bytes match both the ground receiver and Yamcs archive.
Battery8.026V, output8.009V, die21.873°C; current sense calibration remains
unverified. This is a diagnostic delivery after connection recovery, not a
repair or an extension of the original six-of-ten qualification result.
[Evidence](../../../system/ground_station/evidence/ce-context-20261002/report.json).

The temporary CE/context and RLC/HARQ metadata patches changed no scheduling
or RF parameters. The private profile changed MAC debug logging to info,
retaining RLC debug and the same RF settings. Logging can affect timing;
the successful delivery cannot establish a causal improvement.

## Failure ordering

All times are UTC ground-log collection times:

| Time | Event |
| --- | --- |
| 22:10:20.655 | Initial context d869: RRC reconfiguration complete; SRB2 active |
| 22:10:20.735 | SRB2 SN0 downlink:61-byte RLC PDU, MCS5,63-byte transport block |
| 22:10:21.108 | UE requests reestablishment, cause Other Failure |
| 22:10:21.631 | Initial context reaches SRB2 maximum retransmissions |
| 22:10:22.395 | Recovered context d781: reconfiguration complete |
| 22:10:22.633792 | Ground receiver obtains native128-byte EPS sequence4 |
| 22:10:22.634 | Yamcs eps-lte-in archives the identical packet |

Reestablishment precedes the SRB2 retry limit. In this trial, exhaustion is a
later symptom rather than the first observed indication of failure. The
generic Other Failure cause does not identify Walter's internal reason.
Do not label the retransmission limit itself as the root cause.

## Hypotheses tested

The SRB2 MAC build repeatedly reports offset2 + payload61 = TBS63, with one
short-padding byte and no post-padding. No observed MAC build exceeded its
transport block. The trace covers metadata, not full packet contents, so it
does not prove the MAC or RLC bytes are otherwise correct.

MCS5 and PHY TBS504 bits remain consistent in the failing interval. A HARQ
retry at frame303 retains NDI0 from frame301, with RV2 reflected in PHY; later
RLC retransmissions become new MAC transport blocks and toggle NDI. Thus the
previous MCS-retention bug is not reproduced here. The DLSCH nFAPI RV field is
zero while actual PHY RV follows MPDCCH; this local implementation uses that
DCI-derived value. Inspect the actual encoding path before treating the field
difference as a waveform defect.

SRB2 STATUS remains absent despite mixed HARQ feedback. The UE successfully
completed the initial RRC reconfiguration, so merely missing that completion
does not explain this failure. Next inspect SRB2 bearer activation/security,
uplink STATUS scheduling/decoding, and the post-reconfiguration PHY transition.

The uplink-pool assertion did not reproduce. `TRACE_UL_ALLOC` records HARQ
activation whenever no matching active mask exists; successful reception clears
that mask, allowing reuse. Its event count is not a count of leaked contexts.
Keep the pool-full owner dump available for a failed run; no cleanup repair or
pool-size increase is justified by this trial.

## Validation and restoration

The instrumented target built. After both network processes ended at their
deadlines, both metadata patches were reversed and the normal target rebuilt.
Its SHA-256 matches the saved pre-trace binary:
`13ab09bf176773e213dd02f950b96577c6369e9be54723e7a1db1281c14b6d8a`.
Both focused MAC helper tests and the PHY context helper test pass. These tests
do not qualify the waveform; the earlier full PHY simulation limit remains.
Walter confirmed OFF/window0; no eNodeB/EPC processes remain.

Raw upstream logs stay private on the Pi. Selected metadata, host diagnostics,
ground receipt and archive identifiers are committed separately from subscriber
records. The new [trace patch](../diagnostics/oai-ce-context-trace.patch) is
optional instrumentation, not an eighth production candidate.
