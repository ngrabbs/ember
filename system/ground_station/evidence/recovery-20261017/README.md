# Recovery checks — October 17, 2026

Installed: IHU0.9.0, COMMS0.24.0 (clean source f4a6a0a), LTE Feather0.8.0,
Walter0.3.0, receiver2.2.0 and Yamcs UHF assets1.2.0. No firmware changes
were needed for these tests. The stack remained powered with both CAN nodes.

| Test | Observed result |
| --- | --- |
| COMMS reboot | Boot identity changed; request using previous peer timed out after5 seconds as UNKNOWN. IHU cleared peer and pending work. New HELLO and32-byte echo passed. |
| RF after reboot | After HELLO, UHF heartbeat was explicitly rejected with UHF_DISABLED=7. Reboot did not restore a transmit window. |
| CAN application unavailable | Held COMMS Pico in BOOTSEL without changing flash. Echo timed out; COMMS became STALE at last-seen age35097ms with3 discovery timeouts. EPS and LTE stayed ONLINE. |
| CAN application recovery | Rebooted COMMS into its existing image. Fresh HELLO and echo passed; COMMS returned ONLINE with new boot ID. Historical discovery timeout counters remained. |
| Ground receiver stop/restart | Initial reception delivered COMMS identity and heartbeat request33. Stopped receiver with SIGINT; request34 transmitted during outage but was not received. Restarted receiver and waited for READY; requests35 (heartbeat) and36 (registry) arrived without restarting either MCU or reopening the existing bounded RF window. |

The four received packets match native transmitter bytes and Yamcs archive
bytes exactly. Request34 is absent from both receiver captures and the archive;
there was no retry or replay. IHU still correctly reported RF_TX_COMPLETE with
ground_ack=0 for the lost packet. Transmission completion is not ground delivery.
Both receive sessions finished without SDR/decoder errors (the first records
operator interruption). Final state: no pending IHU/UHF requests, zero CAN
TEC/REC/error flags or TX failure counters; two intentional application timeouts
remain recorded as UNKNOWN. COMMS TX=0 and clock output disable0xFF verified.

## Operating recovery

After COMMS reboot or application timeout, wait for discovery, then issue
`hello comms` from IHU. If discovery is currently active, wait briefly after
BUSY_TARGET_SWITCH and retry explicitly. Confirm the peer and echo. Reopen
COMMS's bounded RF window explicitly before requesting new telemetry.

After receiver restart, wait for BPSK_RX_READY before sending the next packet.
No ground acknowledgment or automatic retransmission exists in this bench
protocol; packets sent during downtime are lost. If COMMS itself is unreachable,
the UHF link cannot deliver a fresh report of its own absence: Yamcs retains
historical values until expiration. An independent link is needed to observe
that outage live from the ground.

## Scope limits

BOOTSEL tests loss of the COMMS application, not physical CAN disconnection,
loss of all hardware ACKs, bus-off, power brownout, or reset mid-RF symbol.
Those fault-injection cases remain unqualified. Reboot was tested while idle,
followed by explicit requests; active-run interruption was not tested here.
No powered harness was disconnected. STALE was observed on the IHU console;
no synthetic failure packets were injected into Yamcs.

Raw serial and receiver logs remain in the local recovery artifacts and bench
run directories. verification.json records the independent archive comparison.
