# EMBER archive replay

Verified on the Pi, 2026-10-01, Yamcs 5.13.0. Replay operates on archived
packets through a separate Archive processor. The realtime processor and both
UART/USB bridges continue operating. Replay processor reports hasCommanding=false;
playing recorded telemetry does not reissue hardware commands.

## Use from the browser

1. Open Archive in the EMBER realtime context. Choose the interval containing
   the observation. This verified interval was 2026-10-01 23:10–23:14 UTC.
2. Select the range tool next to the hand tool, then drag across the timeline.
   Click **Replay range**, check start/stop and supply a unique processor name.
3. Click **Start**. The header becomes purple and the context changes to the
   replay processor. Play/pause controls and the historical processor clock
   appear in the header.
4. Open the EPS display with that context. Let at least one packet play after
   subscribing, then pause. A newly opened display before any subscribed
   packet is processed may initially have no parameter values.
5. Return to Archive in the same context. Double-click the desired timeline
   time to seek. Observed behavior: seeking resumes playback even when paused.
   Open the display and pause again when the desired sample arrives.
6. Return to the realtime display by choosing realtime context. Selecting the
   same instance alone did not change its processor in this browser; using the
   explicit realtime display URL worked. Verify purple replay header and Play
   control disappear and the processor clock is current.

[Realtime EPS display](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember__realtime&range=PT15M).
A narrow panel can use View → Zoom out four times to show the full display.

## Verification and interpretation

Created `ember-eps-review`, range 23:11:19.831–23:12:50.273 UTC, at original
speed with endAction STOP. UI play/pause worked. Forward seek from the test
window to +23:12:43 showed CONFIG 44, JEITA enabled and suspended state 256.
Backward seek to +23:11:31 replaced those values with CONFIG 12, JEITA disabled
and NTC-pause state 32. Historic timestamps and VIN/VBAT/IBAT followed the
selected processor, matching the original capture.

At pause, processor time remained exactly 23:12:43.831 across API checks;
realtime continued to 23:22:08.273. Pausing for longer than EPS packet expiry
in wall-clock time did not expire the displayed historical sample: freshness
follows replay time. This validates pause semantics, not every archive gap or
playback speed. EPS readout_age_ms remains the original UART observation age
inside the archived packet; it is not time elapsed on the laptop or ADC age.

Clarified EPS quality label as **Packet link: LIVE** and added the footer that
replay link status describes archived data. The purple header and historical
clock identify replay. Automatic processor-aware freshness for the spare Pico
overview's configurable telemetry interval remains a separate open task.

After verification the browser was returned to realtime. `ember-eps-review`
is left paused for review during this server session; it is not a substitute
for durable archive/backup. Server restart can require creating a new replay.

Evidence: [API responses](evidence/eps-replay-validation-20261001.json) and
[paused replay screenshot](evidence/ember-eps-replay-verified.png).
Source and installation changes were limited to EPS display wording; managed
objects were backed up before replacement and uploaded bytes verified.

Next: configure telemetry retention and archive backups, and prove restoration
in an isolated instance before any archive deletion policy is enabled.
