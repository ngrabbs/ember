# Walter RAR context release and rejected-UE lifecycle

Bench observations on 2026-10-02 UTC, with Thingy powered down. Walter/M75q,
LibreSDR/Pi, antennas, and approximate six-inch separation remained as before.
OAI base is `29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`; srsEPC and the private
SIM database are unchanged. No modem firmware was flashed.

## Pool ownership and candidate

The diagnostic `dlsch-trace-20261002` run reproduced the downlink allocation
assertion at 10:20:49.625. Its eight slots held one system-information context
and seven CE-A random-access-response contexts, all with HARQ mask 1.
The corresponding allocation records identify the response owners. The trace
logging was removed before saving the candidate; raw logs remain private.

The RAR release candidate tags a HARQ process only when MPDCCH explicitly
specifies RA-RNTI, CE-A, and a single PDSCH transmission. After PDSCH scrambling
and modulation, it clears that process's mask bit, consumes the tag, and marks
the process idle. Pending PDSCH resources are retained until mapping completes.
It leaves UE HARQ feedback and the eight-context pool size unchanged. Ordinary
LTE DCI clears the tag. The candidate does not release repeated or CE-B RARs.

In `rar-release-20261002`, 19 BR responses were handled without either pool
assertion. Walter completed RRC setup, SIM authentication at 10:32:30.256,
and NAS Security Mode Complete at 10:32:30.336. OAI generated RRC Security Mode
Command at 10:32:30.541 and UECapabilityEnquiry at 10:32:30.736. Walter then
requested reestablishment with Other Failure at 10:32:31.811. OAI rejected
unknown UE contexts and aborted at 10:32:31.868 because the uplink scheduler
required a dedicated PHY configuration that a rejected context did not have.
Capability enquiry was generated after the RRC Security Mode Command, but no
capability response, completed attach, or usable data bearer was established.

## Rejection lifecycle candidate

OAI already sets a release timer for a reestablishment rejection. Its Msg4 ACK
path nevertheless marks the temporary UE configured. The second candidate
keeps a BL/CE context unconfigured when that rejection timer is active, cancels
its completed RA procedure, and lets the existing timer release it. It does
not fabricate dedicated configuration or enable reestablishment support.

The first run with both new candidates, `reject-lifecycle-20261002`, handled
30 responses and released all 30 temporary BR contexts through the existing
Msg3 failure path. It reached its bounded shutdown with exit 124, with no pool
assertion, but decoded no CCCH. Therefore it did not exercise the rejection guard.

Both runs used TX attenuation 40, legacy PRACH threshold 1000 and CE0 threshold
300. These detector settings are diagnostic, not validated deployment defaults.
The subsequent `reject-tx30-20261002` profile changes only TX attenuation to 30.
UHD gains are uncalibrated; no RF power or link-budget claim is made.

The TX30 trial handled 27 responses, three Msg4 retries, and one exhausted
Msg4 attempt without aborting. The exhausted attempt was released, and a later
attempt completed RRC setup. SIM authentication was accepted at 10:38:12.282;
NAS Security Mode Complete followed at 10:38:12.362. OAI received
ueCapabilityInformation at 10:38:12.822, EPC received Attach Complete at
10:38:12.963, and OAI received RRC Reconfiguration Complete at 10:38:13.025.
EPC recorded Initial Context Setup Response and Modify Bearer Request at that
same time. Walter reported `+CEREG: 2,1` at 10:38:14.479 and remained registered
through the last poll at 10:38:33.877. EPC assigned IP 172.16.0.2.
Both processes reached bounded timeout with exit 124. This establishes a
completed attach in this trial, but the rejection guard was not exercised.

Walter's bands were restored and CFUN 0 confirmed at 10:38:46.884. It was also
restored after the trace, RAR, and first rejection trials; raw modem logs retain
those confirmations.

## First UDP attempt and asynchronous CCCH candidate

`udp-first-20261002` completed attach again. Walter confirmed IP 172.16.0.2
and active PDP context 1. However, OAI aborted at 10:43:21.991 on
`ra->msg4_rrc_sdu_length > 0`, during another reestablishment request. No UDP
datagram reached the ground receiver. The modem accepted one send command;
the next was rejected. A modem send acknowledgment alone is not delivery.

`oai-lte-m-ccch-wait.patch` handles an unavailable first CCCH response by
waiting for another valid MPDCCH opportunity. It allows ten opportunities,
then releases the temporary UE and cancels RA. It preserves the stored Msg4
payload for retries and avoids scheduling an empty payload. This is a bounded
asynchronous-response candidate, not evidence that reestablishment works.
It is applied after the other four patches and the radio target was rebuilt.
The next run, `udp-ccch-20261002`, uses the same RF profile and ten numbered
128-byte payloads; its delivery evidence is recorded separately.

## Verification limits

