# Ground station lab TODO

Updated 2026-10-01. This checklist owns the ground station lab build; the
[root TODO](../../TODO.md) links here. Packet specifications belong in
[command](../protocols/command.md) and [telemetry](../protocols/telemetry.md).
Host locations and Pico build commands are recorded in the
[development baseline](../integration/development_baseline.md).

## Objective and first acceptance test

Build a self-contained bench module that sends commands to a spacecraft
endpoint and receives, displays, and archives telemetry. Operate it from a
laptop browser over the local network. Develop this before the flight comms
board is finished, then reuse the packet interface with that board.

First acceptance test: issue `SET_PARAMETER(TELEMETRY_PERIOD, value)` from the ground web UI,
receive correlated acceptance and completion reports, and observe the new
interval in archived telemetry. Also demonstrate rejection of an invalid
command and timeout handling when its response is lost.

Merged baseline: `ebeec2f` includes PRs #2, #3, and #4. Adopt Dustin’s
[operations dictionaries](../../docs/architecture/operations/Ground_Operations_Command_Telemetry/README.md)
for application meanings and preliminary IDs. Remaining repairs and deliverables
are in the [Dustin coordination note](dustin_followup.md).

PR #5 is now merged at `a21832b`: the Pi/Yamcs dictionary and simulated loop
are the established lab baseline. Next branch: `feature/ground-station-usb`,
starting with the [one-Pico USB hookup](usb_bench_setup.md).

## Current direction and open decisions

- Flight comms is **UHF uplink / UHF downlink**. VHF references describe an
  obsolete design; do not use them as requirements for this build.
- BPSK in both directions is the current working choice. Frequencies,
  symbol rates, coding, framing, and the spacecraft receiver implementation
  still need to be settled.
- Ground host: provisioned Pi 5 / 8 GB, `ember-ground`, Ethernet
  `192.168.1.251`, 128 GB SD. Laptop runs the browser. Yamcs is running;
  modem performance, cooling and USB power remain to verify.
- Software: Yamcs `ember` instance and simulated command loop verified on the
  Pi; `myproject` preserves the upstream reference. USB packet bridge and Pico endpoint are verified; the
  radio bridge and GNU Radio BPSK modem remain to implement. The
  [bench v1 dictionary](../protocols/ember_bench_v1.md) uses CCSDS SPP;
  flight allocation and a possible ECSS PUS subset remain open.
- First hardware transport: direct USB from Pi to one spare RP2040 Pico.
  Then use two Pico + SX1280 endpoints, reusing the existing 2.4 GHz work.
  LoRa transport tests command/telemetry behavior; it does not
  validate the flight BPSK waveform. SX1280 and RFM95W are not native BPSK modems.
- Candidate UHF ground SDR: Pluto. Available alternatives/test instruments:
  LibreSDR, HackRF, RTL-SDR, IC-9700, and handheld radios. Select against the
  required waveform and exact device capabilities.
- Start with alternating transmit and receive. 9,600 symbols/s is a proposed
  BPSK bench setting, not a flight rate or a verified Pi performance limit.
- SatNOGS is the intended additional downlink reception/display path. Keep
  authorized command transmission under our own ground station control.

## 0. Preserve and identify the baseline

- [x] Checkpoint the current comms KiCad project, including the RF-switch
  sheet, board, project configuration, and local libraries: commit `b3f4a0d`.
  This preserves the saved files; it is not an ERC/DRC or fabrication approval.
- [ ] Reconcile the three remaining Mac checkpoint CAD differences with newer
  GitHub `main` through native KiCad/Konnect review before adopting them.
- [ ] Record the known-working Pico wiring, firmware version, radio settings,
  and a reproducible transmit/receive test before changing radio code.

Existing firmware references (separate repositories):

- `/Volumes/work/MSU_Cubesat/s-band_transceiver_payload`: radio HAL/task,
  queues, housekeeping, CAN integration, SX1280 and RFM9x drivers. The HAL
  currently exposes init/TX; the RF command handler is a parsing/dispatch stub.
  Its underlying SX1280 driver has receive methods to evaluate.
- `/Volumes/work/MSU_Cubesat/sx1280-pico`: Semtech driver port and Pico/FreeRTOS
  HAL. The checked-in example tests SPI/firmware identification; bidirectional
  packet operation still needs a reproducible demonstration.

## 1. Ground module and host

- [x] Select and provision the Pi 5 / 8 GB with 64-bit Trixie, static Ethernet,
  key-only SSH and verified sudo; [lab inventory](lab_inventory.md).
