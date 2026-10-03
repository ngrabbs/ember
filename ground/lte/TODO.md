# LTE-M bench and spacecraft channel TODO

Updated 2026-10-02. Bench success is the immediate goal. Spacecraft items are
later validation gates, not prerequisites for getting practical LTE experience.

Native EPS full-chain uplink is proven. The latest fixed-security ten-run bench
series delivered **9/10** byte-exact128-byte packets into Yamcs; **8/10** passed
all checks. One send lost registration and was rejected; one successful delivery
had a controller diagnostic reply failure. All ten confirmed Walter OFF; no
network process crashed. The preceding series delivered6/10. Continuous delivery
and recovery remain open. [Latest results](results/2026-10-02-eps-security-reliability.md).

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

- [x] Install UHD tools on the Pi; record version and image compatibility.
- [x] Stage the custom FPGA image privately and verify checksum.
- [x] Confirm reliable USB connection; test a USB 3 cable/port if needed.
- [x] Run UHD discovery/probe using the explicit custom image, without an eNodeB.
- [x] Record radio serial, driver/firmware/FPGA versions, clock configuration.
- [x] Verify receive-only streaming at 15.36 Msps for 10 s without overruns.
- [ ] Verify full-duplex timed streaming and eNodeB processing performance.
- [x] Confirm antennas attached to all LibreSDR connectors.
- [x] Independently observe LibreSDR TX tone and expected-cell PSS/SSS with HackRF.
- [ ] Obtain CRC-validated MIB and decode LTE-M broadcast/PLMN.
- [ ] Repair/reproduce CE Msg4 feedback and retransmission behavior.
      Controlled Walter ON decoded UL CCCH and generated RRCConnectionSetup;
      patched MAC-debug run recorded Msg4 DTX before the retransmission assert.
      A bounded Msg4 retry candidate now produced a retry, ACK, and RRC Setup
      Complete. Lifecycle CTest covers 11 cases; a later RF run exercised exhausted Msg4
      retries and cleanup. Broader repetition/mode coverage remains outstanding.
- [ ] Investigate UE ULSCH allocation and failed-RA cleanup assertions.
      Experimental Msg3 cleanup patch built and exercised: ten BR contexts
      released, eleven responses handled, then the separate Msg4 assertion.
      Longer regression and automated coverage remain outstanding.
- [x] Trace DLSCH allocation/release and retained RAR contexts.
      Trace found seven retained RAR slots plus one system-information slot.
- [ ] Qualify the single-transmission CE-A RAR release candidate.
      Unit coverage and bounded RF runs exceeded the eight-slot pool without
      allocation assertions. PHY simulation timed out/returned zero throughput;
      a pinned-PDSCH comparison also failed. Full regression remains unresolved.
- [ ] Validate reestablishment rejection and asynchronous CCCH lifecycle fixes.
      Candidates built; CCCH wait/timeout path exercised without the old assertion.
      Rejection-ACK guard has not been exercised in the newer live trials.
- [ ] Diagnose post-attach uplink failure/reestablishment and make the data link stable.
      Six-to-eight-foot comparison completed: same gain did not complete setup;
      TX gain +10 completed attach/bearer, but UL failure preceded UDP submission.
      The HARQ correction trial delivered ten packets after a Service Request;
      initial radio-context release and later uplink failure still need tracing.
      Repeat trace identified SRB2 max retransmissions followed by RRC release.
      Dedicated downlink retry MCS correction did not eliminate that failure.
- [ ] Trace dedicated downlink HARQ/PUCCH feedback, RLC STATUS handling, and
      stale reestablishment contexts; qualify the seventh scheduler candidate.
      Metadata tracing observed three processed STATUS acknowledgments and NAS
      security completion, followed by missing acknowledgment of the RRC Security
      Mode Command (SN 3) and SRB1 retry exhaustion. RX gain 25 did not establish
      registration. All 49 existing RLC-v2 tests passed; RF cause remains open.
- [ ] Correlate SN 3's dedicated MPDCCH/PDSCH parameters and HARQ/PUCCH feedback;
      reproduce the failing PHY simulator case on a fully clean pinned baseline.
- [x] Capture dedicated uplink grants, HARQ/CRC outcomes, socket status at the
      send error, and GTP/SGi packets to separate radio scheduling from socket issues.
      Found process-0 grants with legacy process-1/5 MAC receive updates; candidate
      correction built/unit-tested. Ten matching payloads verified in GTP-U and SGi.
