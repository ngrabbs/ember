# Ground radio bring-up — 2026-10-01

## Verified observations

On `ember-ground`, installed Debian UHD `4.8.0.0+ds1-2` with host utilities and
Python bindings. Staged the existing custom FPGA image under
`/home/ngrabbs/work/ember-lte/images`; its SHA-256 matches the inventory.

Downloaded only `b2xx_common_fw_default` from the UHD 4.8 manifest. The archive
is `b2xx_common_fw_default-g7f7d016.zip`, containing USB-controller firmware
`usrp_b200_fw.hex`. This is separate from the user-supplied FPGA image.

Initial discovery failed due to missing firmware, then USB permissions. Reloading
UHD's installed udev rules and triggering the matching USB device resolved
permissions without running the radio applications as root.

The successful probe explicitly selected the custom FPGA and reported:

- Name `LibreSDR B210mini`, serial `D5I16MA`, board revision 4.
- Firmware version 8.0, FPGA version 16.0.
- Both register loopback tests passed.
- No internal GPSDO; automatic initial master clock 16 MHz.
- USB 3 operation. `lsusb -t` confirmed 5000 Mbps after firmware loading,
  compared with 480 Mbps before loading. No cable change was needed.

## Receive-only transport benchmark

[Captured benchmark output](2026-10-01-rx-15m36.txt).

One channel, 15.36 Msps, 10 seconds, UHD fc32 CPU/sc16 wire defaults. UHD selected
61.44 MHz master clock for this rate.

| Counter | Value |
|---|---:|
| Received samples | 153600038 |
| Dropped samples | 0 |
| Overruns | 0 |
| RX sequence errors | 0 |
| RX timeouts | 0 |
| Late commands | 0 |
| Transmitted samples | 0 |

Exit status 0 with overrun/drop/sequence thresholds set to zero. This validates
the receive transport path for this short test, not full-duplex or LTE attach.

## Walter follow-up

Read-only AT queries on the M75q returned `+SQNMODEACTIVE: 1` (LTE-M), band
profiles including a standard LTE-M profile with bands
1,2,3,4,5,8,12,13,17,18,19,20,25,26,28,66, and PDP context 1 with IP type and an
empty APN. Profile listings do not establish which operator-specific profile
will be selected. No RAT, band, APN, or functionality changes were sent.

User subsequently confirmed both LTE and GPS antennas attached to Walter;
LibreSDR also has antennas attached.

## OAI investigation

Pinned current develop commit `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f` on x1c and
the Pi. Current code contains MPDCCH generation, SIB1-BR/SI-BR scheduling, and a
Cat-M scheduler with a comment describing one repetition and one HARQ process.
This is source evidence, not demonstrated interoperability.

x1c configuration stopped on missing OpenSSL development metadata; sudo needs a
password there. The Pi has space and noninteractive sudo, so it is the first
build candidate. M75q root has about 2.6 GB free; its mounted BACKUP-A drive is
an alternative build location if necessary. No user files were removed.

The complete LTE-M config under `targets/PROJECTS/GENERIC-LTE-EPC/CONF` passes
libconfig syntax validation. Its adapted local copy in configs/oai also passes.
The CI untested config failed at line 359 (`port 36412` without `=`); its tail
also omits closing L1/RU configuration. Neither syntax check verifies RF startup.

A no-RF modem test sent CFUN 4, which the modem accepted, then read CPIN and
CIMI. Both failed to provide SIM readiness/identity; CFUN 0 was restored.
A subsequent diagnostic attempt encountered a USB disconnect before sending
its commands. The USB device was visible again afterward. Physical SIM
presence and stable serial behavior remain to be checked.

After the user inserted the SIM, CFUN 4 no-RF mode returned CPIN READY and a
valid IMSI matching HSS record 4 (Milenage). CFUN 0 was restored. Full IMSI
and keys were not displayed or added to Git.

OAI lte-softmodem, oai_usrpdevif, and rfsimulator compiled successfully on
the Pi without source patches. An initial simulated-radio startup identified
missing dynamically loaded configuration/PHY modules; these are separate build
targets and are being added to the launch procedure.

With the dynamically loaded params_libconfig/coding/dfts modules available,
a 15-second bounded OAI run using `--rfsim --noS1` encoded LTE-M SIB2/3,
initialized the eMTC PRACH thread, and reported `ALL RUs ready - ALL eNBs ready`.
It then tried to connect to the default RF-simulator endpoint; no simulated UE
was running. The process was stopped by the timeout (exit 124) and printed Bye.
This establishes LTE-M configuration/initialization progress without radio
transmission; it does not establish frames exchanged or UE interoperability.

