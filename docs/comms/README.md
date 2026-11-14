# Radio guide

[Documentation home](../README.md) · [Board interfaces](../../system/interfaces/README.md)

Choose the receiver for the hardware sending the packet. These settings describe
the named bench profiles. For spacecraft RF design and coordination status,
see the [frequency plan](frequency_plan.md).

| Bench profile | Signal or transport | Receiver and setup |
|---|---|---|
| EMBER COMMS downlink | 437 MHz test carrier, 1200 baud DBPSK, RF frame v3 | LibreSDR and the [DBPSK receiver](../../ground/bpsk/README.md#live-uhf-demo-receiver) |

## Packet layout on the air

Fields are shown in transmit order. The widths are in bytes.

```text
COMMS DBPSK v3 →
[Preamble 32] [Sync 4] [V3 1] [Seq 4] [Len 2] [EMBER packet N] [CRC-32 4] [Guard 16]
```

Both frames use a repeated `0x55` preamble and sync word `0x1ACFFC1D`.
Multi-byte frame fields are big-endian. `Len` counts the embedded packet bytes.
The outer CRC-32 covers version through packet. The DBPSK guard is 16 zero
bytes. See the [DBPSK modem](../../ground/bpsk/modem.py) and

Inside each RF frame the native
[EMBER packet](../../system/protocols/ember_bench_v1.md#envelope) has its own CRC:

```text
[CCSDS primary header 6] [EMBER secondary header 24] [Payload N] [CRC-16 2]
```
