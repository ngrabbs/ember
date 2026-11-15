# Yamcs operator guide

Open Yamcs from the [demo checklist](../DEMO.md#1-connect) and select
`realtime` in the instance that matches your connection.

| Instance | Path | Receive links |
| --- | --- | --- |
| `ember` | UHF or LTE | `uhf-tm-in`, `lte-tm-in` |
| `ember-bench` | IHU USB directly into the ground Pi | `ihu-serial-in` |

## Displays

| Page | Use it for |
| --- | --- |
| Overview | Last system and power observations. Flight adds the estimated UHF countdown and last GPS sample. |
| Power | EPS voltages, currents, charger temperature, and readout quality. |
| Payload | Last status, ping, and fire-check result. Flight also shows capture GPS and its check ID. |
| Devices & firmware | Discovery status and last reported firmware identities. |

These `.opi` pages use fixed-position widgets. Yamcs scales the whole canvas
and centers it, leaving margins when the viewport has a different shape.
Collapse the sidebar if you need more width, then use **View → Zoom to fit**.
Use **View → Actual size** for crisp text when the canvas fits, or adjust with
**Zoom in** and **Zoom out**. For narrow screens, use the page’s linked raw
parameter table.

A cached value can outlast the connection. Check the receive time in
**Telemetry → Packets**. An expired firmware row still shows the last reported
build. The UHF countdown returns to waiting when its schedule report is stale.

## Commands and results

Open **Commanding → Send a Command** in the selected instance. In `ember`,
the [IHU command guide](../../firmware/ihu/README.md#ground-station-commands-in-yamcs)
covers the UHF command set. In `ember-bench`, the five payload commands use
direct USB and require the regular GROUND_TEST build. The UHF startup profile
restricts USB to read-only console commands.

Check acceptance and completion in **Command History**. A timed-out result is
unknown. For `PAYLOAD_FIRE_CHECK`, check the result, execution mode, and
timestamp on **Payload**. `STATIC_STUB` identifies a stub response. Match
capture GPS to the result’s check ID.

[Deploy or recover Yamcs](OPERATIONAL.md) · [Record and replay](../ember/SESSIONS.md) · [Historical setups and validation](HISTORY.md)
