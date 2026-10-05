# Observational EPS POWER_STATUS payload v1

This extends [EMBER bench v1](ember_bench_v1.md) using Dustin's preliminary
telemetry ID `0x10`. It is a lab contract; flight allocation remains open.
[The JSON dictionary](../../ground/ember/dictionary.json) owns wire order,
widths, enums and scaling. Total packet length is 128 bytes, including the
existing header and CRC-16. Existing command/telemetry bytes are unchanged.

## Provenance and time

The Pi polls the IHU's literal `eps json` UART command every five seconds.
The IHU reads all 19 LTC4162 registers with SMBus PEC verification. The Pi
packages that observational JSON into CCSDS and sends one status packet per
second to Yamcs's separate `eps-uart-in` link. There is no EPS command link
or charger write path. UART text and CCSDS packets remain separate transports.

`provenance=IHU_UART_PI_WRAPPER` explicitly identifies ground packaging.
For this wrapper only, common `source_boot_id` is the nonzero random **Pi
bridge session ID**, repeated in `bridge_session_id`; it is not a detected
IHU boot ID. Common `uptime_ms` is bridge process uptime. The source endpoint
is IHU because the observations originate there. Its sequence tracker is
isolated from the spare Pico's UDP link. `ihu_readout_uptime_ms` comes directly
from the IHU's JSON, after the register reads; IHU boot identity is unknown.

Native IHU packets use `provenance=IHU_NATIVE` (2), with actual IHU boot and
uptime in the common header, `bridge_session_id=0`, and readout completion uptime
from IHU. For manual and native-timer emission, readout_count counts complete reads
packaged into native packets; readout_age_ms=0 at packet construction. Failed
reads emit no native packet. ADC validity and sense-resistor assumptions retain
the same quality rules. This identifies the producer, not a transport or proof
of RF delivery. Native LTE packets enter the isolated Yamcs `ember-lte`
instance; native SDRB/UHF packets enter `ember-uhf` on a separate UDP link.
The Pi UART wrapper remains in `ember`. Both RF paths are telemetry-only bench
configurations; timer submissions do not prove reception. See the [operator capability table](../../docs/user/yamcs.md#instances-and-endpoints).

Yamcs generation time equals ground packet reception time. `readout_age_ms`
is Pi monotonic time since the last complete accepted UART readout, capped at
`0xfffffffe`; `0xffffffff` means never received. It is **not ADC conversion
age**. Registers are sequential observations, not an atomic chip snapshot.
Repeated status packets are not new ADC samples. `readout_count` increments
only on a complete accepted readout and wraps at 32 bits.

## Quality and engineering values

| Field | Meaning |
|---|---|
| `payload_version` | 1 |
| `link` | DISCONNECTED, WAITING, LIVE, READ_TIMEOUT or INVALID_READOUT |
| `readout_present` | At least one complete readout exists in this bridge session |
| `readout_valid` | Last readout exists, link is LIVE and its age is at most 12 s |
| `adc_valid` | Last raw TELEMETRY_STATUS bit 0; not itself a freshness flag |
| `conversion_valid` | Current readout valid, ADC valid, compatible L chemistry and cell configuration |
| `configured_cells` | Explicit confirmed board series count: 2 here |
| `detected_cells` | CHEM_CELLS low nibble; zero uses confirmed board configuration |
| `sense_values_verified` | 0 until the fitted sense resistors have been confirmed |
| `rsnsb_microohms`, `rsnsi_microohms` | Explicit conversion assumptions; currently 10000 each |

Engineering fields are signed i32 fixed-point values on the wire: battery,
input and output voltage in mV; battery and input current in uA; die temperature
in millidegrees Celsius. Yamcs's dictionary-generated 0.001 calibrator exposes
V, mA and degC. Invalid conversions use `INT32_MIN`, excluded by a raw XTCE
valid range so Yamcs marks the value INVALID. A conversion-invalid context
calibrator produces engineering NaN, so plots show gaps instead of numeric
sentinel spikes. The raw sentinel remains auditable; it is not a measurement.

All 19 raw words are retained exactly as unsigned u16, including signed ADC
bit patterns. On failed/disconnected reads these are the **last successful
readout**, gated by presence/validity/age; before any readout they are zero
placeholders. Consult the [register dictionary](../../ground/ember/ltc4162.json)
for signed interpretation and conversions. Negative battery current is retained.
Current uses assumed 10 mOhm resistors and is provisional. Die temperature is
not battery temperature; no thermistor temperature or state of charge is inferred.

The bridge sends health packets through UART loss, suppressing engineering
values. If the bridge itself stops, POWER_STATUS's XTCE rate expires its
parameters after 1.9 s under Yamcs 5.13.0's default expiration tolerance. The
native display uses parameter validity/expiration, not the laptop wall clock.
Realtime failure behavior is verified; interactive replay remains to exercise.
Packet-specific boot/uptime aliases keep other displays from mixing headers
between the real EPS wrapper and the spare Pico.