- [ ] Investigate OAI shutdown segmentation fault after the low-TX run.
- [ ] Establish bench RF connections, attenuation, gains, and operating band.
      Band 13 at six-inch separation now reaches a Walter-correlated CE0 request;
      earlier scans saw Verizon only. RF power/attenuation remains uncalibrated.
- [ ] Decide whether the Pi or x1c hosts the first LTE-M eNodeB based on driver
      support and measured real-time performance.

## 3. LTE-M stack feasibility

- [x] Pin an OAI revision and inspect eMTC build/configuration paths.
- [x] Initialize OAI UHD backend with LibreSDR/custom FPGA; independently detect PSS/SSS.
- [ ] Reproduce single-UE Cat-M1 operation; record supported CE/repetition modes.
- [x] Select srsEPC and verify S1 setup with OAI.
- [x] Verify IP bearer setup after UE registration: Attach Complete, RRC
      Reconfiguration Complete, Initial Context Setup Response, Modify Bearer.
- [x] Add exercised experimental OAI LTE-M config and bounded launch commands.
- [ ] If OAI fails, document the failing layer and compare repair, commercial
      software, and srsRAN implementation effort before choosing a path.

## 4. Walter and SIM

- [x] Confirm LTE/GPS antennas attached to Walter; LibreSDR antennas present.
- [ ] Confirm antenna connector routing, separation, and stable board power.
- [x] Confirm SIM readiness in no-RF mode (CPIN READY).
- [x] Match Walter's SIM to the private HSS record locally (record 4).
- [ ] Verify PLMN, authentication algorithm, OP/OPc, SQN, APN, and bands.
- [ ] Use the vendor AT reference matching UE8.2.1.0 to inspect/select LTE-M.
- [x] Record initial registration states and identify OAI random-access/RRC failures.
- [x] Compare Walter OFF/ON with Thingy powered down and preserve failure evidence.
- [x] Decode RRC Setup Complete, accepted SIM authentication, and NAS Security Mode Complete.
- [ ] Repeat cold-start SQN resynchronization through completed authentication.
- [ ] Establish Thingy firmware identity/AT interface for a controlled comparison (deferred).
- [ ] Distinguish cell acquisition, RRC,
      authentication, and bearer-setup failures.
- [x] Achieve Cat-M1 registration, authentication, and an assigned IP address.
      Walter reported registered and active PDP context 1 at 172.16.0.2.

## 5. Bench telemetry acceptance

- [x] Deliver numbered, timestamped UDP packets from Walter to a ground receiver.
      First demonstrated burst: ten of ten 128-byte packets, in order, zero
      observed duplicates, 13.2-second receive span. Stable/repeatable operation
      remains outstanding; this trial restored its bearer through a Service Request.
      Follow-up repeats delivered zero or nine packets; bounded pre-prompt sender
      retries help some reconnects but do not establish reliability.
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

The [COMMS MCU–Walter checklist](../../system/interfaces/comms_walter.md) owns
controller/UART integration and the IHU I2C-to-CAN migration. The legacy I2C link
is status/ping only; the new CAN Feather bench now forwards an IHU heartbeat.
Full IHU/EPS housekeeping/application migration remains open. LTE reliability remains shelved.

- [x] Build experimental Walter LTE sender with the pinned Arduino toolchain,
      local nonblocking AT state machine, bounded RF windows and distinct outcomes.
      [Implementation and limits](../../firmware/walter_lte_bench/README.md).
- [ ] Flash and qualify Walter LTE sender on hardware; vendor-library integration
      remains a separate choice from this local AT bench application.
      Upload completed with verified hashes; USB confirms OFF/window0. CAN/UART
      status and LTE qualification follow with USB back on IHU.
- [x] Investigate Walter GPS/Galileo and IHU-requested GNSS service; record
      radio-sharing constraints, result fields and asynchronous/cache design.
      [Research and GNSS TODO](../../system/interfaces/walter_gnss.md).
- [ ] Implement and bench-test IHU GNSS requests/results after LTE bring-up.
- [x] Preserve/verify Walter's ESP32 flash and install a pinned standalone
      COMMS UART diagnostic with its modem held in reset; USB checks passed.
      See [responder procedure](../../firmware/walter_uart_bench/README.md).
