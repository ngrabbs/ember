# IHU/EPS UART bench

The assembled IHU can provide real power telemetry while the RF hardware is
unavailable. This connection uses the existing I2C housekeeping bus, not CAN.

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

## New observational definitions

`ground/ember/ltc4162.json` defines 19 registers, signed ADC conversions,
chemistry codes, and the authoritative
[Analog Devices LTC4162-L Rev. A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf).
Regenerate its shared C header with:

```sh
python3 ground/ember/generate_ltc4162.py firmware/shared/ltc4162_registers.h
python3 test/firmware/test_ltc4162.py
```

The new IHU build defaults to `IHU_EPS_ALLOW_CHARGER_WRITES=OFF`: it does not
force the ADC, disable JEITA, restart charging, or change thermistor thresholds.
`kick` and `ntc-bypass` are blocked. All LTC4162 transactions have bounded waits.
The bus mutex serializes readers but does not freeze ADC conversions.

`eps raw` dumps the complete dictionary. `eps json` emits the same raw words
with profile `ltc4162-l-readout-v1` and MCU uptime. Use `quiet` first for a cleaner
console capture; unsolicited alerts can still print. Save just the JSON object,
then decode it with explicitly confirmed board parameters:

```sh
python3 ground/ember/ltc4162_decode.py sample.json \
  --cells 2 --rsnsb-ohms 0.01 --rsnsi-ohms 0.01
```

The decoder retains raw words when ADC status is invalid, chemistry is not L,
or a nonzero detected cell count differs from the configured count. Engineering
values are suppressed in those cases. A detected count of zero can mean the
charger is disabled; use the confirmed board count. ADC-valid means the ADC has
completed warmup, not that each poll acquired a new conversion. A failed or
invalid firmware poll invalidates the previous engineering snapshot.

Build in the m75q container without flashing:

```sh
docker exec amsat-dev-x86 bash -lc '
  cd /workspace/MSU_Cubesat/ember
  PICO_SDK_PATH=/opt/pico-sdk cmake -S firmware/ihu \
    -B firmware/ihu/build-eps-readonly -DIHU_EPS_ALLOW_CHARGER_WRITES=OFF
  cmake --build firmware/ihu/build-eps-readonly -j4
'
```

Enabling `IHU_EPS_ALLOW_CHARGER_WRITES=ON` restores the legacy configuration
behavior, including automatic JEITA disable at boot. It is not needed for the
observational bench test. If ADC status is invalid on battery power, inspect
configuration and hardware before deciding to enable or modify the ADC.

## Remaining integration

The assembled IHU flash was backed up and the new image verified through direct
USB on 2026-10-01. The UART adapter alone does not provide a picotool flash backup.
ADC-valid input-powered readings were captured; compare voltage against a meter. Preserve
battery/supply conditions and fitted resistor values with each measurement.

The JSON console readout is a diagnostic format, not a CCSDS telemetry packet.
Next, define a versioned EPS payload for the adopted POWER_STATUS message,
including measurement validity, source age and raw diagnostic status. Add the
IHU transport and native Yamcs EPS display together so the UI shows measured
hardware data with explicit freshness. This change does not add synthetic EPS
values to the running Yamcs instance.

## Software verification

The read-only image built successfully on 2026-10-01 with Pico SDK 2.1.1 in
`amsat-dev-x86`. Five host test methods passed, covering the actual C driver
in both write-disabled and explicitly write-enabled builds, signed negative
ADC readings, little-endian words, timeout/lock failures, unchanged output on
failure, chemistry/cell/ADC rejection, zero detected cells, preserved CONFIG_BITS
flags, malformed ground readouts and generated-header consistency. The image was subsequently flashed and verified on the assembled IHU; the
baseline table above came from its previous firmware.


## Diagnostic image hardware check

The direct USB BOOTSEL device identified itself as `ihu`, RP2040 B2,
2 MB flash, flash ID `E663682593923F31` (different from the spare packet Pico).
Full-flash backup was saved and verified on the Pi and copied to the Mac:

