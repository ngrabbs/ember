# COMMS–Walter UART bench envelope v1

This is a diagnostic transport beneath EMBER packets. It returns opaque bytes
unchanged, including the inner packet's source, boot ID, sequence, transaction,
and inner CRC. It does not execute spacecraft commands, submit packets to a
modem, or prove IHU forwarding. `BENCH_ECHO_MATCHED` only means the opposite
ESP32 returned matching bytes. Production SEND_PACKET/TX_RESULT/RX_PACKET and
RX_RESULT IDs, queues, and modem outcome handling remain unimplemented.

## Wire definition

115200 baud, 8N1, no hardware flow control. Full COBS-encode the decoded
header/payload/CRC, then append zero. Send an extra leading zero to discard
partial boot output. Empty delimiters are ignored. Standard 0xff COBS blocks
are supported; the existing USB bench framing's smaller bound/decoder must not
be substituted here.

| Decoded offset | Bytes | Field |
| --- | --- | --- |
| 0 | 2 | Magic `45 55` (EU) |
| 2 | 1 | Version, 1 |
| 3 | 1 | Message type |
| 4 | 4 | Sender boot/session ID |
| 8 | 4 | Request origin boot/session ID |
| 12 | 4 | Request ID |
| 16 | 2 | Payload length, 0–240 |
| 18 | length | Opaque payload |
| 18 + length | 2 | CRC-16/CCITT-FALSE of header and payload |

All integers and CRC are big endian. CRC uses polynomial 0x1021, initial 0xffff,
no reflection or final XOR. `123456789` gives 0x29b1. Header is 18 bytes; decoded
maximum is 260, encoded maximum 262 excluding delimiter, wire maximum 263.
The optional leading delimiter adds one transmitted byte.

Boot/session IDs are nonzero random 32-bit values, newly sampled per controller
boot. They are bench reset discriminators with possible collisions, not security
identities or authenticated sessions. RP2040 uses Pico SDK `get_rand_32`; ESP32
uses `esp_random` without enabling its radios. Request IDs are nonzero and grow
within a Feather boot; exhausting them requires reset rather than silent reuse.

| Type | ID | Request payload | Reply |
| --- | --- | --- | --- |
| HELLO | 0x01 | Empty | HELLO_ACK, 0x02, empty |
| BENCH_ECHO | 0x70 | 1–240 opaque bytes | BENCH_ECHO_ACK, 0x71, identical bytes |
| ERROR | 0x7f | Reply only: one reason byte | No automatic processing/response by COMMS |

Requests must have origin equal to sender. Replies carry Walter's sender boot
ID while retaining the request's origin and request ID. The Feather admits one
pending request; another is locally rejected as BUSY. HELLO must succeed before
an echo is admitted. Replies must match version, origin, request, type, size,
and exact payload. Echo replies must also match the established peer boot ID.
A changed peer boot produces UNKNOWN and clears the handshake. A HELLO can
establish the peer afresh. A two-second timeout likewise produces UNKNOWN and
requires HELLO; there are no automatic retries or side-effecting commands.
Duplicate echo requests can be answered repeatedly because echo is stateless.
Unmatched/late responses are logged and ignored, never counted as success.

CRC-valid, structurally intact requests receive explicit ERROR reasons:
1 unsupported version; 2 unsupported type; 3 invalid request origin; 4 invalid
payload size for the selected service. CRC corruption, invalid COBS, bad magic,
zero identity, impossible lengths, and encoded overflow are dropped because
correlation fields are untrusted. Decoder counters distinguish those faults.
An encoded overflow discards through zero. A 250 ms interbyte gap in a partial
frame also discards through zero. The next complete frame can resynchronize.
Unsigned elapsed-time arithmetic supports millisecond timer wrap.

## Bench commands and verification

Feather USB: `status`, `help`, `hello`, `echo N` (ascending-byte test payload,
1–240), `packet HEX` (opaque bytes), and `raw HEX` (bounded fault injection).
Each command ends in newline. `raw` bypasses pending request tracking deliberately;
its responses are unmatched diagnostics. It is not an operational packet API.
Walter USB: `status` and `help`; its modem is held in reset in both images.
There are no automatic UART frames at boot.

Native parser tests (no SDK dependency):

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I firmware/comms_transport firmware/comms_transport/tests/test_uart_link.c \
  -o /tmp/ember_uart_link_test
