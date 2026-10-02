# LTE-M spacecraft telemetry bench

Walter is the proposed spacecraft UE; an SDR eNodeB and EPC operate on the ground.
The first milestone is a repeatable bench LTE-M attach and IP telemetry transfer.
An orbital link is a later experiment, with its own timing, Doppler, power, and RF validation.

- [Bring-up runbook](BRINGUP.md)
- [Bench and spacecraft TODO](TODO.md)
- [Observed equipment and software](INVENTORY.md)
- [Ground-radio test results](results/2026-10-01-ground-radio.md)
- [Independent HackRF/LTE-M access results](results/2026-10-01-hackrf-lte.md)
- [OAI candidate config and build record](configs/oai/README.md)
- [Recovered ordinary LTE configs](configs/srsran-4g/)
- [Walter firmware location](../../firmware/walter/README.md)

## Current status

Hardware access, custom-FPGA UHD initialization, receive streaming, and Walter
AT communication are verified. LTE-M attach is **not**
verified. The recovered srsRAN 4G configuration is an ordinary LTE baseline from
an earlier SIM7600 setup; it cannot by itself connect Walter's Cat-M1 radio.
OAI and srsEPC are now built on the Pi, hardware S1 setup succeeds, and bounded
OTA attempts are documented. HackRF independently detects expected-cell LTE synchronization. During Walter
attempts, OAI exercised LTE-M random access and RRC setup generation, then hit
scheduler/resource assertions. Registration and a telemetry bearer remain
unverified.

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
