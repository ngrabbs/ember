# Offline review of the zero-resource-block crash

2026-10-20 UTC / October 19 local. Saved 5 packet/s crash and working 2 packet/s
logs, plus snapshots of the unchanged ground source. **No new RF, build, flash
or running-source change.**

The failed log contains a second RRC setup completion at 00:32:58.262 UTC while
the old context is still present. Both contexts are being scheduled before the
assertion at 00:32:58.484. The working reference has one setup-complete context
and ends with cleanup after commanded OFF. Contexts are software identities;
this does not establish that two physical UEs were transmitting.

## Defect found

`eNB_scheduler_dlsch.c` selects `dl_config_pdu` before its UE loop (line1218).
The dedicated LTE-M MPDCCH branch clears/writes through that pointer and
increments `number_pdu` (lines1695–1743), but does not refresh the pointer for
the next qualifying UE. Two control-message appends therefore overwrite the
same record while counting two. The DLSCH branch separately refreshes its pointer.

With a zero-initialized counted hole, NFAPI record type0 means legacy DCI and
format0 means Format1. Its zero allocation reaches `conv_nprb()` and produces
zero resource blocks, matching the assertion path. A stale nonzero hole may
behave differently; the live PDU slots and converter inputs were not logged.
This is a demonstrated bookkeeping defect and a strong crash explanation,
**not a confirmed reconstruction of the runtime crash**.

## Offline checks

A reduced C fixture uses the captured real NFAPI structures and an unchanged
extraction of `conv_nprb()`. It exercises the slot/count lifecycle, not the full
scheduler, UE eligibility, RLC, or RF. Built with `-Wall -Wextra -Werror` and
AddressSanitizer/UndefinedBehaviorSanitizer; ten cases pass. `MAX_NUM_CCs=1` is
only a fixture header dependency, not the live build configuration.

| Case, at empty list and after three existing records | Original pointer | Refreshed pointer |
| --- | --- | --- |
| One context, zeroed slots | One valid control record | Not exercised |
| Two contexts, zeroed slots | One overwritten control record and one zero legacy-DCI hole; NPRB0 | Two control records |
| Two contexts, stale nonzero next slot | One overwritten record and a counted stale record | Two control records |

The fixture evaluates the refreshed two-context cases; the single-context
control case exercises the original path. No sanitizer findings.

[Candidate patch](../patches/oai-lte-m-mpdcch-append-slot.patch) adds a current-slot
lookup immediately before the MPDCCH write. It is saved for review, **not applied
or compiled as a full radio**. `git apply --check` passed against the captured
overlay source. The assertion is retained.

The missing uplink packets began before this crash/new context. This finding
does not explain all 38 missing packets, earlier registration losses, or establish
a common cause. Best measured direct goodput stays **7.7824 kbps**.

Fresh ground integrity checks passed 10/10; cell/core remain stopped. Walter was
left OFF by the preceding test. Production firmware unchanged. Source snapshots,
fixture and raw logs remain private under `.runtime/throughput/crash-analysis-20261020/`;
selected evidence is in lab-log 005.

Next: build/check the candidate in an isolated ground source copy preserving the
existing overlay and original binary. RF comparison follows only after that
preparation; no more blind rate repeats.
