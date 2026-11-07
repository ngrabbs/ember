# Radio guide

[Documentation home](../README.md) · [Board interfaces](../../system/interfaces/README.md)

Choose the receiver for the hardware sending the packet. These settings describe
the named bench profiles. For spacecraft RF design and coordination status,
see the [frequency plan](frequency_plan.md).

| Bench profile | Signal or transport | Receiver and setup |
|---|---|---|
| EMBER COMMS downlink | 437 MHz test carrier, 1200 baud DBPSK, RF frame v3 | LibreSDR and the [DBPSK receiver](../../ground/bpsk/README.md#live-uhf-demo-receiver) |
| AMSAT SDRB downlink | 1200 baud 2-FSK, ±2.4 kHz deviation, RF frame v2. Default bench packet carrier 434.1 MHz with SDR tuned to 434.2 MHz. | LibreSDR and the [SDRB receiver](../../ground/uhf/README.md#optional-binary-packet-bench-applications) |
| Walter LTE-M telemetry | EMBER packet carried in UDP over the lab LTE-M network | [LTE bench runbook](../../ground/lte/BRINGUP.md) and [EPS walkthrough](../user/lte-eps-walkthrough.md) |

## Packet layout on the air

Fields are shown in transmit order. The widths are in bytes.

```text
COMMS DBPSK v3 →
[Preamble 32] [Sync 4] [V3 1] [Seq 4] [Len 2] [EMBER packet N] [CRC-32 4] [Guard 16]

SDRB 2-FSK v2 →
[Preamble 16] [Sync 4] [V2 1] [Seq 4] [Len 2] [EMBER packet N] [CRC-32 4]
```

Both frames use a repeated `0x55` preamble and sync word `0x1ACFFC1D`.
Multi-byte frame fields are big-endian. `Len` counts the embedded packet bytes.
The outer CRC-32 covers version through packet. The DBPSK guard is 16 zero
bytes. See the [DBPSK modem](../../ground/bpsk/modem.py) and
[SDRB frame code](../../ground/uhf/packet_radio.py).

Inside each RF frame, or directly inside the LTE UDP datagram, the native
[EMBER packet](../../system/protocols/ember_bench_v1.md#envelope) has its own CRC:

```text
[CCSDS primary header 6] [EMBER secondary header 24] [Payload N] [CRC-16 2]
```

## Verify reception

For the shared ground deployment, use [Yamcs `ember` / `realtime`](../../ground/yamcs/OPERATIONAL.md).
Confirm a fresh archive entry. For a bench acceptance run, compare its bytes to
the sent packet. See [viewing telemetry in Yamcs](../user/yamcs.md#view-telemetry).

- **COMMS DBPSK:** The October 17 run matched all 13 packets in Yamcs over a
  30-second test. [Recorded settings and limits](../../system/ground_station/evidence/uhf-flight-20261017/result.json)
- **SDRB 2-FSK:** The October 3 clock review matched six native packets through
  RF decode and Yamcs during a bounded transponder run. [Recorded run](../../ground/uhf/results/2026-10-03/clock-review/result.json)
- **LTE-M:** The October 2 reliability series matched 9 of 10 EPS packets in
  Yamcs. [Recorded runs](../../ground/lte/results/2026-10-02-eps-security-reliability.md)

The frame layouts above are for downlink. The
[RF fire-check command path](../user/payload.md) is a separate bounded operation.
Flight radio qualification remains open.

[COMMS hardware](../../hardware/comms/README.md) ·
[Modulation design references](modulation.md) ·
[Flight framing decisions](encoding.md) ·
[Link budget](link_budget.md)
