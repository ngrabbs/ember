# UHF demonstration validation in progress

The demonstration route is Yamcs `ember/realtime` through LibreSDR uplink,
COMMS, IHU and payload CAN, then a correlated RF response back into Yamcs.
The serial bench bridge is not part of this route. COMMS's enabled fire-arm
service opens one bounded receive/reply window per ground command; this is
readiness at boot without unsolicited RF transmission.

IHU 0.15.2 forwards explicit payload rejections as a native COMMAND_RESPONSE:
PAYLOAD_FIRE_CHECK, EXECUTION_FAILED, NOT_AVAILABLE, parameter_id=0, with the
payload error code in value. This is not a FIRE/NO_FIRE classification. Covered
cameras returning error 11 should produce this terminal failure in Yamcs,
not an unexplained timeout. Ambiguous missing replies remain UNKNOWN.

COMMS 0.34.3 waits up to seven seconds for the fire-check CAN exchange (including
HELLO and the IHU's five-second payload deadline); the PING wait remains two
seconds. Its 25-second RF lease preserves at least three seconds for one reply.
The original 20-second lease refused an observed 17.7-second first post-reboot
reply because less than three seconds remained. The ground capture is now
20 seconds and the arming-service observation bound is 29 seconds.
The ground receiver admits only matching valid binary results or correlated
NOT_AVAILABLE execution failures. No application retry is introduced.

Yamcs `ember/realtime` exposes PING and PAYLOAD_FIRE_CHECK over UHF. Reports
include elapsed milliseconds and ground packet size. Successful fire replies
also include the 16-byte application result size and payload boot/check IDs.
Payload 0.4.1 stores those IDs and exact generated reply bytes in result.json;
this enables a unique lookup without confusing ground and IHU transaction IDs.
Both MCU duplicate-tracking caches are bounded at 256 transactions per boot.
The IHU serial bench bridge is disabled; the RF/arming and payload services
are enabled at boot and idle between commands.

The rubric now targets 35 seconds ground-dispatch to correlated completion,
including radio setup, processing, RF and decoding. Four PING trials before
the receive-window extension completed in 23.942–24.758 seconds. The expanded
window must be remeasured. Covered-camera failures are independently received
over RF, but successful live analysis still requires a usable uncovered scene.
Neither these development trials nor the target establish detection accuracy
or full cold-power qualification.
