# Controlled LTE cell outage and queued EPS recovery

The bench retained three real EPS packets during an actual LTE registration loss,
then delivered those original packets in FIFO order after the cell returned and
the controller explicitly opened a fresh bounded modem window. All128 bytes of
each packet match enqueue, modem acceptance, UDP reception and Yamcs archive.
[Complete packet, status and archive evidence](../../../system/ground_station/evidence/outage-eps-20261003-01/report.json).

This was October2, 2026 in America/Chicago; UTC label
`outage-eps-20261003-01`, October3 01:51:13–01:56:09. Firmware and radio profile
were unchanged from the preceding queued-delivery proof. OAI binary SHA-256
`5c5de8e17db509b35823f401b99c7fdbe28144307da0be24fbc777c569768e11`,
profile `enb.band13.emtc.ce300tx20diag.conf`. IHU boot2376047495,
COMMS boot1875991883; Walter admission and IHU FIFO candidates remain installed.

## Fault and observation

1. Start a bounded cell/EPC and establish registered READY. Send real EPS
   sequence3 and independently confirm its exact bytes in UDP and Yamcs.
2. Resolve only this labelled helper's eNodeB/EPC process IDs, verify their
   command lines, and send SIGINT. Both children exited0 deliberately; no
   process crash was used to create the outage. Mark the physical cell absent
   only after both children finished.
3. Observe Walter without issuing direct modem AT commands. Cached diagnostics
   changed from READY6/registered1/CEREG1/losses0 to **READY6/registered0/CEREG0/
   losses1**, with54.4 seconds still remaining in the RF window. READY alone was
   therefore a stale indication of usability. No forced-OFF fallback was needed
   to observe loss; the modem was still in its original RF window.
4. Capture three fresh hardware EPS readouts as sequences4–6. Enable the queue
   for8 seconds while the cell is absent, then disable it. Count3, attempts0,
   hold0, no change in queue acceptance count. The status-based admission policy
   retained all packets rather than issuing a send against stale READY. Ground
   had only the baseline packet before restoration.
5. Explicitly stop Walter, verify OFF, restore a fresh bounded cell/EPC, and
   explicitly open a new120-second modem window. Enable FIFO service; all three
   original packets drain in order, with one attempt each and no retry/hold.

Controller event times were baseline acceptance50.726 seconds, confirmed cell
removal51.978, retention checkpoint96.253, restored-cell checkpoint102.259 and
recovery completion133.946, relative to host-test start. The baseline command
wait collects replies for22 seconds, so its event is later than actual packet
reception; these event intervals are not modem/network latency measurements.
The recovery checkpoint was31.687 seconds after the restored-cell checkpoint,
including explicit modem boot/configuration/registration/socket setup and sends.

Baseline UDP reception:01:51:46.110 UTC. Recovered sequence4–6 receptions:
01:53:22.263,01:53:23.303 and01:53:24.563. Receiver reported4/4 total, rejects0,
duplicates0. All four independently match the Yamcs `ember-lte` POWER_STATUS
archive. Each has hardware provenance2, ADC-valid1 and conversion-valid1;
current conversions retain unverified10mΩ sense-resistor assumptions. Queued
capture uptime/packet bytes were preserved; the packets were not resampled.

## Final state and limits

Queue accepted count3→6 (the direct baseline does not count as FIFO acceptance),
count0/enabled0/state0/hold0/retries0. Walter OFF/window0 confirmed. IHU CAN
TEC/REC, TX failure/timeout, RX bad/overflow, fragment error/timeout and busy
counters stayed zero. UNKNOWN stayed1 from the earlier flash-peer refresh,
with no new UNKNOWN during this trial.

Host, receiver and both radio wrappers exited0. The deliberately stopped first
network children exited0; the restored eNodeB/EPC reached their bounded deadlines
with exit124. Capture exited124. Final network-process inspection and log searches
are in the [radio metadata](../../../system/ground_station/evidence/outage-eps-20261003-01/radio-metadata.json).
Raw radio logs/pcaps remain private on the Pi. All36 ground tests pass; the new
host workflow was exercised against actual hardware, not a synthetic EPS source.

This proves registration-aware retention and recovery under **explicit controller
RF stop/reopen**, in one deliberate outage. It does not prove reconnection within
the original modem window, autonomous RF reopening, pre-submission backoff on
hardware, or replay of uncertain sends. Ambiguous submissions remain held.
FIFO retirement is modem acceptance; ground application acknowledgments remain
unimplemented. Operational queue ownership remains COMMS; this is IHU bench
harness policy. A bounded periodic EPS burst is the next independent milestone.

The reusable host side is `ground/ember/eps_outage_trial.py --port IHU_SERIAL
--output FRESH_PRIVATE_DIRECTORY`. Its coordinator must confirm baseline UDP
and archive before removing the exact labelled cell, create `outage` only after
removal, and create `restored` only once the new cell reaches steady state. It
refuses directories containing stale coordination flags/results. Use the existing
bounded radio helpers with180 seconds per cell, receiver4 packets/300 seconds,
and295-second capture. Each modem window is120 seconds and cannot be extended.
