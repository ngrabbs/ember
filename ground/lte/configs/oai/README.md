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
