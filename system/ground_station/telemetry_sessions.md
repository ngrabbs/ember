# Record and replay an EMBER housekeeping session

The Pi's existing Yamcs archive provides packet recording. The new
`ground/ember/session.py` exports a bounded session containing raw HEARTBEAT
and POWER_STATUS packets, original archive timestamps/link names, link-counter
snapshots, operator-declared source context, and the decoder dictionary hash.
It validates packet length, CRC, identity, name, and archive time bounds.

Run from the EMBER repository on the laptop with Python 3; no extra packages
are required. The Pi must be reachable on the bench LAN:

```sh
python3 ground/ember/session.py record \
  ground/yamcs/.runtime/sessions/housekeeping-new.json \
  --url http://192.168.1.251:8090 --seconds 30 \
  --origin 'Pi USB Pico bench heartbeat; IHU UART Pi EPS wrapper'
python3 ground/ember/session.py summary \
  ground/yamcs/.runtime/sessions/housekeeping-new.json
python3 ground/ember/session.py replay \
  ground/yamcs/.runtime/sessions/housekeeping-new.json --speed 10
```

Choose a new filename for each recording; existing sessions are never
overwritten. Record windows are limited to 1–300 seconds. The laptop UTC clock
defines the archive generation-time window, so verify clocks if the selected
window unexpectedly contains no packets. Two seconds are allowed for archive
writing before export; unusually delayed archive writes may need a later export
workflow. An empty recording fails. A successful export is a bounded snapshot,
not a long-term archive backup or guaranteed capture of all in-flight data.

Replay decodes the entire file before displaying any packet. `--speed 0`
(default) emits immediately; 1 preserves recorded receive-time spacing and
10 runs ten times faster. Output is JSON lines marked `OFFLINE_REPLAY`, carrying
the original receive time and decoded header/payload. Replay requires neither
Yamcs nor hardware and has no network transmission or command-dispatch path.
It does not populate a Yamcs replay processor or modify live parameter values.

Raw exported sessions and replay outputs stay under ignored `.runtime/sessions`;
files include operational metadata and are created with private permissions.
Retain that directory separately when cleaning the checkout. The dictionary
hash prevents silently decoding a session against changed packet definitions;
keep the matching dictionary/codec revision with a session for future use.
Source labels are declared context, not authenticated spacecraft identity.

The source/link/boot ID distinguishes streams. Sequence numbers are shared
between message types within an endpoint, so gaps in this two-message export
must not be interpreted as lost packets. Yamcs assigns these bench packets
ground-local generation time; neither generation/reception differences nor
replay spacing establishes spacecraft latency or synchronized spacecraft time.

The [live overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime)
remains the native display. POWER_STATUS quality flags govern whether EPS
engineering values can be used. A bridge that emits packets while UART polls
time out is not evidence of fresh EPS measurements. Preserve unavailable
sentinels and quality flags in replay rather than substituting cached voltages.

## Demonstration — 2026-10-02

A 30-second window from 12:53:11.318 to 12:53:41.324 UTC exported 60 packets:

- 30 live Pico HEARTBEAT packets over the existing USB bridge, source boot ID
  3087467115, receive span 29.002 seconds. Sequence 2178–2265 spans other packet
  types that were intentionally excluded from this export.
- 30 Pi-generated EPS UART wrapper packets, session 2301702123, receive span
  29.042 seconds. All had invalid/stale readouts and unavailable conversions.
  The latest UART readout was already about 12 hours old at inspection;
  current EPS voltages were not demonstrated in this run.

Pagination was exercised with page size 10. Replay at 10x produced all 60
decoded packets with matching recorded receive times and explicit replay tags.
All 30 ground tests passed, including seven new session tests for pagination,
repeated tokens, corruption before playback, timing, quality preservation,
metadata/dictionary/time mismatches, and refusing command packets.

[Evidence summary](evidence/telemetry-session-20261002.json) records counts and
dictionary/session hashes. The local raw session is
`ground/yamcs/.runtime/sessions/housekeeping-20261002.json`; decoded replay is
`housekeeping-20261002-replay.jsonl` alongside it. Existing bridge services and
Yamcs were left running; no firmware, charger configuration, or RF operation
was changed. The Pico heartbeat and portable recording/replay are working.

After the user restored bench power, a second 30-second session from
12:56:13.040 to 12:56:43.046 UTC captured 30 heartbeats and 30 EPS packets.
All 30 EPS packets had current UART readouts; the bridge recovered without a
service restart. ADC-valid remained zero, so every engineering conversion
remained unavailable. A zero detected cell count uses the configured two-cell
fallback in this decoder; it is not alone the reason for invalid conversions.
No charger or ADC setting was changed. The user confirmed VIN/solar is off
and the EPS is running on battery only. CONFIG_BITS is zero, so forced
telemetry is off; this matches the normal read-only firmware's
[previously recorded battery-only state](eps_bench_setup.md#normal-firmware-restored).
Analog Devices describes battery-only ADC operation as requiring forced
telemetry; see its
[LTC4162-L explanation](https://ez.analog.com/power/f/q-a/537074/ltc4162-l-reading-vbat-as-0).
Live engineering measurements need input-powered observation or a separate,
narrow ADC-control change. That change was not part of session recording.

The second session and replay are saved alongside the first as
`housekeeping-powered-20261002.json` and
`housekeeping-powered-20261002-replay.jsonl`. Its
[powered-session evidence](evidence/telemetry-session-powered-20261002.json)
records fresh-readout quality and ADC state. Both sessions retain the original
quality flags, making the stale-to-current UART transition reproducible offline.

Export uses the documented
[Yamcs List Packets API](https://docs.yamcs.org/yamcs-http-api/packets/list-packets/),
including continuation tokens and inclusive/exclusive generation-time bounds.