- Radio targets built and source whitespace checks completed.
- The standalone release CTest calls the production helper: consume one-shot
  flag, clear the selected bit, preserve another active HARQ bit, and retain
  UE HARQ when release is disabled. It completed with no failures.
- The five patches apply sequentially to the pinned OAI source. The rejection
  guard has no standalone unit coverage; live-path evidence is tracked separately.
- `ENABLE_PHYSIM_TESTS=ON` registered the LTE downlink simulator test. The
  standard 1,500-frame case hit the 180-second limit on the Pi.
- A reduced 50-frame check returned exit 255 and zero throughput. A 10-frame
  check at SNR 20 also returned exit 255 and zero throughput. Restoring the
  pinned PDSCH routine, while retaining other candidate files and the descriptor
  layout, produced the same high-SNR result. This isolates the new release
  hook from that failure, but is not a full clean-source baseline comparison.
  PHY regression remains unresolved; no passing physim or release qualification
  is claimed. The candidate was restored and rebuilt before subsequent RF runs.

Private logs are in Pi `~/work/ember-lte/logs/`: `dlsch-trace`, `rar-release`,
`reject-lifecycle`, and `reject-tx30` run prefixes ending `-20261002`; build
and simulator logs use `build-rar-*`, `build-dlsim-*`, `test-rar-dlsim*`, and
`test-dlsim-pinned-pdsch.log`. M75q retains matching modem logs. No raw subscriber
records, authentication keys, or unredacted modem identities are included here.

Next investigation: demonstrate UDP delivery, make initial Msg3 and completed
attach repeatable, reproduce reestablishment with timestamped downlink and
feedback evidence, and resolve the PHY simulator baseline.

## Final UDP and gain observations

| Run | RX gain | BR responses | Msg4 retries | Exhausted attempts | CCCH response timeouts | Attach | UDP accepted / received | OAI exit |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| udp-first | 35 | 18 | 3 | 0 | 0 | Complete | 1 / 0 | -6 (CCCH assertion) |
| udp-ccch | 35 | 57 | 3 | 1 | 10 | Complete | 1 / 0 | 124 |
| udp-rx15 | 15 | 24 | 12 | 4 | 0 | Not complete | 0 / 0 | 124 |

The first row predates the asynchronous CCCH candidate. The remaining rows
use all five candidates. The same TX attenuation 30 and detector thresholds
1000/300 were retained. RX15 changes only RX attenuation to 50, reducing the
logged UHD gain from 35 to 15. It did not record Msg4 ACK or registration.
The gain-35 sender aborts early on a modem error; the gain-15 sender waits its
full registration deadline. Response totals are therefore not directly comparable
measurements of false-detection rate.

In `udp-ccch`, Attach Complete was received at 10:46:21.051. Walter reported
registered at 10:46:21.812, IP 172.16.0.2 at 10:46:22.013, and active PDP
context 1. CSQ returned 24,99 (raw modem metric, not calibrated path loss).
Socket setup completed. The modem accepted sequence 0, then rejected sequence 1
with `+CME ERROR: operation not supported`. The receiver observed no matching
packet during its full 150-second window. The trial requested ten packets;
only one send was modem-accepted. Do not report this as a ten-packet loss test.
Repeated Other Failure reestablishment requests were observed before socket
transmission; socket-state errors and radio instability still need isolation.

The cell stayed alive to its 140-second deadline with the CCCH wait candidate.
Ten pending-response timeouts used the release path without the old assertion.
The rejection-ACK guard was not exercised, and successful reestablishment is
not demonstrated. Neither UDP trial establishes end-to-end telemetry delivery.

The receiver's production script was tested locally with invalid JSON, a
duplicate sequence, and out-of-order arrivals; it reported the expected counts.
Python syntax checks completed. This validates bookkeeping, not the RF link.
The UDP command sequence is derived from the pinned
[vendor socket implementation](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/src/proto/WalterSocket.cpp).
Numbered bench packets were generated by the M75q and submitted over serial to
Walter's modem; the M75q did not send those packets over its own network stack.
UTC send timestamps are host timestamps, not synchronized spacecraft clocks.

All bounded radio/core/receiver sessions stopped. Walter's full standard band
list was restored and CFUN 0 confirmed after the last trial at 10:51:28.196.
The latest OAI/EPC timeout exits were recorded at 10:51:39.688/10:51:44.673.
Thingy remains deferred. The next RF comparison should use greater antenna
separation or an attenuated coax setup and the gain-35 profile, followed by
repeat attach and numbered UDP delivery. A complete clean-source PHY simulator
comparison remains a separate validation requirement.

Final saved patch sequence was compared byte-for-byte with all 13 changed OAI
files on the Pi. Rebuilt `build-lte/lte-softmodem` SHA-256:
`f1169eb1130b117fbbfe41a48297ff6c28cdec45b071b3eff93d87a518328145`.
The source branch remains `ember/lte-m-msg3-cleanup`; all candidates are local
changes preserved in EMBER patches, not OAI upstream commits.
