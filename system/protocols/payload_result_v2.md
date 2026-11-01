# Payload result v2: explicit quality UNKNOWN

The payload CAN result stays 16 bytes, big endian:
`version:u8, result:u8, mode:u8, reserved:u8, boot:u32, uptime_ms:u32, check_id:u32`.
Version 1 retains binary results 0=NO_FIRE and 1=FIRE. Version 2 additionally
permits 2=UNKNOWN only in ALGORITHM mode (2). The reserved byte remains zero;
no v1 field is silently repurposed. Boot and check ID must be nonzero.

Payload 0.5.0 uses v2 only for completed registration quality outcomes
REGISTRATION_LOW_CONTRAST and REGISTRATION_WEAK_FIT. Those outcomes deliberately
stop classification; they are neither FIRE nor NO_FIRE. Existing binary results
remain v1. Capture faults, corrupt inputs and processing deadline exhaustion
remain explicit errors, not completed quality results. Detailed reasons and
input/configuration hashes remain in the associated result.json.

IHU 0.15.3 preserves the result version when wrapping the reply in the existing
52-byte native PAYLOAD_FIRE_RESULT packet (20-byte body). COMMS 0.34.5 validates
both versions without changing radio framing or CRC checks. Ground dictionary,
result correlation and displays add UNKNOWN=2 while retaining historical
binary decoding. Result history publishes both ember-analysis-result and the
legacy ember-fire-result with the explicit UNKNOWN string when applicable.

For the demonstration, COMPLETED means capture/processing produced an explicit
decision or quality outcome. It does not prove fire-detection accuracy. A
command TIMEOUT/UNKNOWN is a different condition: no confirmed terminal reply.
The rubric still rejects those uncertain commands and actual execution faults.
