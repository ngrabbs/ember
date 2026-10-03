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

The prepared [candidate](../patches/oai-new-bearer-security.patch) passes the
negotiated ciphering/integrity algorithms with the already-derived keys to
the existing PDCP configuration API. It does not reset PDCP sequence numbers,
disable security, change RF settings or suppress assertions. The candidate
target builds; the three existing MAC/PHY helper tests pass, but they do not
exercise PDCP security or qualify this correction.

Corrected RF validation is pending restoration of normal CAN mode on both
Feathers after the power cycle. The Pi currently has this candidate plus the
temporary PDCP-security and RLC traces applied; no radio processes are running.
Do not label this build as a qualified or normal baseline. Preserve the original
seven candidates when reversing this candidate or either optional trace.
The expected seven-candidate baseline SHA remains
`13ab09bf176773e213dd02f950b96577c6369e9be54723e7a1db1281c14b6d8a`.

Next, confirm SRB2 security activation and negotiated algorithms on hardware,
observe STATUS/reestablishment behavior, byte-match real EPS delivery in Yamcs,
then remove temporary traces and rerun independent reliability windows.
