# UHF demonstration validation in progress

The demonstration route is Yamcs `ember/realtime` through LibreSDR uplink,
COMMS, IHU and payload CAN, then a correlated RF response back into Yamcs.
The serial bench bridge is not part of this route. COMMS's enabled fire-arm
service opens one bounded receive/reply window per ground command; this is
readiness at boot without unsolicited RF transmission.

IHU 0.15.1 forwards explicit payload rejections as a native COMMAND_RESPONSE:
PAYLOAD_FIRE_CHECK, EXECUTION_FAILED, NOT_AVAILABLE, parameter_id=0, with the
payload error code in value. This is not a FIRE/NO_FIRE classification. Covered
cameras returning error 11 should produce this terminal failure in Yamcs,
not an unexplained timeout. Ambiguous missing replies remain UNKNOWN.

COMMS 0.34.1 waits up to seven seconds for the fire-check CAN exchange (including
HELLO and the IHU's five-second payload deadline); the PING wait remains two
seconds. The existing 20-second RF lease and single-response bound remain.
The ground receiver admits only matching valid binary results or correlated
NOT_AVAILABLE execution failures. No application retry is introduced.

Timing limits for the demonstration must be established from measured Yamcs
ground-to-ground command history, including capture, analysis, radio setup,
RF and decoding. The prior 8-second wired target does not apply to this route.
This change is not yet a hardware qualification or an accuracy claim.