## EPC/S1 and first OTA attempts

Built all OAI runtime modules and srsEPC on the Pi (see BUILD.md). Private HSS
records were staged with mode 0600. A first simulated S1 attempt exposed a
local PLMN adaptation error; correcting MNC to 70 produced S1 Setup Response
from srsEPC, with OAI accepting served GUMMEI/PLMN data. This is control-plane
startup evidence, without a UE or radio transmission.

A bounded hardware run initialized custom-image LibreSDR at 15.36 Msps in both
directions and completed S1 setup. Default threaded processing logged roughly
73,778 `L1_thread isn't ready` messages. Walter accepted APN `srsapn` and CFUN 1,
but a pending COPS selection was not given enough time before further commands;
those blank responses are not valid registration-failure evidence. The cell was
stopped and Walter was reset through the passthrough and confirmed at CFUN 0.

A 20-second `--noS1` single-thread/worker-disabled run had zero such L1 messages,
but many random-access detections while Walter's radio was off. These are not
UE attach evidence. UHD RX gain was 65 dB.

A subsequent full EPC/hardware run used the same single-thread settings and
RU `att_rx=30`, yielding logged UHD RX gain 35 dB (TX stayed 29.75 dB). During
inspection it had zero L1-not-ready messages, zero generated RARs, no assertion,
and successful S1 setup. Walter's manual PLMN selection completed with
`+CME ERROR: no network service`. No RRC connection or SIM authentication was
observed. Later queries confirmed LTE-M, APN `srsapn`, standard band profile
including band 13, CEREG searching, CSQ 99/99 and all-unknown CESQ fields.
CFUN 0 was acknowledged after those queries.

Failure is currently before demonstrated cell acquisition/random access.
Successful EPC startup does not establish a usable Cat-M1 waveform. RF output,
antenna/connector routing, Walter's active band/profile, and broadcast decoding
remain diagnostic targets. No IP bearer or telemetry transfer has succeeded.

## Band-limited scan at lower transmit gain

User reported approximately six inches between Walter and LibreSDR. A separate
candidate runtime config increased `att_tx` to 80; UHD logged TX gain 9.75 dB,
RX gain 35 dB. Single-thread/worker-disabled hardware processing again logged
zero L1-not-ready messages, zero RARs, zero RRC connections, and no assertion.

Using the vendor library's `SQNBANDSEL` syntax, temporarily set Walter's standard
LTE-M profile to band 13 only, enabled CFUN 1 and allowed 15 seconds of searching.
CSQ returned 19/99. `AT+COPS=?` completed and listed only forbidden Verizon
PLMN 311480 (AcT 7), not test PLMN 99970. CSQ therefore cannot be attributed to
the local eNodeB. CEREG cycled searching/unknown/not registered; no test attach
was observed. This demonstrates reception of an external cellular network,
not that all expected bands or the local waveform are usable.

Restored the original full standard LTE-M band list and confirmed CFUN 0. Sent
SIGINT to the eNodeB and EPC; neither remained running and OAI printed Bye.
The shell subsequently reported a segmentation fault during OAI shutdown;
this cleanup defect needs investigation and must not be described as a clean exit.
Private detailed logs remain on the Pi in `~/work/ember-lte/logs`.

The user subsequently confirmed antennas on all LibreSDR connectors.
Next checks: independently
observe the 751 MHz output, verify MIB/SIB1-BR/SI-BR decoding and advertised
PLMN, then retry Walter. Do not infer a SIM/HSS problem before cell acquisition.
Vendor command source: https://raw.githubusercontent.com/QuickSpot/walter-arduino/main/src/WalterModem.cpp

## Broadcast scheduler diagnostic

A final bounded hardware/EPC run used the lower-TX runtime config with MAC debug
logging and Walter radio off. Logs show repeated `SIB1_BR->DLSCH` scheduling
(27-byte RRC payload) and SI-BR scheduling (61-byte payload). No L1-not-ready
messages or assertions appeared during inspection. This establishes that the
LTE-M broadcast scheduling path executes; it does not independently measure
radiated I/Q, decode the broadcast, or establish Walter interoperability.
Debug logs are private and were not copied to Git.

Final scheduler diagnostic exited via timeout (124), printed Bye, and left no
eNodeB/EPC processes running. The earlier low-TX shutdown segmentation fault
was not reproduced in this short diagnostic. Antennas were confirmed on all
LibreSDR connectors; six-inch separation is user-reported, not a calibrated
RF path. Walter remained CFUN 0 with its original band list restored.
