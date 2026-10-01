# EMBER bench packet dictionary v1

Status: **implemented host codec; proposed lab contract, not a flight freeze**.
The [JSON dictionary](../../ground/ember/dictionary.json) is the source for IDs,
field types, enum values and units. Dustin's merged operations documents own
application meanings; this subset preserves their command and telemetry IDs.
New numeric parameter, stage, endpoint and reason values here need his review.
The codec does not dispatch commands, authenticate uplink, or change firmware.

## Envelope

Use a six-byte [CCSDS Space Packet Protocol primary header](https://ccsds.org/Pubs/133x0b2e2.pdf):
version 0, type 1 for commands and 0 for all downlink, secondary header flag 1,
bench APID `0x100` for commands and `0x101` for downlink. Sequence flags are
`11` (unsegmented). A per-source, per-APID 14-bit sequence increments modulo
16384 for each transmitted packet, including a retransmission. Packet data
length is the total packet byte count minus seven. APIDs are local bench
assignments, pending flight allocation.

All multibyte fields are big endian, packed without padding. The secondary
header follows the primary header:

| Byte offset | Field | Type |
|---|---|---|
| 6 | schema_version (1) | u8 |
| 7 | kind: command 0, telemetry 1, response 2 | u8 |
| 8 | message_id | u16 |
| 10 | source | u8 |
| 11 | target | u8 |
| 12 | transaction_epoch | u32 |
| 16 | transaction_id | u32 |
| 20 | source_boot_id | u32 |
| 24 | uptime_ms | u32 |
| 28 | payload_length | u16 |
| 30 | payload in dictionary field order | variable |
| final 2 | CRC-16/CCITT-FALSE | u16 |

CRC covers every preceding byte, including the primary header: polynomial
`0x1021`, initial value `0xffff`, no reflection, xorout 0; `123456789` gives
`0x29b1`. Minimum packet length is 32 bytes; maximum is 240, leaving at most
208 payload bytes. A four-byte RadioHead wrapper is outside this packet and
CRC. Verify the actual driver/buffer limit before RF integration. Serial
framing, RF framing/FEC and authentication are separate layers.

Endpoint values: ground 1, IHU 2, comms 3, payload 4. Bench commands go ground
to IHU; IHU is the command acceptance and result authority. Downlink targets
ground. `source_boot_id` is a nonzero identifier changed on source restart.
`uptime_ms` is elapsed source uptime modulo 2^32; it wraps after about 49.7
days. It is not UTC. Archive ground reception time separately. Boot identity
and packet sequence help detect resets/gaps, but do not provide authentication
or replay protection. Unique, persistent identity and absolute time remain
flight decisions.

## Implemented dictionary subset

| Kind | ID | Name | Payload in wire order |
|---|---|---|---|
| command | 0x01 | PING | empty |
| command | 0x02 | REQUEST_STATUS | empty |
| command | 0x03 | REQUEST_TELEMETRY | data_group:u8 |
| command | 0x30 | SET_PARAMETER | parameter_id:u16, value:u32 |
| telemetry | 0x01 | SYSTEM_STATUS | mode:u8, configuration:u8, telemetry_period_ms:u32, accepted_commands:u32, rejected_commands:u32 |
| telemetry | 0x05 | HEARTBEAT | mode:u8, configuration:u8, telemetry_period_ms:u32 |
| telemetry | 0x30 | COMM_STATUS | rx_packets:u32, tx_packets:u32, crc_errors:u32, dropped_packets:u32, rssi_dbm:i16 |
| response | 0x31 | COMMAND_RESPONSE | command_id:u16, stage:u8, reason:u16, parameter_id:u16, value:u32 |

IDs are scoped by kind: command `0x01` is not telemetry `0x01`.
All counters are unsigned, wrap modulo 2^32 and reset at source boot. RSSI
is integer dBm; `-32768` means unavailable (e.g. USB), not a measurement.
No power or thermal values are fabricated by this subset.

`TELEMETRY_PERIOD` parameter 1 is milliseconds, inclusive range 100–60000,
default 1000 at boot, nonpersistent. For this bench it controls periodic
HEARTBEAT, SYSTEM_STATUS and COMM_STATUS publication. An immediate requested
report does not restart periodic scheduling. `REQUEST_STATUS` returns
SYSTEM_STATUS; `REQUEST_TELEMETRY` group 1 returns SYSTEM_STATUS, group 48
returns COMM_STATUS. PING returns acceptance then completion without data.
SET_PARAMETER is available only on the explicitly configured GROUND_TEST
bench endpoint. Mode and interlock policy for flight is still Dustin's work.

## Transactions and results (endpoint implementation pending)

Ground allocates a nonzero session `transaction_epoch` and monotonically
increasing nonzero `transaction_id`. Start a new epoch on session restart
or ID exhaustion; do not reuse a live epoch. Commands and every associated
response/requested telemetry echo both values. Unsolicited telemetry uses
both zero. Ground's boot ID can be its session epoch. Lab random 32-bit
identifiers can collide; a production identity scheme is still required.

Result stages: ACCEPTED 0, REJECTED 1, COMPLETED 2, EXECUTION_FAILED 3.
ACCEPTED means queued/authorized, not executed. A rejected command gets one
terminal REJECTED result. An accepted command gets a terminal COMPLETED or
EXECUTION_FAILED result. SET_PARAMETER completion reports parameter 1 and
the applied value; other results use parameter/value zero. Query completion
follows generation/queueing of its correlated telemetry; it does not prove
ground received that telemetry. The UI verifies correlated data separately.

Reason 0 is success; 1–7 preserve the earlier proposed unknown-command,
invalid-parameter, mode, interlock, busy, fault and unavailable meanings.
This bench adds 8 EXECUTION_ERROR and 9 TRANSACTION_CONFLICT. REJECTED and
EXECUTION_FAILED require a nonzero reason; ACCEPTED and COMPLETED require 0.
These cross-field rules belong in the dispatcher, not just packet decoding.

Bench timeout proposal: 5 s for acceptance, 10 s from acceptance for terminal
result. A timeout means **unknown outcome**, never rejection or execution
failure. No automatic retries. Check status before manually resending a
state-changing command. A retry preserves transaction identity and semantic
command contents; packet sequence/uptime/CRC may change.

Proposed endpoint cache: retain the last 64 transactions during a boot,
keyed by ground source, epoch and ID. Exact command/target/arguments repeats
return cached outcomes without executing again; changed contents with the
same identity return TRANSACTION_CONFLICT. Cache eviction or endpoint reset
can lose duplicate protection: old transactions must not be retried across
those boundaries. Ground invalidates outstanding transactions on a new IHU
boot ID and checks state before starting a fresh transaction. Durable retry
semantics remain open for flight.

## Validation and next integration

The host codec checks packet bounds, primary length/version/type/APID/flags,
CRC, schema version, endpoint/transaction rules and exact payload length.
Argument validation is a separate call: invalid values must reach the
command handler's correlated INVALID_PARAMETER response after structural
validation. An unknown command ID currently raises PacketError; the future
dispatcher must preserve its validated header to issue UNKNOWN_COMMAND.
Malformed packets are discarded/counted rather than acted upon.

Run [codec tests and vectors](../../ground/ember/README.md). Firmware must
serialize fields explicitly; do not cast a packed C struct or reuse the
little-endian internal `comms_hk_proto.h` register map.

Next: generate the [Yamcs XTCE mission database](https://docs.yamcs.org/yamcs-server-manual/mdb/loaders/xtce/)
from this source, implement header/sequence/CRC command postprocessing and
matching simulated endpoint, then a bounded Pico parser/dispatcher and USB
bridge. The current live Yamcs instance still runs the upstream demonstration
dictionary. Events, event persistence, authentication, UTC, PUS, flight
limits and SatNOGS decoding are not implemented by this lab v1.
