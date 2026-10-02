# LTE-M spacecraft telemetry bench

Walter is the proposed spacecraft UE; an SDR eNodeB and EPC operate on the ground.
The first milestone is a repeatable bench LTE-M attach and IP telemetry transfer.
An orbital link is a later experiment, with its own timing, Doppler, power, and RF validation.

- [Bring-up runbook](BRINGUP.md)
- [Bench and spacecraft TODO](TODO.md)
- [Observed equipment and software](INVENTORY.md)
- [Ground-radio test results](results/2026-10-01-ground-radio.md)
- [Independent HackRF/LTE-M access results](results/2026-10-01-hackrf-lte.md)
- [Controlled Walter OFF/ON and Msg3 cleanup results](results/2026-10-02-walter-control.md)
- [Msg4 retry and accepted SIM authentication](results/2026-10-02-msg4-authentication.md)
- [RAR release and first completed Walter attach](results/2026-10-02-rar-release.md)
- [Six-to-eight-foot separation comparison](results/2026-10-02-separated-antennas.md)
- [First end-to-end Walter UDP telemetry](results/2026-10-02-uplink-telemetry.md)
- [Experimental OAI patches](patches/README.md)
- [OAI candidate config and build record](configs/oai/README.md)
- [Recovered ordinary LTE configs](configs/srsran-4g/)
- [Walter firmware location](../../firmware/walter/README.md)

## Current status

Hardware access, custom-FPGA UHD initialization, receive streaming, and Walter
AT communication are verified. Walter completed LTE-M attach on 2026-10-02,
with modem registration and EPC bearer setup recorded. A subsequent trial
delivered ten numbered 128-byte UDP packets through GTP-U and SGi to the ground
receiver. Repeatability and radio stability remain under test. The recovered srsRAN 4G configuration is an ordinary LTE baseline from
an earlier SIM7600 setup; it cannot by itself connect Walter's Cat-M1 radio.
OAI and srsEPC are now built on the Pi, hardware S1 setup succeeds, and bounded
OTA attempts are documented. HackRF independently detects expected-cell LTE synchronization. During Walter
attempts, OAI exercised LTE-M random access and RRC setup generation, then hit
scheduler/resource assertions. Initial trials did not complete registration; newer trials reached Attach Complete
and RRC Reconfiguration Complete. The first UDP burst was received in order
without missing sequences or duplicates within its observation window.

The 2026-10-02 OFF/ON comparison with Thingy powered down strongly attributes
the decoded CE0 connection request to Walter. Experimental OAI patches now
release abandoned Msg3 contexts and retry Msg4. Live tests reached Msg4 ACK,
RRC Setup Complete, accepted SIM authentication, and NAS Security Mode Complete.
The new RAR release candidate removed the observed pool assertion in bounded
trials; subsequent trials completed attach and assigned 172.16.0.2. Reestablishment
lifecycle failures and PHY simulator regression remain unresolved.
Thingy interface work is deferred.

OAI is the first open-source LTE-M candidate to evaluate. Its historical eMTC
work demonstrated commercial modems, including Sequans, but had single-UE,
scheduler, and repetition limitations. Current support must be reproduced before
calling it usable. Amarisoft is a commercial alternative; SDR compatibility and
licensing remain unverified.

## Repository boundaries

Keep small configs, scripts, procedures, and sanitized evidence here. Keep full
srsRAN/OAI source and builds outside the repository. Store private subscriber
records, raw logs, and packet captures in ignored directories. Review logs for
identifiers and authentication material before publishing excerpts. Keep the
custom LibreSDR FPGA image externally until its provenance and redistribution
terms are established; its source path and checksum are in the inventory.

## References checked 2026-10-01

- [srsRAN LTE-M support discussion](https://github.com/srsran/srsRAN_4G/issues/747)
- [OAI eMTC implementation and limitations, slides 23–26](https://www.openairinterface.org/docs/workshop/1stOAINorthAmericaWorkshop/Training/KALTENBERGER-OAI_basics_June_2019.pdf)
- [Current OAI untested eMTC example](https://github.com/OPENAIRINTERFACE/openairinterface5g/blob/develop/ci-scripts/conf_files/untested/enb.band13.tm1.50PRB.emtc.conf)
- [Amarisoft radio capabilities](https://www2.amarisoft.com/technology)
- [Walter documentation](https://github.com/QuickSpot/walter-documentation)
- [LTE-M satellite adaptations research](https://arxiv.org/abs/2103.14169)