- Backup: `ihu-before-eps-readonly-20261001.uf2`, SHA-256
  `8a98fdc72f76cc16e5665a345880fd993a6eb53dfc9179bf00a54435a9ef09d6`.
- New image: `ihu-eps-readonly-20261001.uf2`, SHA-256
  `28816c803930c903265c02d42c56702a7542ced1fd677aad8e5a4fa20baecc71`.
- Pi copies are under `/home/ngrabbs/`; Mac copies are under
  `/Users/nick/Documents/ChatGPT/EMBER/`.

Flash verification passed. UART boot confirms both I2C devices (`0x42`, `0x68`),
read-only operation and successful comms housekeeping. `eps json` returned the
complete 19-register object. Both `kick` and `ntc-bypass on` were rejected without
configuration changes; periodic output was restored with `loud` afterwards.

After the BOOTSEL/flash procedure, the battery-powered EPS reported its default
CONFIG_BITS `0` and CHARGER_CONFIG_BITS `1` (JEITA enabled), charger suspended,
TELEMETRY_STATUS `0`, CHEM_CELLS `0x00E0`, and zero ADC measurements. The diagnostic
firmware does not force the ADC on, so these zeros are not reported as valid
voltages/current/temperature. The ground decoder confirms LAD chemistry,
zero detected cells and configured two cells, with `conversion_valid=false`
and `engineering=null`. See the
[captured raw sample](evidence/ltc4162-battery-adc-off-20261001.json).

The earlier valid-looking readings came from the prior configuration with
force_telemetry_on set. Input-powered ADC-valid measurement is recorded below; independent
calibration remains open. ADC enable on battery will need a deliberate, narrowly
scoped operation if required. Do not enable the legacy write build merely to
obtain battery telemetry, because it also changes JEITA and charger state.


## Input-powered readout, 2026-10-01

The operator applied a supply set to 12 V to the solar input, leaving the battery
connected. Three readouts at MCU uptime 217709, 220715 and 223721 ms report
TELEMETRY_STATUS `1` (ADC valid), CHEM_CELLS `0x20E2` (decoded LAD / two cells),
CONFIG_BITS `0`, CHARGER_CONFIG_BITS `1`, CHARGER_STATE `32` (NTC pause),
CHARGE_STATUS `0`, SYSTEM_STATUS `0x0067`, and JEITA region `7`.
Full raw readouts are preserved in the
[input-powered samples](evidence/ltc4162-input-power-20261001.json).

| Measurement | Decoded range over three sequential readouts |
|---|---|
| Battery pack | 8.20586–8.20624 V |
| VIN at charger | 8.21202–8.21532 V |
| VOUT | 7.57239–7.57405 V |
| Battery current | -40.90 to -39.14 mA |
| Input current | 61.72–63.33 mA |
| Chip die temperature | 22.02–22.19 °C |
| Thermistor ADC | 784–796 raw; no battery temperature conversion |

The ground decoder accepts all three samples and agrees with the IHU console
within its display rounding. Current still assumes the unverified 10 milliohm
sense resistors. These samples validate decoding and ADC gating, not independent
calibration, charging operation, or new ADC conversion for every read.

Two unresolved observations must carry into the next test:

- The supply setting was 12 V, but decoded charger VIN is about 8.21 V.
  Its conversion was rechecked against the official datasheet's 1.649 mV/LSB.
  Read actual supply voltage/current and CV/CC indication, then measure input
  terminals and the charger-side VIN test point if accessible before deciding
  whether this is supply droop, input-path behavior, wiring or another issue.
- Charging is paused in JEITA region 7. The datasheet identifies region 7 as an
  out-of-range thermistor condition; this does not prove the battery is hot.
  Die temperature is a separate measurement. Check the actual NTC/bias wiring
  and values; do not bypass the temperature guard as part of this readout.

Firmware remains observational: no ADC-force, JEITA-disable, charger-kick or
threshold writes were issued. Routine console output was restored after capture.
