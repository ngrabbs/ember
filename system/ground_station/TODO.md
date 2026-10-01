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

## Current direction and open decisions

- Flight comms is **UHF uplink / UHF downlink**. VHF references describe an
  obsolete design; do not use them as requirements for this build.
- BPSK in both directions is the current working choice. Frequencies,
  symbol rates, coding, framing, and the spacecraft receiver implementation
  still need to be settled.
- Ground host: provisioned Pi 5 / 8 GB, `ember-ground`, Ethernet
  `192.168.1.251`, 128 GB SD. Laptop runs the browser. Yamcs is running;
  modem performance, cooling and USB power remain to verify.
- Software: pinned Yamcs starter verified on the Pi. Packet/radio bridge and
  GNU Radio BPSK modem remain to implement. The
  [bench v1 dictionary](../protocols/ember_bench_v1.md) uses CCSDS SPP;
  flight allocation and a possible ECSS PUS subset remain open.
- Initial transport: two RP2040 Pico + SX1280 endpoints, reusing the existing
  2.4 GHz work. LoRa transport tests command/telemetry behavior; it does not
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
- [ ] Exercise parameter plots and interactive archive replay on the Pi.

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
- [ ] Implement command handlers, result lifecycle and telemetry scheduler in
  an EMBER simulator, then the Pico endpoint. Prove invalid arguments,
  duplicate suppression, transaction conflict and lost-response timeout.
- [ ] Generate an unsolicited simulated event, preserve it during link loss,
  and deliver/deduplicate it after recovery without an operator command.
- [ ] Define the Yamcs mission database and matching spacecraft encoder/parser.
- [ ] Implement a USB/serial-to-UDP bridge with explicit framing and separate
  debug output. Preserve the same CCSDS packet bytes across transports.
- [ ] Prove the first acceptance test over USB with the spacecraft Pico.

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
