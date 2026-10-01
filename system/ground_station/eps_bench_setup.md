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


### Supply and meter follow-up

The operator confirmed the bench supply is in CV mode at 12.00 V / 0.038 A,
and a multimeter reads 12 V at the solar-input terminals. This rules out supply
current limiting as the explanation for the earlier input discrepancy at that
measurement time. A subsequent direct `eps raw` read at roughly 442 s MCU uptime
still reports VIN `4950` (8.16255 V), ADC valid, LAD/two cells, JEITA region 7,
CONFIG_BITS `0` and CHARGER_CONFIG_BITS `1`. Charger state is now `256`
(suspended), so the earlier NTC-pause state is not assumed permanent.

VIN register address `0x3B`, little-endian read assembly and 1.649 mV/LSB scaling
were rechecked. The design guide describes connector blocking diodes and a
2.7 ohm series resistor upstream of `VIN_CHG`; this is design documentation,
not verification of the fitted board. At 38 mA the documented resistor alone
would drop only about 0.103 V, not several volts. Do not adjust the decoder to
match the supply setting without measuring the charger-side node.

Next requested measurement: charger-side VIN decoupling capacitor/test point
to board ground. If it is near 8 V, inspect the intervening input path. If it is
near 12 V, continue ADC/reference/readout investigation. Actual input-current
calibration also remains unresolved: the supply's 38 mA differs from the earlier
61–63 mA decoded using an assumed 10 milliohm resistor; the readings were not
simultaneous, so this is not yet a determined calibration error.


### Recheck requested by operator

Three additional readouts at uptime 531514–537524 ms are saved in
[input recheck evidence](evidence/ltc4162-input-recheck-20261001.json).
The first readout has ADC-valid cleared and its engineering values are
suppressed. The next two are ADC-valid and report VIN 8.180689 / 8.195530 V,
battery 8.200088 / 8.199703 V and VOUT 7.597188 / 7.595535 V. Both current words
are zero in those two readouts. Charger state transitions from suspended to
battery detection (`2048`), with JEITA region 7 retained. Configuration words
remain unchanged (`0` / `1`). The VIN discrepancy persists; no physical
charger-side VIN measurement or explanation for these transitions is available.


### Charger-input confirmation and checksum audit

The operator subsequently confirms a good 12 V on the board feeding the LTC4162,
measured with a digital multimeter. The several-volt difference remains
unexplained; it is not accepted as an input-path drop without further evidence.

