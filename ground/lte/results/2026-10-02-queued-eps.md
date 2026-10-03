# First queued hardware EPS delivery

Three real EPS POWER_STATUS packets were captured on IHU, retained while Walter
was OFF, then delivered in FIFO order through CAN → COMMS → Walter → LTE-M/
LibreSDR → OAI/srsEPC → native receiver → Yamcs `ember-lte`. Every packet matches
all128 bytes at enqueue, modem acceptance, receiver and Yamcs archive.
[Packet/status/archive evidence](../../../system/ground_station/evidence/queued-eps-20261003-01/report.json).

This run occurred October2, 2026 in America/Chicago. UTC label
`queued-eps-20261003-01`, network window01:39:57–01:43:02 on October3.
Receipts were01:40:52.057,01:40:53.297 and01:40:54.537 UTC, sequences0–2,
IHU boot2376047495. All have hardware provenance2, ADC-valid1 and
conversion-valid1. Battery-only EPS ADC was explicitly verified on before
capture. Current conversions retain unverified10mΩ sense-resistor assumptions.
Queued packets preserve capture uptime and original readout; they are not
resampled or rewritten at transmit time.

## Procedure and results

The final IHU queue and Walter admission candidates were installed and verified.
[Policy, hashes and deployment](2026-10-02-queue-preparation.md).
COMMS stayed on its previous image, boot1875991883. The OAI eight-candidate
binary/profile stayed unchanged from the9/10 reliability series, SHA-256
`5c5de8e17db509b35823f401b99c7fdbe28144307da0be24fbc777c569768e11`,
profile `enb.band13.emtc.ce300tx20diag.conf`.

After IHU reboot, CAN was explicitly restored from configuration to normal mode.
The first Walter status query encountered the new Walter boot identity after
flashing; its stale peer rejection is preserved in the final guard evidence.
Refreshing CAN HELLO/status restored the relay with Walter OFF. The active-CAN
EPS enqueue guard also passed: a simultaneous `lte status` and `eps enqueue`
returned BUSY for enqueue and left the queue empty.
[Final-image guard evidence](../../../system/ground_station/evidence/lte-queue-preparation-20261003/final-guard.json).

`eps_queue_trial.py` checked an empty FIFO, collected three real EPS packets,
enabled queue service for8 seconds with RF OFF, then disabled it. The FIFO
retained all three: attempts0, accepted0, hold0. The host explicitly opened one
120-second RF window and enabled queue service; no autonomous RF start occurred.

The queue waited for readiness and then drained all three packets. Each send
had one attempt; retries0, holds0, FIFO count0, accepted3. Ground receiver
reported3 received, rejects0, duplicates0. Exact FIFO order and each packet's
Yamcs archive match were verified independently. There was no ground-side
injection of synthetic EPS data.

The host disabled queue service, waited for idle and explicitly stopped RF.
Walter OFF/window0 was confirmed; queue enabled0/count0/state0/hold0. IHU
CAN TEC/REC, TX failure/timeout, RX bad/overflow, fragment error/timeout and busy
counters remained zero. UNKNOWN stayed1 throughout the trial; this was the
pre-trial stale-Walter-peer rejection, not a new delivery failure.

Host, receiver and radio wrapper exited0. The eNodeB/EPC children ended at their
bounded deadlines with exit124; capture exited124. Final log metadata found
zero assertion, maximum-retransmission or reestablishment-request lines, and
no network processes remained running.
[Radio metadata](../../../system/ground_station/evidence/queued-eps-20261003-01/radio-metadata.json).

## Scope and reproduction

This proves radio-off retention followed by three queued deliveries in one
explicit RF window. It does not exercise a forced mid-window registration loss,
backoff after actual NOT_READY/BUSY, or ambiguous-send hold on hardware. Those
paths have mock/native policy tests and remain hardware qualification work.
Retirement still means modem acceptance, not an application ACK from ground.
The volatile queue is in the IHU bench harness; operational queue ownership
remains COMMS. Continuous telemetry and reset recovery remain open.

Run the existing bounded ground radio helper with `--seconds 180`, the native
receiver with `--count 3 --seconds 200`, and an185-second bounded packet capture.
After cell steady state, on M75q run `eps_queue_trial.py --count 3 --seconds 120
--port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 --output
PRIVATE_DIRECTORY` from the staged host-tests directory. Compare each saved
queued packet with the receiver and Yamcs archive, and check child process exits
separately from the wrapper. Raw radio logs/pcaps remain private on the Pi.