- [x] Demonstrate COMMS Feather ↔ Walter physical UART round trip: ten of ten
      exact diagnostic PING/PONG replies; no additional RX bytes over five seconds idle.
      Production telemetry service and LTE packet firmware remain open; later CAN
      forwarding milestone is recorded below.
- [x] Build a shared bounded COBS/CRC diagnostic envelope with correlated replies;
      install/readback-verify Feather and test BUSY/missing-peer timeout behavior.
- [x] Install framed Walter peer, verify upload hashes and USB behavior with modem held reset.
- [x] Run [paired packet/fault checks](../../firmware/comms_transport/README.md) with USB on Feather:
      19 exact packet echoes plus HELLO, synthetic heartbeat identity preserved,
      version/type rejection, and recovery immediately after each CRC/overflow/gap fault.
      Echo preserves opaque packets; it is not modem submission or IHU forwarding.
- [x] Replace the IHU bench module with a CAN Feather, preserve/verify both
      controller flash images, and prove physical CAN HELLO/echo at 500 kbit/s.
- [x] Forward ten hardware-IHU heartbeat packets via CAN → COMMS → Walter UART
      echo and back to IHU, with identity/sequence/CRC preserved and no new
      IHU-side CAN/fragment/timeout errors. [Evidence](../../system/ground_station/evidence/ihu-comms-walter-can-20261002.json).
- [x] Build the CAN Feather IHU's manual read-only EPS register reader with PEC
      validation and Feather SDA/GPIO2, SCL/GPIO3 I2C1 mapping; eight EPS tests pass.
- [x] Verify the new IHU's physical EPS connection and complete PEC-valid reads.
      Three complete 19-register readouts passed PEC; CAN HELLO still passes.
      [Evidence](../../system/ground_station/evidence/ihu-eps-i2c1-20261002.json).
- [x] Obtain ADC-valid voltage/current/temperature readings on the new IHU.
      Battery-only ADC enable changed only CONFIG_BITS bit2, with readback
      verified and three complete ADC-valid reads. Approximately 8.108 V pack,
      8.089 V output and 21.46 °C die. Current sense values remain unverified.
      [Evidence](../../system/ground_station/evidence/ihu-eps-battery-adc-20261002.json).
- [x] Build native EPS POWER_STATUS packet encoding and matching CAN/UART services;
      verify fixed-point/raw fields against real EPS captures in the ground codec.
- [x] Flash/readback-verify matching COMMS v2 update; local loopback, physical
      CAN HELLO and exact128-byte echo pass with zero CAN/fragment errors.
- [x] Prove real EPS packets through COMMS and Walter echo with USB back on IHU.
      Ten of ten native128-byte POWER_STATUS returns, ADC/conversion-valid1,
      source boot/sequence/raw registers preserved; no additional IHU-side
      CAN/fragment/timeout errors. [Evidence](../../system/ground_station/evidence/ihu-comms-walter-eps-can-20261002.json).
- [x] Prepare isolated Yamcs ember-lte input on loopback UDP10018 and bounded
      native packet receiver for EPC UDP51000. Running, with zero radio packets.
- [x] Run first bounded native EPS LTE trial; record EPC Attach Complete,
      application REGISTER, zero submissions/receptions and confirmed RF OFF.
      [Evidence](../../system/ground_station/evidence/native-eps-lte-20261002-01.json).
- [x] Fix Walter CEREG response spacing and preserve unsolicited registration
      updates, including bytes drained between commands; build and host tests pass.
- [x] Flash registration fix, verify image hashes and USB startup OFF/window zero.
      [Evidence](../../system/ground_station/evidence/walter-registration-v2-flash-check-20261002.json).
- [x] Retry aligned radio/receiver windows; registration and modem acceptance pass.
      [First send trial](../../system/ground_station/evidence/native-eps-lte-20261002-02.json).
- [x] Capture native EPS UDP through LTE/EPC with a 10-second send settle;
      identify exact LF-prefix/last-byte-loss corruption. Receiver rejects it.
      [Byte comparison](../../system/ground_station/evidence/native-eps-lte-20261002-03.json).
- [x] Build and host-test CR-only AT terminator fix.
- [x] Flash CR-only AT terminator fix; image hashes and startup OFF verified.
      [Evidence](../../system/ground_station/evidence/walter-cr-only-flash-check-20261002.json).