The driver address (`0x3B`), repeated-start Read Word sequence, low/high byte
assembly and 1.649 mV/LSB conversion match the LTC4162-L datasheet. To test
transfer integrity independently of engineering scaling, a new image requests
and checks the optional SMBus PEC byte on every LTC4162 word read. CRC includes
write address, command, read address and both data bytes, using the
[SMBus 2.0 PEC specification](https://www.smbus.org/specs/smbus20.pdf).
Checksum failures reject the whole readout without replacing its output.

The six host test methods pass with the added checksum checks. The actual C
mock exercises a fixed golden PEC (`D0 3B D1 FF FF` → `2E`), altered data and
altered PEC rejection in both read-only and legacy-write builds. ARM Release
build passes. Prepared image `ihu-eps-pec-20261001.uf2` SHA-256:
`6bd2a4462939a8955bd8dadcc135bfe4ba89e0a33715b9b5111ac0a30c1227f8`.
This image was subsequently loaded and checked on hardware as recorded below.
Earlier captures did not verify PEC. A valid checksum validates the
transfer, not ADC calibration, sample freshness or analog hardware health.


### Checksum-enabled image hardware validation

The IHU was again identified in BOOTSEL by flash ID `E663682593923F31`.
The prepared PEC image hash matched, and `picotool load -v -x` passed flash
verification. UART confirms the new build booted, both I2C devices remain
available, and read-only charger configuration is preserved.

Three complete JSON readouts at uptime 9826, 12833 and 15840 ms are saved in
[PEC-enabled input samples](evidence/ltc4162-pec-input-20261001.json).
All 19 words in each readout passed firmware PEC verification. ADC-valid is
set, LAD chemistry and detected two cells are retained, CONFIG_BITS is `0` and
CHARGER_CONFIG_BITS is `1`. Decoded ranges:

| Field | Range |
|---|---|
| Battery pack | 8.19509–8.19586 V |
| VIN | 8.15431–8.16090 V |
| VOUT | 7.59719–7.60049 V |
| Battery/input current | 0 mA in these three readouts |
| Die temperature | 24.517–24.560 °C |

Charger state alternates between battery detection and suspended. An additional
raw dump contains nonzero current words, so zero current in these three samples
is not assumed a permanent condition. The ground decoder agrees with the
accepted raw words. Routine UART output was restored. The separate USB packet
bridge remains active and the Yamcs instance remains RUNNING.

This establishes that the unexpected VIN words arrived with matching chip PEC,
not that their analog accuracy is correct or that every transfer is reliable.
Do not calibrate the VIN scale against one supply setting to hide the discrepancy.
The next requested physical readings are VCC2P5 (pin 8, nominal 2.5 V), INTVCC
(pin 2, nominal 5 V), and VOUTA (pin 3, analog system supply), all relative to
the chip ground. Use bypass capacitors/test points when accessible. These pin
functions are defined on datasheet page 10 (PDF page index 9). Their readings
are not yet available; no ADC/reference or chip defect is established.


### Physical rail readings and suspected pin 3/4 junction

The operator measured VCC2P5 (pin 8) = 2.48 V, INTVCC (pin 2) = 4.8 V,
and VOUTA (pin 3) = 7.59 V, and supplied a microscope photograph pointing to
a possible connection between pins 3 and 4. The two internal rails are near
nominal; these DC readings do not exclude ripple or intermittent supply faults.
The measured VOUTA agrees with the approximately 7.60 V VOUT ADC readout,
so a common scale error across all voltage channels is not supported.

A read-only XML netlist export of the repository schematic confirms U1 pins
3 (VOUTA), 4 (CLN), 27 and 28 (VOUT) share `/Solar_Charger/VOUT_PP`, together
with C4/C5, RS1 pin 2 and Q2 drain-side pads. The design guide independently
connects VOUTA to CLN. Therefore a pin 3-to-4 connection is intentional for
this design and should not be removed merely because it appears bridged.
The photograph alone does not establish physical pin numbering or whether
the visible junction is copper, solder or contamination. No CAD edits or
physical repair were performed. The export warns of annotation errors; this
connectivity check is not a full design validation or confirmation that the
assembled board matches this repository revision.

Next discriminating VIN check: meter at U1 VIN pin 7 itself (or verify the
pin-to-pad joint), using chip ground. The exported net places VIN pin 7,
C3 pin 1 and solar connector positives together on `VIN_CHG`. A connector/pad
reading of 12 V does not by itself verify an intact joint to the IC terminal.
If pin 7 itself is at 12 V during a PEC-verified ~8.16 V report, VIN-specific
analog/chip behavior remains under investigation. No defect is established.


### VIN pin measurement and intervening resistor

The operator measured U1 pin 7 at 8.168 V, agreeing with PEC-verified telemetry.
This resolves the earlier suspected telemetry/meter disagreement: the measured
12 V upstream is not the voltage present at the IC terminal. The operator then
identified a resistor between the solar input and pin 7; its reference, value,
exact current path and board revision are not yet established.

If that resistor carries the entire previously reported 38 mA supply current,
(12.00 - 8.168) / 0.038 gives an effective resistance of about 100.84 ohm. This
is an inference from nonsimultaneous measurements and a current-path assumption,
not a resistance measurement or proof the fitted part is 100 ohm. A 2.7 ohm
resistor carrying 38 mA would drop about 0.103 V.

Direct visual review of datasheet Figure 8 revealed an error in the repository
schematic guide: the 2.5 ohm damping resistor is in series with a bulk capacitor
in a shunt branch to ground, not in series with the main DC solar feed. The
guide's topology/table were corrected. The earlier prose reference to a
series solar-feed damping resistor must not be treated as correct design
intent. This is a documentation correction only; no CAD or physical changes
were made. The exported current schematic net already directly joins solar
connector positives, C3 pin 1 and U1 VIN pin 7. The assembled resistor therefore
requires reconciliation with that revision rather than blind removal.

The operator was asked for its reference/marking or an unpowered resistance
measurement. Isolation may be needed for a reliable in-circuit resistance
reading. Charging/NTC behavior and fitted current sense calibration remain open.


### Isolated resistor and recovered VIN reading

The operator identified the intervening resistor marking as `2R70` (2.70 ohm),
reported 259 ohm in circuit with power removed, and approximately 109 ohm after
lifting it. An isolated resistor reading on its terminals is inconsistent with
its marked value. The earlier inferred approximately 101 ohm path resistance
is consistent in magnitude, but nonsimultaneous voltage/current readings do not
establish an exact resistance or exclude joint problems.

The operator subsequently reported 10.7 V at pin 7. Exact rework (replacement
versus jumper) and the new supply voltage/current are pending confirmation.
Three PEC-verified, ADC-valid readouts agree with that meter reading:

| Field | Range |
|---|---|
| VIN | 10.677275–10.680573 V |
| VOUT | 10.063464–10.066770 V |
| Battery pack | 8.183542–8.184311 V |
| Battery current | -3.372 to -1.466 mA, assuming 10 milliohm RSNSB |
| Input current | 90.452–93.971 mA, assuming 10 milliohm RSNSI |
| Die temperature | 26.5595–26.6025 °C |

[Captured samples](evidence/ltc4162-input-10v7-20261001.json) have ADC-valid set,
LAD chemistry, two detected cells, CONFIG_BITS `0`, CHARGER_CONFIG_BITS `1`,
charger state `32` (NTC pause), charge status `0`, and JEITA region `7`.
VIN now agrees with the physical terminal measurement at two operating points
(8.168 V and approximately 10.7 V); the prior suspected VIN decoding discrepancy
is resolved. This does not establish full calibration or explain any remaining
drop from the supply, whose present reading has not been reported.

Charging remains inhibited by the thermistor qualification path. Raw thermistor
words are 536–588, without a fitted-thermistor/bias model to convert them into
battery temperature. Presence and values of the actual battery thermistor are
requested. The firmware still makes no charger configuration changes.


### Input repair confirmed; thermistor divider pending

The operator confirms the lifted input resistor was replaced by a wire jumper.
A blocking diode is present between the solar supply connection and pin 7;
the supply now reads 11 V and pin 7 approximately 10.69 V. The approximately
0.31 V difference is consistent with a forward-biased blocking diode at this
operating point. This resolves the reported supply-to-VIN discrepancy after
the input repair. Resistor reference and reconciliation with the assembled
board revision are still pending; no CAD modification was performed.

No battery thermistor is fitted. The operator installed a substitute resistor,
but its value and wiring are not yet confirmed. The exported schematic nets
contain no connections to U1 pins 9 or 10, so the presence of a complete
on-board NTC divider must not be assumed from the current repository design.
Bench wiring must be inspected and measured directly.

The expected circuit is:

```text
NTCBIAS (pin 9) -- Rbias -- NTC (pin 10) -- Rthermistor -- GND
```

The datasheet requires Rbias to match the thermistor's nominal resistance.
For a controlled room-temperature substitute, equal known Rbias and dummy
resistance produce a midpoint reading. For example, 10 kohm / 10 kohm gives
about 0.6 V at NTC while the 1.2 V bias is active and a raw ADC near 10914.
This simulates a nominal-temperature resistance and does not measure battery
temperature. Qualifying the divider may enable charging without a software
write; a dummy resistor is a supervised bench setup, not battery thermal sensing.

Next requested checks with all power disconnected: identify the substitute's
marking/value and its two connected nodes, and measure/identify the resistor
between pins 9 and 10. In-circuit resistance can include other paths. Once the
wiring is established, read the raw thermistor ADC and JEITA region again.
NTCBIAS is applied during measurement; low-power telemetry is sampled roughly
every five seconds, so a DMM may average the bias pulses. A low average meter
voltage alone does not prove the bias output is defective. JEITA remains enabled
and firmware configuration writes remain disabled.


The operator deferred the thermistor wiring/resistance measurements for a later
bench session. They are recorded explicitly in TODO, followed by a repeat
thermistor/JEITA/charger-state capture after the divider is established. No
hardware rewiring, temperature bypass or charger configuration change was made
in response to that deferral. Charging acceptance remains open; telemetry and
ground display integration can proceed with the actual NTC-pause state visible.
