# Internal Housekeeping Unit Phase 1 Validation Plan

## Scope

Phase 1 validates IHU boot behavior, interface reliability, and basic
command/telemetry loop closure before full system integration.

## Test 1: Boot and Reset Behavior

### Objective

- Verify deterministic startup sequence and mode initialization
- Verify watchdog-triggered recovery behavior

### Procedure

1. Power-cycle IHU board repeatedly and log boot status
2. Verify default mode is safe mode until subsystem links are healthy
3. Trigger watchdog timeout intentionally and verify reset recovery path

Provisional healthy-link criteria for mode release:
- EPS I2C telemetry reads valid for >= 5 consecutive polls
- Comms SPI heartbeat valid for >= 5 consecutive intervals

### Initial Acceptance Criteria

- Boot completes reliably across repeated power cycles
- Reset reason is logged and exposed to diagnostics
- Watchdog recovery returns board to known-safe state
- IHU remains in safe mode until both healthy-link criteria are met

## Test 2: IHU <-> EPS Housekeeping Link (I2C)

### Objective

- Verify reliable charger and rail telemetry polling via I2C path

### Procedure

1. Connect IHU I2C bus to EPS telemetry path
2. Poll telemetry registers at fixed interval (for example 5 to 10 Hz)
3. Inject transient bus disturbance and verify retry behavior

### Initial Acceptance Criteria

- Polling remains stable without persistent bus lockup
- Timeout/retry logic recovers from transient communication failures
- Telemetry values pass range/sanity checks

## Test 3: IHU <-> Comms Data Link (SPI)

### Objective

- Validate bidirectional packet exchange between IHU RP2040 and comms RP2040

### Procedure

1. Bring up SPI link with IHU as master and comms as slave
2. Exchange loopback packets with sequence counters and CRC
3. Run sustained transfer test at target SPI clocks (4 to 8 MHz range)
4. Inject framing faults and verify retry/timeout policy

### Initial Acceptance Criteria

- No unrecovered framing loss during sustained test window
- CRC and sequence checks detect injected faults
- Bounded retries and degraded-mode logic behave as designed

## Test 4: Command and Telemetry Control Loop

### Objective

- Verify IHU command dispatch and telemetry aggregation flow end-to-end

### Procedure

1. Inject representative command set to IHU command parser
2. Dispatch commands to subsystem interface handlers (EPS/comms stubs or live)
3. Aggregate status into telemetry frames and forward to comms path

### Initial Acceptance Criteria

- Valid commands execute with ACK/response behavior
- Invalid commands are rejected with explicit status code
- Telemetry frame generation remains deterministic under command load

## Evidence Capture Requirements

- Save serial logs, trace captures, and failure-injection notes
- Record firmware version/hash and test configuration
- Store outputs under `hardware/ihu/bringup/` by date/revision

## Phase 1 Exit Condition

- IHU boots and recovers predictably
- I2C and SPI baseline links are repeatable and fault-tolerant
- Command and telemetry loop is stable enough for broader integration testing
