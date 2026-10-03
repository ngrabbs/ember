# SRB2 security initialization candidate

The baseline `srb2-security-before-20261002-02` logs SRB2 ADD and MODIFY with
security mode255 (the unchanged-state sentinel), security inactive, algorithms0
and no RRC security container. It later reaches SRB2 maximum retransmissions.
One real EPS packet was modem-accepted; none arrived at ground. The host trial
was interrupted before a final OFF sample; the user subsequently powered down
the bench. The bounded network processes both ended with exit124.
[Metadata and host evidence](../../../system/ground_station/evidence/srb2-security-20261002/report.json).

At RRC reconfiguration completion, this OAI source passes mode255 to PDCP,
even for newly added SRB2/DRB entities. New PDCP entities are zero-initialized;
the sentinel skips security setup instead of inheriting the established SRB1
security. This is a concrete initialization defect. It is not yet demonstrated
to explain every SRB2 failure, lost packet or ULSCH-pool assertion.

The tested [candidate](../patches/oai-new-bearer-security.patch) passes the
negotiated ciphering/integrity algorithms with the already-derived keys to
the existing PDCP configuration API. It does not reset PDCP sequence numbers,
disable security, change RF settings or suppress assertions. The candidate
target builds; the three existing MAC/PHY helper tests pass, but they do not
exercise PDCP security or qualify this correction.

## Corrected bench comparison

Both Feathers were restored to CAN normal mode after the power cycle. Fresh EPS
ADC operation was re-enabled and verified. Walter started OFF. Two new modem
and eNodeB/EPC windows each sent three real EPS packets, without retries:

| UTC label/date | Build | Accepted / received / Yamcs byte matches |
| --- | --- | --- |
| after-20261003-01 | Candidate plus temporary security/RLC traces | 3 / 3 / 3 |
| after-20261003-02 | Candidate, temporary traces removed | 3 / 3 / 3 |

These UTC runs occurred on October2 in America/Chicago. In the first corrected
run, at 00:41:27.257 UTC, SRB2 MODIFY requested mode32: ciphering algorithm0 and
integrity algorithm2. Security became active and the RRC security container
existed. At 00:41:27.374, its RLC entity returned STATUS ACK_SN1. This establishes
both the corrected security state and acknowledgment of the previously failing
SRB2 downlink. Neither corrected run logged signaling-bearer max retransmissions,
reestablishment requests or an assertion.

All six native128-byte packets byte-match the IHU source, ground receiver and
Yamcs archive. IHU boot979862082, sequences0–5; ADC/conversion-valid1. Receivers
reported zero rejects/duplicates. Cached diagnostics reported zero registration
losses during both windows. No additional IHU CAN/fragment/timeout errors were
recorded; the earlier failed HELLO while COMMS was in configuration mode remains
in cumulative counters and must not be erased from the evidence.

Both corrected trials confirmed Walter OFF/window0; network processes ended
at bounded deadlines with exit124. The Pi now retains the eight-candidate build
with no temporary traces. Its SHA-256 is
`5c5de8e17db509b35823f401b99c7fdbe28144307da0be24fbc777c569768e11`.
The RRC source matches the prepared candidate exactly. Reverse the eighth
candidate before the original seven when restoring the earlier baseline.
That seven-candidate binary SHA was
`13ab09bf176773e213dd02f950b96577c6369e9be54723e7a1db1281c14b6d8a`.

The target builds, three focused MAC/PHY helper tests and34 ground host tests
pass. The helper tests do not cover PDCP security; the radio comparison supplies
that bounded evidence. Six packets in two windows are not six independent
attach trials. Repeat the ten-run reliability series with this fixed build/profile
before adding queued telemetry. The separate ULSCH-pool issue and full PHY
simulation regression remain open; these successes do not establish flight,
continuous-operation or downlink-command qualification.

The subsequent fixed-build [ten-run series](2026-10-02-eps-security-reliability.md)
delivered9/10 packets;8/10 passed every check. All confirmed OFF. Registration
loss and a controller diagnostic query failure remain; recovery is not qualified.
