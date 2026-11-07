# AMSAT SDRB FSK receiver

Use this guide for the optional SDRB binary FSK bench profile. The
[radio guide](../../docs/comms/README.md) gives the frame layout and identifies
the separate EMBER COMMS receiver.

## Receive SDRB telemetry

1. Confirm LibreSDR is free and uses the bench's custom FPGA image. Check the
   physical receive port and gain for your bench. The example uses the recorded
   SDRB setup with a 434.2 MHz tune frequency and a 434.1 MHz packet carrier.
2. Use the [installed supervision profile](SERVICES.md), or start a bounded
   manual receive session from the repository root:

   ```sh
   python3 ground/uhf/libresdr_live_rx.py --seconds 60 --channel 0 --gain 40 \
     --frequency 434200000 --forward --output /path/to/new-run
   ```

3. Wait for `UHF_RX_READY` before submitting a packet on SDRB. The
   [supervision procedure](SERVICES.md#start-arm-observe-stop) covers SDRB startup,
   CAN admission, and shutdown. With manual ground reception, use only the SDRB
   steps from that procedure.
4. On the shared deployment, look for a fresh Yamcs packet in `ember` /
   `realtime` on `uhf-tm-in` (UDP 10019). Compare the decoded and archived
   bytes to the original packet. Use the
   [shared deployment guide](../yamcs/OPERATIONAL.md) for the Yamcs setup.

See the [clock and transport review](CLOCKING.md) for the bounded 614.4 kS/s SDRB
profile. The [October 3 bench notes](results/2026-10-03/bench-notes.md) retain
the manual sender examples, isolated archive setup, test sequence, and results.
[SDRB workstreams](../../system/sdrb/TODO.md)
