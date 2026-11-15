# Ground station demo checklist

## 1. Connect

- [ ] Power on `ember-ground`. Connect LibreSDR for a radio demo or the IHU USB console for a wired demo.
- [ ] For hotspot use, leave Ethernet unplugged, join `EMBER-Ground`, and open [Yamcs](http://192.168.50.1:8090). On lab Ethernet, use [the lab address](http://192.168.1.251:8090).

## 2. Choose a path

Use one radio session at a time on the shared LibreSDR.

### Receive UHF

- [ ] Select **ember / realtime**. Use the running UHF gateway (`ember-fire-uplink`) or follow the [manual DBPSK receiver guide](bpsk/README.md#live-uhf-receiver) after releasing LibreSDR. Check **uhf-tm-in**.

### Receive LTE

- [ ] Select **ember / realtime**. Check `systemctl status ember-lte-listener` on the Pi, then follow the [LTE cell runbook](lte/README.md#start-the-cell) and [Walter bench check](../firmware/walter/README.md#how-lte-telemetry-reaches-yamcs). Check **lte-tm-in**.

### Direct USB

- [ ] Plug the registered IHU console directly into the Pi. Select **ember-bench / realtime** and check **ihu-serial-in**. The wired links disable when the console disconnects. The UHF startup firmware restricts USB to read-only console commands.
- [ ] For manual console access only, run `sudo systemctl stop ember-bench-bridge@ttyACM0` on the Pi. Use the [actual tty name](yamcs/OPERATIONAL.md#serial-ownership-and-eps) if it differs.

## 3. Verify a fresh packet

- [ ] On **Links**, check that the selected receive counter increases. Open **Telemetry → Packets**, refresh, and look for the expected packet with a receive time after the demo started.
- [ ] If nothing arrives, check the instance and link first, then check the receiver or USB bridge and whether EMBER is sending on that path.

## 4. Shut down

- [ ] Stop any demo telemetry run and close the manual receiver. Restore the UHF gateway if you stopped it. For LTE, close the IHU window with `lte 0` before stopping the eNodeB and EPC.
- [ ] Close the manual USB console and run `sudo systemctl start ember-bench-bridge@ttyACM0` if you stopped the bridge and the IHU is still connected. Power down the Pi with `sudo poweroff` before disconnecting power.

[Pi setup and recovery](pi/README.md) · [Yamcs deployment](yamcs/OPERATIONAL.md) · [Release records](releases/README.md) · [SDRB bench](bench/sdrb/README.md) · [LTE diagnostics](lte/diagnostics/README.md)
