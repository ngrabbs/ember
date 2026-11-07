# Walter LTE-M telemetry bench

Walter registers on the lab LTE-M cell and sends the native EMBER packet over
UDP to the ground receiver. The recorded setup uses an SDR eNodeB and EPC on the
ground Pi. The profile has demonstrated bounded bench delivery.

1. Prepare the [shared ground deployment](../yamcs/OPERATIONAL.md) and make
   sure the LTE cell can take ownership of LibreSDR.
2. Use the [EPS telemetry walkthrough](../../docs/user/lte-eps-walkthrough.md)
   to start the listener and cell, register Walter, and send one EPS observation.
3. Check the fresh packet in Yamcs `ember` / `realtime` on `lte-tm-in`.
   The walkthrough gives the byte and provenance checks and shutdown sequence.

Use the [engineering runbook](BRINGUP.md) for radio and EPC bring-up,
[inventory](INVENTORY.md) for the bench configuration, and
[Walter firmware](../../firmware/walter/README.md) for the modem application.
See the [October 1–2 notes and results](results/2026-10-02-bringup-notes.md) for
the attach and delivery experiments and [open work](TODO.md) for reliability
and orbital link questions.
