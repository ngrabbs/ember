# Command and telemetry coordination with Dustin

[Ground station checklist](TODO.md) · [Operations definitions](../../docs/architecture/operations/Ground_Operations_Command_Telemetry/README.md)

Merged baseline: `ebeec2f` (PRs #2, #3 and #4). Adopt Draft 0.2's message
categories, command names, preliminary IDs, onboard validation authority,
transport/acceptance/completion distinction, timeout-as-unknown policy, and
independent autonomous telemetry/event flow. No final wire format is implied.

## Bench proposal now available

Review the [bench v1 contract](../protocols/ember_bench_v1.md) and
[JSON dictionary](../../ground/ember/dictionary.json). Existing application
IDs are preserved; parameter/stage/reason/endpoint numeric values and
TELEMETRY_PERIOD limits are new lab proposals. Please confirm these semantics
and correlated result rules, or identify corrections before firmware adoption.
Only the host codec is implemented so far; the live Yamcs example is unchanged.

## Request for Dustin

Please finish the following operations definitions so we can implement the
same dictionary in the ground console and spacecraft:

1. **Repair the incomplete documents.** Eight documents end in an unclosed
   code block: overview, command dictionary, command responses, telemetry
   dictionary, console, test, interfaces, and folder README. Recover omitted
   content where appropriate, especially the NACK reason-code table from Draft
   0.1. Ensure the short documents agree with `09-command-telemetry-protocol.md`.
2. **Define a small bench subset.** Start with `PING` (`0x01`), `REQUEST_STATUS`
   (`0x02`), `REQUEST_TELEMETRY` (`0x03`), and `SET_PARAMETER` (`0x30`). Define a
   `TELEMETRY_PERIOD` parameter, its units, permitted range, default, applicable
   telemetry group, and whether it survives reset. Confirm expected responses
   and GROUND TEST/mode permissions. Keep the remaining flight command set draft.
3. **Specify command outcomes.** Define fields for acceptance, rejection,
   successful completion, and known execution failure after acceptance, including
   reason codes. Require command-result/requested-data correlation to the
   originating transaction. An autonomous event or matching periodic value alone
   should not be mistaken for proof that a particular command executed.
4. **Define transaction and event identity behavior.** Specify what happens
   after a duplicate, delayed response, sequence rollover, ground restart and
   spacecraft restart. Distinguish a message type ID from an event occurrence
   ID. Define event retention, overflow policy, priority, and what evidence
   confirms delivery before an important stored event may be discarded. Exact
   numeric sizes/timeouts can be proposed jointly with firmware/comms.
5. **Finish the bench acceptance cases.** Expand GO-01/02/04/05/06/13/14/15/16
   with expected correlated results. Add an accepted command with an execution
   error, simultaneous periodic and requested telemetry, a delayed old response,
   and a simulated autonomous event generated while the ground link is down.

These are the requested deliverables, not an instruction to implement our SDR
modem or choose a new console framework. This note has not been sent to Dustin.

## Shared decisions with firmware and communications

We should settle these together, rather than assign the complete packet format
to one subsystem:

- Versioned binary schema: field types/widths, byte order, units/conversions,
  payload limits and error validation; source/target and message categories must
  disambiguate overlapping command/telemetry IDs.
- CCSDS SPP envelope/APIDs, transaction identifier placement, timestamp and time
  quality, and whether we use a tailored ECSS PUS subset. Keep packet sequence
  counters distinct from transaction and event identities.
- Uplink authorization/replay behavior and its lab exercise.
- USB bridge handoff, radio framing/CRC/FEC, and UHF BPSK profile. These remain
  outside the operations dictionary's RF-independent message meanings.
- Yamcs MDB and flight encoder/parser generated or checked against one shared
  machine-readable schema, with known byte vectors; eventual SatNOGS decoding
  must use the same engineering conversions.

The restored `firmware/shared/comms_hk_proto.h` provides real internal bench
health fields for `COMM_STATUS`; its I2C register map is not the RF packet format.
Do not copy its little-endian register layout into an unspecified CCSDS envelope.