- [ ] Assemble a panel with cooling, storage, power distribution, USB, Ethernet,
  Pico/radio mounting, and labelled RF connections.
- [ ] Confirm USB power budget; use a suitable supply or powered hub as needed.
- [x] Set hostname, network access, and browser-accessible Yamcs on the Pi:
  `http://192.168.1.251:8090`.
- [x] Configure startup on boot and bounded container logs; verify a full Pi reboot.
- [ ] Configure telemetry retention and archive backup.
- [x] Add a pinned, reproducible [Yamcs starter lab](../../ground/yamcs/README.md)
  with isolated simulator and persistent archive storage.
- [x] Verify starter telemetry, sample command receipt, packet archiving and
  recovery after server restart on m75q; [validation record](starter_validation.md).
- [x] Verify Pi starter telemetry, simulator command receipt, packet archive,
  laptop browser access and archive survival across a full Pi reboot.
- [x] Open native parameter plotting from the system display and verify
  archived/live telemetry on the Pi.
- [ ] Exercise interactive archive replay on the Pi.
- [x] Add native EMBER overview and detail displays, with received timestamps,
  RSSI-unavailable handling and navigation to command history;
  [display setup](../../ground/yamcs/DISPLAYS.md).
- [ ] Add a processor-aware freshness indication that expires appropriately
  across the configurable telemetry period and during replay.

## 2. Packet contract and wired command loop

- [x] Define bench APIDs, byte order, schema version, length/size checks,
  uptime, units and sequence behavior; add a host codec and literal vectors
  in [ground/ember](../../ground/ember/README.md).
- [x] Draft bench arguments, correlated acceptance/rejection/completion/execution
  failure and timeout/retry/duplicate/reset rules in the
  [contract](../protocols/ember_bench_v1.md).
- [ ] Review bench parameter/stage/reason IDs and semantics with Dustin;
  freeze flight APIDs, timestamps and packet limits separately.
- [ ] Define uplink authorization/authentication and replay handling for the
  flight path; document how the lab exercises those checks.
- [x] Implement host encoding/decoding for `PING`, `REQUEST_STATUS`,
  `REQUEST_TELEMETRY`, `SET_PARAMETER(TELEMETRY_PERIOD)`, `HEARTBEAT`,
  `SYSTEM_STATUS`, `COMM_STATUS` and `COMMAND_RESPONSE`.
- [x] Implement EMBER simulator handlers, correlated result lifecycle and
  telemetry scheduling. Verify 1000→2000 ms in archived packets, query data,
  invalid-argument rejection and lost-response TIMEOUT/UNKNOWN on Pi/m75q.
- [x] Verify duplicate suppression, transaction conflict, malformed/unknown
  commands and bounded/reset cache behavior in simulated endpoint tests.
- [x] Implement that validated command subset and bounded parser on the Pico;
  repeat duplicate/reset tests with hardware.
- [x] Connect and identify a spare RP2040 Pico on the Pi USB host; record its
  model/USB identity and load the dedicated USB bench build when ready.
  Existing IHU firmware uses UART stdio with USB CDC disabled.
- [ ] Generate an unsolicited simulated event, preserve it during link loss,
  and deliver/deduplicate it after recovery without an operator command.
- [x] Generate Yamcs EMBER mission database and Java wire offsets from JSON;
  validate CRC/length/identity before archive and correlate native command
  acceptance/completion history. Send SET_PARAMETER from the laptop browser.
- [ ] Reconcile pending history after ground service restart and late results
  after timeout; expose an identity-preserving manual retry when appropriate.
- [x] Implement a USB/serial-to-UDP bridge with explicit framing and separate
  debug output. Preserve the same CCSDS packet bytes across transports.
- [x] Prove the first acceptance test over USB with the spacecraft Pico.

Evidence: [software validation](ember_validation.md) and
[USB hardware validation](usb_validation.md). USB acceptance is complete; RF
acceptance remains open. Next: record the existing SX1280 wiring/settings and
build the two-Pico RF transport using the same packet interface.

## IHU/EPS bench while RF hardware is unavailable

Details and observed baseline: [IHU/EPS UART bench](eps_bench_setup.md).

- [x] Identify the connected IHU UART adapter, confirm LTC4162-LAD and 2S2P
  battery configuration, and capture existing telemetry without charger changes.
- [x] Define the observational register dictionary and generated shared header;
  check signed scaling and ADC/chemistry/cell-count rejection on the host.
