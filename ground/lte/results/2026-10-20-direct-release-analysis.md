# Direct Walter removal analysis — 2026-10-20 UTC

Offline comparison of the saved 512-byte 1 packet/s pass and 2 packet/s failure.
No new RF run, firmware build, flash or radio-setting change.

Both sessions completed authentication, attach and bearer setup. Compare the
same 1.216-second interval after RRC reconfiguration, ending at the failed
session's tunnel deletion. Scheduled-uplink events match the attached UE's
RNTI and UE_id 0; random-access events are excluded.

| Saved observation | Working 1 packet/s | Failed 2 packet/s |
| --- | --- | --- |
| Scheduled-uplink decode log events, OK / error | 48 / 12 | 2 / 58 |
| Last pending LCID 2 buffer report after setup | 0.136 s | 1.215 s |
| First tunnel deletion after setup | 45.541 s | 1.216 s |
| Release request in log | Yes, after host-confirmed OFF | None recorded |
| UDP packets delivered in original run | 10 | 0 |

These are decoder/buffer log events, not UDP packet counts or calibrated RF
measurements. LCID 2 corresponds to signaling bearer 2 in this setup. The source
logs buffer status only when nonempty; no direct empty-buffer observation is
claimed for the working run.

The source contains a matching cleanup route: signaling retry exhaustion sends
an unsuccessful RLC indication; RRC sets release flag 4, sends release complete,
deletes the tunnel and expires the cleanup timer. The timer message is the end
of this path; it does not by itself identify the original trigger.

**Strong lead:** signaling retransmission exhaustion following poor scheduled
uplink decoding. Pending LCID 2 makes SRB2 a candidate. Neither the exact bearer
nor the initiating callback was captured: RLC/RRC were at info level, while the
max-retry/failure messages are debug-level. No confirmed root cause or fix.
The lack of individual UTC timestamps on USB responses also prevents a precise
network-versus-modem-reset ordering claim.

Source checked at OAI commit `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`, with the
existing local overlay unchanged. Function paths/hashes and selected observations
are recorded in lab-log entry 005; original raw logs remain private and unchanged.
Private analysis: `.runtime/throughput/direct-release-analysis-20261020/`.

Next diagnostic, when RF work resumes: use the existing RLC/RRC debug-only profile
and timestamp each USB modem event. Identify which SRB reaches its retry limit
and align it with registration loss. No firmware build or cable move is needed.
No new RF test was performed here. Higher-rate sweep remains paused.
