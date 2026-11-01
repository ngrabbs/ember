# C&DH UHF demonstration contract

Commands use the existing native header and CRC; no transport or pin-map migration.
The operational route is Yamcs ember/realtime → SDR → COMMS → IHU CAN, with one
correlated RF response. No serial bench command/result path is used.

| Command | ID | Arguments | Terminal result |
| --- | --- | --- | --- |
| REQUEST_STATUS | 2 | none | IHU_STATUS (58), actual policy snapshot |
| REQUEST_TELEMETRY | 3 | data_group:u8 | group1 → IHU_STATUS; all other groups → REJECTED/INVALID_PARAMETER |
| STATUS_CAPTURE | 4 | none | STATUS_RECORDS (59), after five1Hz samples |
| STATUS_FETCH | 5 | capture_id:u32 | same frozen STATUS_RECORDS, or explicit failure |
| IHU_REBOOT | 6 | none | COMPLETED/value5000: restart scheduled in5s; verify new boot by status |

C1 is firmware SAFE initialization within30s, periodic outputs off, plus status
query round trip ≤35s. `boot_ready_ms` is completion of application initialization,
not a physical rail/power-up measurement. A new boot ID must follow the reboot.
Reboot requires SAFE/output flags0 and no pending mission/capture work. The
scheduling response is not evidence the restart occurred. Battery health and
health-gated mission enablement are excluded from this revised demonstration.

C2 deliberately transmits group255 through Yamcs and RF; the IHU returns native
COMMAND_RESPONSE stage1/reason2. A UI validation error, CRC discard or missing
reply is not a successful rejection demonstration. Both positive and negative
terminal reports must arrive within35s; mode/output flags must remain unchanged.

C3 holds one volatile bank of five16-byte records. Record order is sequence:u16,
uptime_ms:u32, mode:u8, configuration:u8, outputs:u8, can_ready:u8, can_eflg:u8,
eps_valid:u8, eps_age_ms:u32. EPS validity means register-read success only.
The STATUS_RECORDS payload is version:u8=1,count:u8=5,record_size:u8=16,
volatile:u8=1,capture_id:u32,then80 stored bytes:88 payload /120 native bytes.
The183-byte BPSK frame takes1.22s at1200baud, within existing1.5s payload and
2s hard mute limits. No RF safety window is enlarged.

Sampling is actor-owned and uses actual uptime timestamps; it never fabricates
catch-up records. More than100ms scheduling lateness fails the capture. Measured
intervals are visible in the report. A completed bank stays frozen until an
explicit new capture or reboot. Fetch requires the exact capture ID; unknown
sets fail. Capture transaction keys are bounded/non-evicting (64 per IHU boot);
a duplicate does not repeat capture. Old replaced sets/conflicting identities
fail explicitly. An incomplete capture is never exposed as a complete bank.

Yamcs reports sample intervals, count, capture ID, age and SHA-256 of exactly80
stored bytes. The read-only verify_cdh_records.py compares original archived
UHF bytes, exact equality, sequence and timing, same boot/capture, both ≤35s
command deadlines and at least60s between IHU response timestamps. Qualification
also records a ground receiver idle interval ≥60s after the original report.
SHA-256 and CRC are integrity evidence, not authentication or detector accuracy.

Readiness is enabled at boot; all RF remains bounded and command-initiated.
A fresh correlated read-only status response can establish a changed IHU boot;
other outstanding work remains uncertain across a reset. No automatic retry.
