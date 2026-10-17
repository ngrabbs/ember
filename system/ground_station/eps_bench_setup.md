# Historical IHU/EPS UART bench

These are dated observations from the retired FreeRTOS UART prototype.
The active IHU uses the [USB console guide](../../docs/user/ihu-can-console.md)
and [current firmware](../../firmware/ihu/README.md). The original workflow
is available in Git history; its application and build options were removed.

## Connected hardware, 2026-10-01

- Ground host: `ember-ground`, Pi 5, `192.168.1.251`.
- IHU: RP2040, UART console through the Prolific USB serial adapter at
  `/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0`.
  UART is 115200 baud, 8N1, 3.3 V logic; IHU GP0 TX / GP1 RX, common ground.
  The existing IHU build disables USB CDC; this is a USB UART adapter connection.
- EPS: confirmed `LTC4162EUFD-LAD#TRPBF`, 2S2P 18650 pack. Use two series cells
  for voltage conversion; parallel cells do not multiply pack voltage.
- Present power: battery. Solar-charge inputs are available for a later
  controlled supply test. No input supply or charger configuration was changed.
- IHU I2C: GP4 SDA / GP5 SCL, 100 kHz, LTC4162 address `0x68`, comms slave `0x42`.
- Firmware currently assumes RSNSB = RSNSI = 0.01 ohm. Confirm the fitted values
  before treating engineering current as calibrated.

The original spare Pico remains on its separate `ttyACM` connection and the
existing Yamcs USB bridge. Do not send this interactive UART console to that
COBS packet bridge; they use different protocols.

## Baseline observed before flashing

The existing IHU console responded to the observational `eps raw` command:

| Register | Raw | Interpretation |
|---|---|---|
| CONFIG_BITS `0x14` | `0x0004` | force telemetry on |
| CHARGER_CONFIG_BITS `0x29` | `0x0000` | JEITA disabled in existing configuration |
| CHARGER_STATE `0x34` | `0x0100` | charger suspended |
| SYSTEM_STATUS `0x39` | `0x00A1` | preserve raw status and charger context |
| VBAT `0x3A` | `21322` | 8.2047056 V, two series cells |
| VIN `0x3B` | `3` | 0.004947 V |
| VOUT `0x3C` | `4952` | 8.185656 V |
| IBAT `0x3D` | `64947` = signed `-589` | -86.3474 mA with 10 milliohm RSNSB |
| IIN `0x3E` | `81` | 11.8746 mA with 10 milliohm RSNSI |
| DIE_TEMP `0x3F` | `13252` | 20.518 °C chip die, not battery |
| THERMISTOR_VOLTAGE `0x40` | `9078` | raw; no NTC temperature model assumed |

These sequential register reads are illustrative, not a simultaneous sample or
an independent calibration. The old readout does not include TELEMETRY_STATUS
or CHEM_CELLS, so ADC validity and detected cell configuration were not verified.
Compare pack and output voltage against a meter before accepting accuracy.
The comms console also reports Si5351 failure and about 3299 mV RX baseband;
these are existing bench observations, not EPS faults or RF acceptance.

## Current EPS definitions

The active IHU retains the shared LTC4162 register dictionary and observational
reader. Regenerate/check those definitions with:

```sh
python3 ground/ember/generate_ltc4162.py firmware/shared/ltc4162_registers.h
python3 test/firmware/test_ltc4162.py
```

Current IHU `eps json`, output switches, ADC overrides and sole-console-owner
requirements are documented in the [IHU guide](../../docs/user/ihu-can-console.md).
The historical `eps raw`, `quiet`, `kick`, `ntc-bypass` and FreeRTOS build options
are not the active application interface.
