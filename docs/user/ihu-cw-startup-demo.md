# Automatic IHU startup and CW beacon bench demo

**IHU 0.17.0 + transceiver 0.36.0.** This is a matched, explicitly built
GROUND_TEST profile for the existing CAN Feather IHU and original-Pico radio
controller. It is separate from the standalone Pico switch demo and from flight
firmware. Use a conducted, attenuated RF bench setup and an isolated test CAN bus.
The transceiver can automatically transmit after boot when the matching IHU
requests the beacon. Do not install these two test images on a flight article.

## Build

Use separate build directories. Both options default OFF. The IHU demo option
cannot be combined with the FLIGHT configuration.

```sh
identity=$(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake -S firmware/ihu -B build/ihu-startup-demo \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" -DIHU_BOOT_DEMO=ON $identity
cmake --build build/ihu-startup-demo -j4
cmake -S firmware/transceiver -B build/transceiver-startup-demo \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" -DPICO_BOARD=pico \
  -DTRANSCEIVER_BOOT_DEMO=ON $identity
cmake --build build/transceiver-startup-demo -j4
```

Use a POSIX shell for those commands. On zsh, run them under `sh` so the
multiline identity variable is split into its two CMake arguments.

## Run

1. Connect the transceiver TX output to the conducted load/attenuator and test
   receiver. Connect the IHU, EPS housekeeping I²C and transceiver CAN A. Keep
   antenna actuators disconnected; the demo has no actuator command.
2. Save/readback-verify the current firmware on both boards. Identify each board
   by its flash ID before loading the corresponding UF2. Do not interchange
   the IHU and transceiver images.
3. Open the IHU USB console at 115200, then cold-power the bench pair. The
   sequence runs without a serial client and replays retained startup messages
   when one connects. `startup` prints the trace and current mode on demand.
4. Observe local CAN and valid EPS register reads, then the transceiver READY
   handshake. This is a readiness check, not RF reception evidence. Simulated
   release starts two independent timers: **10 s antenna**, **15 s radio silence**.
5. After simulated antenna deployment and the silence wait, the IHU enters
   COMMISSIONING. The transceiver keys **KI5YNG - EMBER BOOT** once on the
   existing nominal **437.000 MHz** transmit setting at **15 WPM** (80 ms dot).
6. Once the radio reports the beacon complete and RX clock ready with TX muted,
   the IHU reports `NOMINAL` with `reason=DEMO_RX_ONLY`. All six IHU output
   flags remain off. The radio leaves RX enabled; it samples bounded capture
   blocks and logs decoded packets without dispatching commands or transmitting
   replies. There are acquisition gaps while it decodes, so a single arbitrary
   uplink is not guaranteed to be captured.
7. Use `mode safe` or `uhf stop` on the IHU to cancel. A byte on the
   transceiver console also stops that radio profile; do not type into it when
   observing a run. Reset both boards to run the one-shot again.

No per-step console action is required. If a check fails or radio completion is
unknown, the IHU enters SAFE, reports the reason, and does not retry the beacon.
Ground-test demo commands do not permit manual mode jumps or output enables.
The transceiver demo excludes the ordinary transmit and command-dispatch loop.

## CAN and bounds

The demo reserves classic CAN A IDs 0x750–0x756, in order: PROBE, FIRE, STOP,
READY, RX, FAILED, KEEP. Each frame has two little-endian 32-bit words: IHU boot
token, then transceiver boot ID (zero for PROBE). This is correlation for an
isolated bench, not authentication. The transceiver admits only one token per
boot, requires a 15 s local wait and 30 s arm expiry, and consumes the beacon
permission before touching TX. IHU sends FIRE at most once. While keying it
expects a matching keepalive at least every 750 ms (IHU sends every 200 ms)
and uses an 18 s absolute mute alarm. Neither late replies nor duplicate FIRE
can reopen the one-shot. The radio mutes and shuts down clocks on failure.
The IHU times out missing receive status after 12 s. There is no state retained
across a full pair power cycle.

## Conducted acceptance

Save the exact firmware hashes, both console traces, and an independent RF
capture. Register readback/firmware logs do not demonstrate actual RF silence,
frequency, or decode. Before declaring hardware acceptance:

- Cold boot without any console commands. Confirm no RF before the silence
  deadline; check the two timer events separately and show no actuator operation.
- Measure the carrier near its configured nominal target, decode the entire
  CW text and check keying speed. Confirm one burst and mute after it.
- Confirm the receiver remains enabled and capture a known test uplink in a
  sampling window. Verify no automatic RF response or payload dispatch.
- Test missing EPS, missing/mismatched transceiver, operator stop during a mark,
  CAN loss or IHU reset during CW, and loss of RX status. Record mute latency
  and verify no second beacon. Reset the pair between tests.
- Restore prior images and verify their identities if returning to the normal
  bench configuration.

The short waits and simulated release are demo-only. They do not replace flight
release sensing, launch delays, independent inhibits, or actuator feedback.