- [x] Verify exact packet bytes over LTE after CR-only terminator fix.
- [x] Receive real EPS packets over LTE and byte-match them in Yamcs archive/display.
      One packet, sequence15, native IHU provenance, all128 bytes unchanged;
      battery8.060V, output8.042V, die21.894°C. Paused replay verified visually.
      [Evidence](../../system/ground_station/evidence/native-eps-lte-20261002-05.json).
- [x] Measure ten independent full-chain attempts with firmware/profile fixed:
      six deliveries, two modem rejections, two accepted without reception;
      all ten OFF confirmations. [Results](results/2026-10-02-eps-reliability.md).
- [x] Build/test cached diagnostics carrying exact numeric/text CME detail,
      registration transitions, send prompt/OK flags and historical socket-open
      acceptance. All34 host tests and all three hardware-target builds pass.
- [x] Flash/readback-verify diagnostic IHU image; CAN HELLO and ADC-valid EPS read pass.
- [x] Flash/readback-verify matching COMMS diagnostics; CAN HELLO and128-byte
      echo pass with zero errors.
- [x] Flash matching Walter diagnostic image; all written hashes verified,
      application SHA matches prepared build, USB startup OFF/window zero.
- [x] Verify96-byte diagnostic return over physical CAN/UART with USB on IHU,
      then run bounded instrumented radio trials. Three accepted EPS packets,
      zero ground receptions; SRB2 SN0 retry exhaustion captured.
      [Results](results/2026-10-02-eps-diagnostics.md).
- [ ] Add separately bounded live socket-state probes if cached evidence is insufficient.
- [ ] Trace accepted-but-undelivered uplinks/bearer failures in OAI.
- [ ] Trace SRB2 dedicated downlink allocation/HARQ association and ULSCH context
      allocation/cleanup during reconnects; preserve assertions until explained.
- [x] Add and bench-test optional CE/context metadata trace; verify MAC block
      fit and MCS/NDI retention, and capture reestablishment before SRB2 exhaustion.
      One recovered EPS packet byte-matches the ground receiver and Yamcs.
      [Results](results/2026-10-02-ce-context.md).
- [ ] Inspect SRB2 activation/security, uplink STATUS scheduling/decoding and
      post-reconfiguration PHY transition; reproduce pool-full with owner dump.
- [x] Capture baseline SRB2 ADD/MODIFY with security mode255, inactive security
      and no container before SRB2 exhaustion; prepare negotiated-security fix.
- [x] Bench-verify new-bearer security initialization: active SRB2 integrity2,
      STATUS ACK_SN1, six exact EPS deliveries/Yamcs matches across two windows.
      Temporary traces removed; normal eight-candidate build retained.
      [Results](results/2026-10-02-srb2-security.md).
- [x] Repeat ten independent reliability attempts with the fixed security build
      and profile unchanged:9/10 exact deliveries,8/10 complete passes, all OFF.
      [Results](results/2026-10-02-eps-security-reliability.md).
- [ ] Trace cached diagnostic UNKNOWN_REMOTE_LINK reason6 after a successful
      send; attempt4 increased IHU unknown-reply counter without losing telemetry.
- [ ] Define operational CAN startup/recovery after reset; current bench images
      require the normal-mode console command on both Feathers after power cycling.
- [x] Capture a hardware modem rejection with exact CME diagnostics: attempt6
      lost registration before send, then text CME `operation not supported`.
- [x] Implement/test registration-aware Walter admission and an opt-in four-packet
      IHU bench FIFO with bounded pre-submission retry/backoff and held uncertainty.
      Radio-off capacity/retention test passed; deployment/OTA recovery are separate.
      [Preparation](results/2026-10-02-queue-preparation.md).
- [ ] Install Walter admission candidate; verify queued hardware EPS bytes at
      ground and Yamcs after an explicit radio-off wait and bounded RF window.
- [ ] Qualify registration-loss/recovery on hardware; add final-ACK handling
      before treating a modem-accepted packet as end-to-end delivered.
- [ ] Add bounded queues, recovery/backoff and duplicate handling; then rerun
      qualification and add periodic EPS streaming. Latest delivery result is9/10 (8/10 complete passes),
      not a reliable or continuous telemetry qualification.
- [ ] Integrate CAN into the full IHU/EPS and COMMS applications; add real sensor
      telemetry, periodic streaming, ground ingestion, and separately qualified uplink handling.
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
