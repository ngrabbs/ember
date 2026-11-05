# Continuous UHF link to Yamcs

For the conducted bench with **IHU 0.18.0 / transceiver 0.37.1** in
`GROUND_TEST / NOMINAL / LINK_ACTIVE`, use Yamcs instance **ember**, processor
**realtime**. The ground Pi at 192.168.1.251 runs one LibreSDR owner,
`ember-fire-uplink.service` (now the continuous gateway).

```text
Yamcs ember ── native command / UDP 10029 ──> ground RF gateway
              ── conducted uplink ──> EMBER transceiver ── CAN ──> IHU

IHU ── CAN ──> EMBER transceiver ── conducted downlink ──> ground RF gateway
    ── validated original packet / loopback UDP 10019 ──> Yamcs ember
```

Yamcs does not control the SDR. It sends command bytes through its UDP TC link
and correlates the returning native reply. The gateway keeps the SDR's
`RX2` stream running on 437.000 MHz and schedules finite bursts on the
`TX/RX` port at 434.994550 MHz. The separate conducted paths allow the ground
radio to receive during TX. The spacecraft radio is half-duplex and returns
to RX after each transmission.

Continuous RX forwards valid native packets, including unsolicited 10-second
heartbeats, without a preceding command. The gateway forwards original bytes,
suppresses overlap duplicates, bounds receive/decode memory, and logs receive
gaps and local TX status. It does not retain raw IQ during ordinary operation.
SDR TX acknowledgment means a local burst completed; only Yamcs receiving the
correlated IHU reply completes PING. A PING can still miss the spacecraft's
receive window, so a timeout is UNKNOWN and is not automatically retried.

## Operation

- Confirm the conducted and attenuated uplink/downlink connections before
  starting the service. No RF TX occurs at service startup.
- `systemctl status ember-fire-uplink` and
  `journalctl -fu ember-fire-uplink` on the ground Pi show readiness and counts.
- In `ember / realtime`, check for recent HEARTBEAT packets and issue **PING**.
  The current startup profile admits PING only. Older command definitions in
  the MDB do not make those commands supported by this firmware.
- Stop the gateway before using another SDR diagnostic or listener. On this
  bench, `ember-lte-listener` is a UDP listener and does not own the UHF SDR.
- m75q remains available for USB console debug and flashing. Its serial arm
  and network bench bridge services are retired from this setup. The
  `ember-bench` instance retains historical data and displays without a live
  connection. Optional wired lab tools require an explicit endpoint.

## Deployment

Install `link_gateway.py` with the BPSK and native codec modules. Install the
updated `ember-fire-uplink.service` on the ground Pi; remove the temporary
`--link-active` override from the preceding one-shot deployment. Reload systemd
and enable/start the service. No firmware reflash is needed for the ground
gateway change. Do not start the former m75q arm or serial bridge units.

The operational Yamcs generator leaves the bench archive without hardware
links and publishes only the two live RF/LTE telemetry ports. On an existing
running server, disable `ihu-serial-in` and `ihu-serial-out` in `ember-bench`
using the Links page; there is no need to rebuild the running MDB or archive.

## Acceptance

Verify several consecutive RF heartbeats appear in the Yamcs archive without
issuing commands. Send PING from Yamcs and check a correlated COMPLETED reply.
Verify heartbeats before and after the PING with the same gateway process.
Check that m75q bridge services are absent and both retired Yamcs links are
disabled. This is an integration test of the conducted bench, not a claim of
gap-free spacecraft receive coverage or over-the-air qualification.