/tmp/ember_uart_link_test
```

Tests cover a literal HELLO frame, the standard CRC check vector, all 1–240 byte
sizes for three patterns (720 cases), COBS 0xff blocks, corrupted CRC, malformed
COBS, overflow, partial-frame timeout, timer wrap, explicit service rejection,
and recovery. Independent Python HELLO vector:
`0d455501011122334411223344010102070103538b00`.

After both images are installed and USB is on Feather:

```sh
python3 ground/ember/comms_uart.py \
  --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF637882D39E4426-if00 \
  --output /path/to/private/evidence
```

Host test checks 15 boundary/pattern echoes, one synthetic EMBER IHU heartbeat,
explicit version/type rejection, and a separate 240-byte echo immediately after
each bad CRC, oversized encoded input, and truncated frame. It requires 20
correlated matches (19 echoes plus HELLO), two unmatched diagnostic rejections,
and no increase in the timeout counter. The synthetic heartbeat is generated by
the host; it is not live telemetry from the IHU. Output preserves the complete
USB transcript and summarized JSON. It does not establish sustained throughput,
FIFO overrun behavior, independent controller-reset recovery, or RF delivery.

## Hardware state, 2026-10-02

Both images build with warnings treated as errors. Feather image was flashed
and readback verified. Before updating Walter, a real hardware test established
HELLO_REQUIRED, BUSY, two-second UNKNOWN timeout, and pending-slot clearance.
Its initial gap counter includes a pre-test startup byte.
The native shared-parser tests passed under AddressSanitizer/UndefinedBehaviorSanitizer,
and all 30 existing ground protocol/bridge/session tests passed. The host paired
test script is staged under the m75q task directory's `host-tests/` subdirectory.

Feather UF2 SHA-256:
`b45d81ef73d59b0b9d48bfc8c41de22e1f38fdd2cf171dc55b28821b4820828a`.
Built Walter binary SHA-256:
`268875a1a0cd98776607696c47f86e05d78319456436d278b997e1b9dbedc7b9`.
Walter framed image was installed with all written-region hashes verified.
Its USB status/help, unknown-command rejection, overlong-command rejection,
nonzero consistent boot identity, and growing uptime passed. Both sampled
statuses reported zero UART traffic/parser faults and `modem=HELD_RESET`.
Opening USB reset the application (first sampled uptime 301 ms).

Paired hardware tests passed with USB on Feather and Walter separately powered.
The first run completed 15 boundary echoes, one synthetic heartbeat, one recovery
echo after the combined faults, and HELLO (18 matches). The strengthened second
run completed 19 echoes plus HELLO (20 matches), checking recovery immediately
after each injected fault. Sizes 1, 2, 32, 239, and 240 bytes passed with zero,
nonzero, and ascending patterns. The returned heartbeat decoded with original
IHU source 2, sequence 7, boot ID 0x10203040, uptime 123456, SAFE/GROUND_TEST,
and 1000 ms period. It was host-generated rather than sampled from the IHU.

Unsupported version/type requests returned their explicit reasons and were
ignored as unmatched raw diagnostics. Corrupt CRC, 263 encoded nonzero bytes,
and an eight-byte truncated frame elicited no frame response during the checked
window; each was immediately followed by a successful exact 240-byte echo.
Feather's match count rose 18 → 38 during the strengthened run, with two new
unmatched diagnostics, no pending request afterward, and no new UNKNOWN timeout.
Starting overflow/gap counters and the earlier deliberate missing-peer timeout
are historical, not failures in these paired runs. Faults were injected into
Walter; its local parser counters were not independently sampled afterward.

[Saved summary](../../system/ground_station/evidence/comms-walter-framed-20261002.json)
includes board identities, binary hashes, original/final status, and scope.
Private paired transcripts are in `framed-paired-20261002/` and
`framed-independent-faults-20261002/` beneath the task directory below.
These short runs do not qualify sustained throughput, independent reset recovery,
live IHU forwarding, CAN, modem submission, or RF delivery.
Private logs are under `/media/ngrabbs/BACKUP-A/ember-walter-bridge/` on m75q:
`feather-framed-build.log`, `walter-framed-build.log`,
`feather-framed-flash.log`, `feather-framed-no-peer.log`,
`walter-framed-flash.log`, and `walter-framed-usb.log`.
