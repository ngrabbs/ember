# Walter LTE-M firmware

Reserved for the spacecraft-side Walter application. No application source has
been imported or developed here yet. The attached board currently runs a modem
AT passthrough application whose source/build provenance is not yet located.

Intended placement: Walter alongside the **COMMS MCU** on the communications
assembly. The COMMS MCU is the spacecraft communications endpoint; Walter
manages LTE-M beneath it. The **IHU MCU** supplies telemetry and retains command
authority. Current IHU–COMMS I2C firmware is status/ping only; CAN is the intended
internal packet transport. See the
[controller interface draft and owned TODO](../../system/interfaces/comms_walter.md).
UART pins and forwarding firmware are not assigned/implemented yet.

Bench procedures and the implementation checklist live in
[ground/lte](../../ground/lte/README.md).

When development begins, record the ESP32 toolchain, WalterModem library commit,
modem firmware, build/flash procedure, and power/reset behavior. Start with
sequenced UDP telemetry and reconnect handling, then integrate the shared EMBER
telemetry definitions. Keep SIM credentials and builds outside tracked source.

## Vendor sources checked 2026-10-01

Organization: [QuickSpot](https://github.com/QuickSpot).

- [Arduino modem library](https://github.com/QuickSpot/walter-arduino), inspected
  commit `c30b707f8d64b49daec80de6bccfc80c04e42d58`.
  Its [passthrough example](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/examples/passthrough/passthrough.ino)
  bridges USB serial to modem UART at 115200 and hardware-resets the modem in
  setup. This is consistent with the observed reset behavior, but does not
  identify the exact binary currently flashed on our board.
- [Arduino UDP example](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/examples/udp/udp.ino)
  supplies a registration, PDP context, and UDP starting point. Its default
  destination is QuickSpot's demo server; adapt to our local ground receiver
  and APN `srsapn` when developing EMBER telemetry.
- [ESP-IDF modem library](https://github.com/QuickSpot/walter-esp-idf), inspected
  tree commit `d99e5783c28d66e67457794de95464d3c67cd0e6`; includes a UDP example.
- [Documentation](https://github.com/QuickSpot/walter-documentation), inspected
  commit `5e16b81f0aaa2f0a455feb6573bb94a46786dd7e`; includes
  [SIM/network API reference](https://github.com/QuickSpot/walter-documentation/blob/5e16b81f0aaa2f0a455feb6573bb94a46786dd7e/walter-modem/arduino_esp-idf/reference/sim_and_network.md)
  and [GM02S AT command manual](https://github.com/QuickSpot/walter-documentation/blob/5e16b81f0aaa2f0a455feb6573bb94a46786dd7e/file/gm02s_at_commands.pdf).
  The manual's applicability to installed UE8.2.1.0 still needs checking before
  relying on firmware-specific commands.

The Arduino UDP example sets NO_RF, defines its PDP context, enables FULL radio
operation, selects an operator, and waits for home or roaming registration
before proceeding. Our next firmware should also bound waits and preserve
explicit shutdown/recovery behavior. A vendor example does not resolve the
current ground-cell acquisition failure by itself. No firmware was flashed
as part of this source review.
