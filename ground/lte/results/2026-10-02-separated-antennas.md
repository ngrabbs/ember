# Walter antenna-separation comparison

On 2026-10-02 the user moved Walter and its LTE antenna from approximately
six inches to approximately six to eight feet from the LibreSDR antennas.
The setup remains over the air, with no splitter, coax path, or calibrated
attenuation. Thingy work remains deferred.

The first trial kept the prior gain-35 profile and all five OAI patches.
OAI binary SHA-256 remained
`f1169eb1130b117fbbfe41a48297ff6c28cdec45b071b3eff93d87a518328145`.
No source, firmware, SIM credentials, or modem command sequence changed.
This is a comparison of reported positions, not a calibrated RF link budget;
precise antenna orientation and room multipath were not measured.

## Same-gain trial

Run ID: `udp-separated-20261002`. Profile:
`enb.band13.emtc.ce300tx30diag.conf` (TX attenuation 30, RX attenuation 30,
legacy/CE0 PRACH thresholds 1000/300). UHD reported TX gain 59.75 and RX gain
35. OAI steady-state operation was reported at 11:16:59.228 UTC before the
Walter test helper started. Radio deadline was 140 seconds, modem enable
window 100 seconds, UDP receiver window 150 seconds.

| Observation | Count/result |
| --- | ---: |
| BR random-access responses | 62 |
| Response identifiers observed released | 62 |
| Decoded UL CCCH | 13 |
| Msg4 retries | 33 |
| Exhausted Msg4 attempts | 6 |
| Msg4 ACK indications | 7 |
| RRC Setup Complete | 0 |
| Downlink/ULSCH pool assertions | 0 |
| CCCH response timeouts | 0 |
| OAI/EPC exits | 124 / 124 |
| Modem-accepted UDP sends | 0 |
| Received UDP datagrams | 0 |

Some initial Msg3 attempts failed, while later attempts decoded valid connection
requests and generated RRCConnectionSetup. Msg4 ACK indications alone did not
establish completed RRC setup: Walter remained in searching state (`CEREG 2,2`)
and no Attach Complete was received. Therefore the sender never opened its UDP
socket or submitted a packet. The receiver's missing sequence list describes
unreceived requested packets, not loss of ten transmitted packets.

The MAC log records valid Msg3 CRCs and later dedicated uplink CRC errors. This
narrows the observed failure to signaling after initial random access; it does
not distinguish an unheard grant, incorrect scheduling, or PHY decoding failure.

OAI/EPC stopped at 11:19:14.692/11:19:19.674. Walter's full standard band list
was restored and CFUN 0 confirmed at 11:19:22.523.

## Controlled TX-gain follow-up

The next profile, `enb.band13.emtc.ce300tx20diag.conf`, changes only TX attenuation
from 30 to 20. RX gain and the separated antenna positions stay as above.
UHD reported TX gain 69.75 and RX gain 35; actual output power remains unmeasured.
Run ID: `udp-separated-tx20-20261002`. The radio/modem/receiver windows are
120/75/130 seconds. Counts from unequal windows must not be compared as rates.
This is a diagnostic check of downlink-margin sensitivity, not a new default.

This run handled 25 BR responses and decoded one connection request. Msg4 was
retried twice and acknowledged. RRC Setup Complete, accepted SIM authentication,
NAS Security Mode Complete, UE capability response, Attach Complete, RRC
Reconfiguration Complete, and Initial Context Setup Response were recorded.
EPC assigned 172.16.0.2; Walter confirmed registration and its active PDP context.
There were no pool assertions, Msg4 exhaustion, or CCCH response timeouts.

Key events, UTC:

- 11:20:54.053: OAI received RRC Reconfiguration Complete.
- 11:20:54.054: EPC received Initial Context Setup Response and Attach Complete.
- 11:20:55.071: MAC reported UL Failure timer 1.
- 11:20:55.934: Walter reported registered (`CEREG 2,1`).
- 11:20:56.134: Walter confirmed IP 172.16.0.2.
- 11:20:57.337: modem accepted UDP sequence 0.
- 11:20:58.539: sequence 1 was rejected with operation not supported.

The ground receiver observed no matching UDP packet during its 130-second
window. Only one packet was modem-accepted; the requested ten-packet transfer
was not completed. CSQ returned 99,99, so no useful signal-strength measurement
was obtained in this run. Uplink-failure reporting preceded the first socket
send; successful control-plane establishment did not produce a demonstrated
user-plane path. It remains possible that a separate socket-state issue also
exists; no socket-state query was captured at the error.

OAI/EPC reached timeout with exit 124 at 11:22:17.760/11:22:22.739. Walter's
full standard bands were restored and CFUN 0 confirmed at 11:21:11.743.
All radio/core/receiver sessions stopped.

The higher-TX run reached attach while the same-gain separated run did not.
One trial at each setting does not establish a reliable gain threshold or prove
that antenna separation caused the difference. Preserve both profiles as
explicit diagnostics. The next test should capture dedicated uplink grants,
HARQ/CRC outcomes, modem socket status, and GTP/SGi packet evidence around the
first send. Avoid treating a gain change or a modem send OK as a solved data link.

## Evidence and remaining work

Private logs remain on Pi `~/work/ember-lte/logs/udp-separated*-20261002-*`
and M75q with corresponding `-walter.log` suffixes. Full subscriber identifiers
and raw logs are not copied into Git. The receiver and sender helpers remain
unchanged for this comparison.

A completed attach was recorded in earlier six-inch trials, but the data path
has not been demonstrated. Reproduce RRC setup completion at this position,
then capability/security exchange, bearer setup, and numbered UDP delivery.
The earlier PHY simulator regression remains unresolved; this comparison does
not qualify the source patches for deployment or flight.
