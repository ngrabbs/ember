# OAI LTE-M candidate

Experimental configuration: syntax validation does not establish successful
startup, RF behavior, or Walter attach. Do not launch without reviewing RF setup.

Derived from `targets/PROJECTS/GENERIC-LTE-EPC/CONF/enb.band13.tm1.50PRB.emtc.conf` at OAI
commit `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`. Original SHA-256: `1a099382b2dc98af5da3ff092f84ae4913daf02d278f2bb736ed8c3922f0a4f1`.
The separate CI untested example is malformed (missing assignment at line 359
and an incomplete tail); this complete older example is the starting point.

Changes: PLMN 999/70, TAC 7, Pi-local eNB S1 address 127.0.1.1/8,
MME 127.0.1.100, explicit custom FPGA in RU sdr_addrs, and RU transmit
attenuation 60 and receive attenuation 30. This attenuation is a starting configuration, not measured EIRP.
Band 13 at the upstream frequency is retained as a candidate supported by
Walter's standard LTE-M band list. These settings were exercised in a bounded hardware run with S1 setup; Walter
registration is still unverified. Use single-thread/worker-disabled flags from
the runbook to avoid the observed default-threading timing errors.

The initial topology runs eNodeB and srsEPC on the Pi. The EPC uses the
recovered loopback addresses (127.0.1.100 for MME/GTP, 172.16.0.1 for SGi);
the eNB uses a distinct loopback address so GTP port 2152 does not conflict.
Use the preserved epc.conf from configs/srsran-4g in the same runtime config
directory as a private user_db.csv. See [build record](BUILD.md).

At six-inch antenna separation, a diagnostic copy with `att_tx=80` yielded
UHD TX gain 9.75 dB; Walter's band-13 scan still did not list the test PLMN.
The tracked starting candidate retains `att_tx=60` for comparison. A MAC-debug
run confirms repeated SIB1-BR/SI-BR scheduler activity, not a decoded RF signal.

`enb.band13.emtc.tx30.conf.example` preserves the subsequent diagnostic profile
with attenuation 30 (logged UHD TX gain 59.75). Independent HackRF PSS/SSS
detection and controlled Walter OFF/ON access were observed with this profile.
It remains experimental: OAI aborts on CE Msg4 retransmission and Walter has
not registered. For MAC-only debug, change `mac_log_level` to `"debug"`; leave
PHY logging at info. See [controlled results](../../results/2026-10-02-walter-control.md)
and [experimental cleanup patch](../../patches/README.md).

The `ceonlydiag` and `ce300diag` profiles use attenuation 40, MAC-debug logging,
and ordinary-LTE PRACH threshold 1000. `ce300diag` also increases CE0 threshold
from 200 to 300. These are controlled diagnostics to investigate false detection
and context pressure. They reached Msg4/RRC and accepted SIM authentication,
but OAI still aborted on downlink allocation before completed attach. See
[latest results](../../results/2026-10-02-msg4-authentication.md).

With the newer candidates, `ce300tx30diag` changes only `att_tx` from 40 to 30
relative to `ce300diag`. It recorded completed Walter attach and registration.
`ce300tx30rx15diag` changes only `att_rx` from 30 to 50 relative to that profile,
reducing logged UHD RX gain from 35 to 15. This checks gain sensitivity at the
six-inch bench separation. Neither profile establishes calibrated RF power.
Use all five patches in order and keep the profile explicit in every result.
See [RAR/lifecycle results](../../results/2026-10-02-rar-release.md). A completed
attach alone does not prove telemetry delivery or stability.

At the reported six-to-eight-foot antenna separation, `ce300tx30diag` decoded
connection requests but did not complete RRC setup in one trial. The follow-up
`ce300tx20diag` changes only TX attenuation from 30 to 20 (logged gain 69.75;
RX remains 35). It completed attach and bearer setup, but UDP delivery still
failed after uplink-failure reporting. This is an experimental comparison,
not a calibrated-power setting or demonstrated stable telemetry profile.
See [separated-antenna results](../../results/2026-10-02-separated-antennas.md).

With all six candidates, the same `ce300tx20diag` profile delivered ten numbered
UDP payloads after a Service Request restored the bearer. It remains a bench
profile with unresolved context release and uplink failure. See
[first telemetry results](../../results/2026-10-02-uplink-telemetry.md).

`ce300tx20rrcdiag` changes only RLC and RRC logging from info to debug, allowing
SRB maximum-retransmission and RRC release events to be correlated. The latest
seven-patch trial still experienced those failures. See
[release trace](../../results/2026-10-02-repeatability-release.md). Debug logging
adds overhead and this profile is for diagnosis.
