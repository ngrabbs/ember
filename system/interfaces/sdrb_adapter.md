# SDRB integration boundary

Draft bench interface, October 3, 2026. SDRB remains an AMSAT system; EMBER
uses an optional adapter without changing its normal startup or radio flows.
[Work checklist](../sdrb/TODO.md) · [CAN transport](../../firmware/can_feather_bench/README.md)

## Ownership

EMBER owns telemetry meanings, the packet dictionary, spacecraft modes, transmit
permissions, scheduling, and its adapter. SDRB owns its drivers, FPGA, UHD and
radio applications. Reusable SDRB improvements should be developed and reviewed
separately from EMBER-specific code. No EMBER protocol belongs in SDRB core code
merely because SDRB is the temporary radio.

The intended path is IHU → existing EMBER CAN transport → optional adapter →
generic SDRB packet interface → RF → ground decoder → original EMBER packet.
The initial implementation ends at durable local recording and a CAN response.
It starts no radio, service, modem or automatic transmitter.

## Existing transport reused

`ground/ember/sdrb_can.py` is an opt-in, standard-library Linux SocketCAN service
in the EMBER repository. It uses the existing bench IDs `0x710` and `0x711`,
fragment rules, COBS envelope and CRC without changing either Feather image.
These debug IDs are not AMSAT flight CAN allocations. The default is a monitor
that sends no application replies and may observe the existing IHU–COMMS bus.
`--respond` enables the responder; use it only when the existing COMMS responder
is absent. The direct response test substitutes SDRB for COMMS on the bench bus.
Monitor mode does not set controller-level listen-only mode; a normally configured
CAN controller can still acknowledge valid frames at the link layer.
The installed Xilinx PS CAN driver was checked during the October 3 boot test
and rejects listen-only mode with `Operation not supported`. Confirm H7/L8
orientation before bringing CAN1 up in normal mode; suppress application replies
with the adapter default. Do not claim electrical passivity from monitor mode.

HELLO establishes the IHU boot identity. Diagnostic ECHO remains opaque.
CHAIN accepts only valid HEARTBEAT or POWER_STATUS packets with matching IHU
boot/source identity and ground destination. The service validates both CRCs,
records the exact original packet with decoded fields, flushes and fsyncs the
log, then in responder mode returns CHAIN_ACK with the exact bytes and correlated
request identity. Monitor mode suppresses every application reply. Begin observing
before the IHU sends HELLO so the adapter can establish the producer session.
Unsupported requests, including LTE and RF control, receive explicit errors.
Storage failure reports unknown outcome; no successful admission is claimed.

**CHAIN_ACK means validated and recorded locally.** The unchanged IHU currently
prints `WALTER_BENCH_RETURN` for that response type. During this test that legacy
label does not imply Walter participated or that RF occurred; the SDRB packet
log identifies the actual route. A dedicated radio-admission result is later work.

One incoming assembly is supported with a 500 ms gap limit and 263-byte wire
bound. Responses are paced at 2 ms per fragment. Up to 32 completed request
responses are cached per peer boot; exact duplicates return the cached response
without another record, while conflicting reuse is rejected. This bounded cache
is not persistent exactly-once delivery; old evicted requests can be recorded
again. A peer change clears it and requires HELLO. Boot identity is session
correlation, not authentication.

The adapter never configures CAN interfaces. Its advisory lock prevents another
instance of this adapter under the same account/interface; it cannot exclude
unrelated CAN clients. Use a new evidence directory per run and a maximum
120-second run. Baseline interface state and error counters must be captured
before and after physical testing.

## Radio interface still to implement

The existing SDRB telemetry demo accepts 1–128 UTF-8 bytes; the real EMBER
POWER_STATUS packet is 128 binary bytes. Arbitrary packet bytes are not valid
UTF-8, and hex expansion exceeds the demo limit. Do not silently reinterpret
them as text or change the existing text API.

Add a separate opt-in binary packet submission operation, or a separate packet
application, with explicit bounds, queue responses and preserved text behavior.
Keep EMBER fields opaque on the SDRB side. RF framing and the ground decoder must
recover the exact EMBER bytes before the established codec/Yamcs path is used.
Queue acceptance, samples passed to a sink, and ground decode are separate
observations; none substitutes for another.

## Software verification and coordinated bench procedure

From the repository root, run:

```sh
python3 -m unittest discover -s tests/ground -p test_sdrb_can.py -v
```

The tests compare the Python envelope/fragments with the actual C firmware
headers for all 1–240-byte payload lengths. A saved hardware EPS packet is
replayed with byte preservation and checked for 7.995 V battery voltage and
−88.986 mA current. Tests cover fragment loss/duplicates/timeouts, session
reset, request conflict, CRC/producer rejection and storage failure. This proves
software interoperability; it does not prove the physical SDRB link.

After coordinating power, wiring, interface ownership and termination, prepare
SDRB CAN1 at the existing 500 kbit/s setting using the SDRB runbook. No wiring
changes are permitted while powered or backfed. With CAN1 already configured:

```sh
python3 ground/ember/sdrb_can.py --interface can1 --seconds 60 --output /path/to/new/run
```

On the IHU console, check role/status and pending work, then use `normal`,
`hello`, and one `eps telemetry`. Match the returned bytes and correlated
request to `packets.jsonl`; confirm no CAN errors and no RF flow. In default
monitor mode COMMS handles the response and SDRB only records the request.
For a separately coordinated direct IHU–SDRB response check, remove the competing
COMMS responder and add `--respond` to the adapter command. Stop the
adapter, restore the prior CAN state, and verify SDRB's established test path.
Do not run the existing multi-board `can_chain.py` as this one-packet test: its
scope and expected counters include a different route.

## Source reference captured during implementation

Reviewed SDRB candidate checkout:
`/media/ngrabbs/BACKUP-A/sdrb-can-20260917/source-checkout` on m75q,
branch `can-dual-20260917`, HEAD `543d3f6d77d278e19badd728d8e32d6f974b2586`.
The read working files remain relevant independently of that HEAD; no claim is
made that it identifies the running board image. Reviewed telemetry client
SHA-256: `d2a984e533744dbdbdcc44009477a976b941ad2cd577fd0c2d5e5d7b9e78cd0b`;
overlay implementation: `614d17560f385621c81e3edb38677d5a4d6dcd03de21c8c2a1fcb6e39ab448a5`.
No SDRB source or board configuration was changed for this software milestone.