- [x] Build the default read-only IHU image in the m75q Pico SDK container.
- [x] Add default read-only charger operation, bounded LTC4162 transactions,
  complete raw/JSON console readouts, and invalidation after failed EPS polls.
- [x] Back up assembled IHU firmware over direct USB, load and verify the
  diagnostic image, and capture all 19 registers on hardware.
- [x] Verify ADC-off battery readout is retained as raw data while engineering
  values are suppressed; confirm legacy charger CLI commands are blocked.
- [ ] Confirm fitted RSNSB/RSNSI and compare pack/output voltage with a meter.
- [x] Capture TELEMETRY_STATUS and CHEM_CELLS on battery and input power:
  ADC invalid → valid, LAD chemistry, detected two cells with input present.
- [ ] Resolve input-voltage discrepancy (12 V supply setting vs ~8.21 V VIN)
  and NTC-pause/JEITA region 7. Supply confirmed CV / 12.00 V / 38 mA,
  meter confirms 12 V at input terminals and board feeding LTC4162.
  Input discrepancy remains unresolved; checksum-verified readout next.
- [x] Build/test SMBus PEC verification, including corrupted data/checksum rejection.
- [ ] Flash PEC image and distinguish transfer corruption from ADC/analog issues.
- [ ] Document sample age and measurement limits across repeated power transitions.
- [ ] Define the versioned EPS POWER_STATUS payload with validity and freshness;
  implement IHU telemetry transport to the ground station.
- [ ] Add native Yamcs EPS display and validate it against real measurements.

## 3. Pico/SX1280 RF loop

- [ ] Expose receive operations through the existing driver/HAL layers and
  deliver validated packets to the command dispatcher.
- [ ] Implement ground USB-to-RF and RF-to-USB forwarding on the second Pico.
- [ ] Set matching radio parameters and implement TX/RX turnaround, bounded
  waits, error recovery, and receive resumption after transmission.
- [ ] Account for the existing four-byte RadioHead wrapper; bound payload
  lengths before copying and passing them through the uint8_t-length API.
- [ ] Repeat the acceptance test over RF and log packet loss, round-trip time,
  duplicates, radio errors, and endpoint resets.

## 4. UHF BPSK and flight-board integration

- [ ] Freeze a versioned waveform profile: frequencies, pulse shaping, symbol
  rates, preamble/sync, phase-ambiguity handling, whitening, CRC/FEC, framing,
  and half-duplex turnaround. Select the spacecraft demodulator implementation.
- [ ] Build a ground GNU Radio modem and an SDR-based spacecraft emulator,
  preserving the packet interface used by the Pico lab.
- [ ] Plan attenuation/protection for cabled tests using actual RF output and
  receiver input limits; test each direction independently, then round trips.
- [ ] Benchmark modem + Yamcs on the selected Pi: CPU/RAM, dropped samples,
  archive writes, and sustained decoding at the selected sample/symbol rates.
- [ ] Exercise frequency offset, simulated Doppler, weak signals, and corrupted
  frames. Archive representative IQ captures and expected decoded packets.
- [ ] Replace the emulator with the flight board and repeat command-loop tests,
  including RF inhibits, command rejection, watchdog/reset, and safe-mode behavior.

## 5. SatNOGS integration

- [ ] Check the exact BPSK waveform profile against available SatNOGS demodulator
  and framing support before freezing the flight implementation.
- [ ] Publish a telemetry format specification and known-good packet/IQ vectors.
- [ ] Develop a telemetry decoder (Kaitai for satnogs-decoders) and verify
  engineering conversions against the spacecraft/Yamcs definitions.
- [ ] Coordinate mission/transmitter registration and station integration with
  SatNOGS; use an appropriate test workflow for bench data.
- [ ] Verify signal capture, packet recovery, and engineering-value display as
  separate milestones; create the mission dashboard when supported.
- [ ] Evaluate FoxTelem only if the chosen waveform/frame format makes an
  additional receiver useful; it is not a prerequisite for this ground station.

## References

- [Yamcs starter project](https://github.com/yamcs/quickstart)
- [Pluto driver installation](https://analogdevicesinc.github.io/documentation/solutions/platforms/pluto/get-started/drivers.html)
- [GNU Radio BPSK tutorial](https://wiki.gnuradio.org/index.php/Simulation_example%3A_BPSK_Demodulation)
- [SatNOGS operator guide](https://wiki.satnogs.org/Satellite_operator_manual)
