# LTE-M bench and spacecraft channel TODO

Updated 2026-10-01. Bench success is the immediate goal. Spacecraft items are
later validation gates, not prerequisites for getting practical LTE experience.

## 1. Inventory and preserve the previous experiment

- [x] Locate the previous srsRAN checkout, version, and built eNB/EPC.
- [x] Confirm the private SIM database exists without publishing its keys.
- [x] Preserve portable ordinary LTE configs and source hashes.
- [x] Record the custom LibreSDR FPGA image path and checksum.
- [x] Confirm Pi SSH access and LibreSDR USB enumeration.
- [x] Confirm M75q SSH access and Walter AT passthrough.
- [x] Record GM02SP firmware and initial radio/registration state.
- [ ] Locate the currently flashed passthrough source and build provenance.

## 2. Ground radio bring-up

- [ ] Install UHD tools on the Pi; record version and image compatibility.
- [ ] Stage the custom FPGA image privately and verify checksum.
- [ ] Confirm reliable USB connection; test a USB 3 cable/port if needed.
- [ ] Run UHD discovery/probe using the explicit custom image, without an eNodeB.
- [ ] Record radio serial, driver/firmware/FPGA versions, clock configuration.
- [ ] Verify timed streaming at the required rate without under/overruns.
- [ ] Establish bench RF connections, attenuation, gains, and operating band.
- [ ] Decide whether the Pi or x1c hosts the first LTE-M eNodeB based on driver
      support and measured real-time performance.

## 3. LTE-M stack feasibility

- [ ] Pin an OAI revision and inspect eMTC build/configuration paths.
- [ ] Verify OAI's RF backend can operate this LibreSDR/custom FPGA combination.
- [ ] Reproduce single-UE Cat-M1 operation; record supported CE/repetition modes.
- [ ] Select EPC and verify compatibility for conventional IP bearer setup.
- [ ] Add a reviewed LTE-M config once it is actually exercised.
- [ ] If OAI fails, document the failing layer and compare repair, commercial
      software, and srsRAN implementation effort before choosing a path.

## 4. Walter and SIM

- [ ] Confirm antenna or conducted RF connection and stable board power.
- [ ] Confirm SIM presence/readiness in the required modem functionality state.
- [ ] Match Walter's SIM to the private HSS record locally.
- [ ] Verify PLMN, authentication algorithm, OP/OPc, SQN, APN, and bands.
- [ ] Use the vendor AT reference matching UE8.2.1.0 to inspect/select LTE-M.
- [ ] Record registration states and distinguish cell acquisition, RRC,
      authentication, and bearer-setup failures.
- [ ] Achieve Cat-M1 registration, authentication, and an assigned IP address.

## 5. Bench telemetry acceptance

- [ ] Send numbered, timestamped UDP packets from Walter to a ground receiver.
- [ ] Record payload size, offered rate, duration, received count, loss,
      duplicate/out-of-order packets, RTT, and modem signal metrics.
- [ ] Establish time synchronization before claiming one-way latency.
- [ ] Demonstrate command/response traffic if required by the interface.
- [ ] Test modem reset, ground restart, link interruption, and reconnect.
- [ ] Repeat the procedure from cold boot and a clean configuration.
- [ ] Preserve sanitized logs, packet captures, exact revisions, and results.

Acceptance: a repeatable Walter Cat-M1 attach and measured IP telemetry path
through an SDR eNodeB/EPC. Ordinary LTE attach by SIM7600 is a separate baseline.

## 6. Firmware and EMBER integration

- [ ] Develop in firmware/walter with a pinned toolchain and WalterModem library.
- [ ] Implement bounded queues, sequence numbers, reconnect/backoff, and watchdogs.
- [ ] Define modem startup, radio enable, shutdown, and sleep/wake behavior.
- [ ] Integrate EMBER telemetry encoding and ground ingestion.
- [ ] Measure startup, attach, idle, transmit, and recovery current/energy.
- [ ] Define command authentication and replay handling before operational use.

## 7. Spacecraft channel validation after bench success

- [ ] Define orbit/contact geometry and minimum elevation when relevant.
- [ ] Close uplink/downlink budgets using actual antenna patterns and losses.
- [ ] Determine modem frequency acquisition/tracking and timing limitations.
- [ ] Test representative propagation delay, Doppler, and Doppler rate on bench.
- [ ] Evaluate ground compensation and whether modem/vendor changes are needed.
- [ ] Verify compatibility with intended operating frequencies and authorizations.
- [ ] Budget peak/average power, attach time, pass throughput, and storage.
- [ ] Evaluate antenna deployment, pointing, polarization, and spacecraft coupling.
- [ ] Verify thermal/vacuum, radiation/reset recovery, and GNSS behavior if used.
- [ ] Keep bench, channel-emulated, and flight results explicitly distinguished.
