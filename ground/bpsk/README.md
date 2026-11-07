# COMMS DBPSK receiver

Use this receiver for EMBER COMMS v3 downlink. The
[radio guide](../../docs/comms/README.md) gives the RF profile and frame layout.
For the bounded fire-check uplink, see the [Yamcs service guide](../yamcs/FIRE_CHECK.md).

## Live UHF demo receiver

1. On the ground Pi, confirm LibreSDR is free and uses the existing custom FPGA
   image. Confirm the receive port matches the physical setup. The example uses
   the October 17 test carrier and gain.
2. From the repository root, start a bounded receiver session with a new output
   directory:

   ```sh
   python3 ground/bpsk/live.py --seconds 90 --frequency 437000000 --gain 0 \
     --forward --output /path/to/new-run
   ```

3. Wait for `BPSK_RX_READY`. For current IHU and COMMS firmware, follow the
   [IHU-requested UHF procedure](../yamcs/OPERATIONAL.md#ihu-requested-uhf-telemetry).
   The receiver does not start the transmitter.
4. Look for `BPSK_RX_PACKET` and a fresh packet in Yamcs `ember` / `realtime`
   on `uhf-tm-in`. Compare the archived bytes to the native packet. Use
   `packets.jsonl` and `result.json` to check packet identity and receiver errors.

The receiver writes about 92 MB of raw IQ per minute. Ctrl-C ends reception and
saves results. Check receiver and IHU status when closing a bench run.

The [October 17 run](../../system/ground_station/evidence/uhf-flight-20261017/result.json)
matched 13 packets in Yamcs over a bounded 30-second transmission. Earlier
capture, firmware-specific commands, and test results are in the
[DBPSK bench history](HISTORY.md). See [release identities](../releases/README.md)
when comparing deployed versions.
