# UHF / AMSAT SDRB ground channel

[Ground software](../README.md) · [SDRB workstreams](../../system/sdrb/TODO.md)

Optional [application supervision and operation](SERVICES.md) now provides explicit
start/stop and bounded logs. A subsequent short native telemetry run passed2/2
through Yamcs. The [supervision evidence](results/2026-10-03/supervision/result.json)
also retains a TX startup underrun/timing fault: reliable restart remains open.

**Current operating profile:**614.4kS/s with automatic UHD clock selection,
matched analog bandwidth, larger local transport frames and timed TX startup.
The [clock review](CLOCKING.md) traces the deployed driver/FPGA behavior.
The [final bounded test](results/2026-10-03/clock-review/result.json) ran93.24seconds
in transponder mode with zero reported U/O or UDP errors, and6/6 fresh IHU packets
matched at CAN, socket admission, RF decoder and Yamcs. Higher rates and indefinite
operation remain unqualified. Earlier results below retain their original limits.

The [conducted-uplink check](results/2026-10-03/conducted-proof/result.json)
now demonstrates435.1→434.2MHz tone forwarding alongside three fresh IHU packets
through Yamcs. Its optional application uses forwarding scale16 and the tested250ms
timed TX priming, with explicit RX/TX error counters. The later HT test records operator-observed antenna forwarding below; the
LibreSDR tone gate and longer operation remain open. Preserve earlier results separately.

The subsequent [native headroom check](results/2026-10-03/headroom/result.json)
adds an opt-in compiled mixer. A 60.6-second conducted stress run kept forwarded
IQ at 0.25 full scale and the telemetry mix below 0.37, with zero RX/TX/UDP errors
and 3/3 fresh packets byte-matched through Yamcs. This establishes a bounded
digital amplitude check; linear SSB, analog headroom and longer operation remain open.

The intended route is IHU native telemetry → CAN1 → optional EMBER adapter on
AMSAT SDRB → UHF packet waveform → LibreSDR receiver on the ground Pi → unchanged
EMBER packet → Yamcs `ember-uhf` → EPS display. Radio reception, decoder validation,
Yamcs archive byte identity and displayed values are separate acceptance gates.
No host replay or USB/LTE reception qualifies the UHF path.

## Observed ground setup — October 3, 2026

- Ground host: `ngrabbs@192.168.1.251`, Pi 5 / Debian 13 / aarch64.
- Yamcs 5.13.0 runs in `ember-ground-starter-yamcs-1` from
  `/home/ngrabbs/work/MSU_Cubesat/ember/ground/yamcs`, HTTP port 8090.
- Existing `ember` input ports are UDP10016 (USB) and UDP10017 (EPS UART).
  Existing isolated `ember-lte` uses UDP10018. All publish on host loopback.
- LibreSDR enumerates as USB `2500:0020`, B210-compatible, with UHD4.8 and Python
  UHD/NumPy installed. No GNU Radio or SciPy was found on the Pi.
- Use the existing custom image at
  `/home/ngrabbs/work/ember-lte/images/usrp_b210_fpga.bin`, SHA256
  `7f0e329b4724e0d919a06b9924aaa3c77305b6f25038deebd6171657ac7c8a99`.
  Its provenance is described in the [LTE inventory](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/ground/lte/INVENTORY.md).
- LTE softmodem/EPC/receiver processes were absent and LibreSDR had no USB owner
  at inspection. Recheck ownership immediately before each radio session.
- User selected antennas and approximately 434 MHz. Exact RF connectors and
  initial gain/channel settings must match the physical setup before transmission.

LibreSDR is the RF hardware, not the Yamcs bridge. A UHF application must own the
radio, demodulate/decode the waveform, validate the original EMBER packet and
hand those bytes to Yamcs. LTE's OAI/EPC chain performs a different role and is
not required for the UHF path. Only one application may own LibreSDR at a time.

## Isolated Yamcs input

`prepare_yamcs.py` clones the existing prepared telemetry-only LTE instance
configuration into `ember-uhf`, using `eps-uhf-in` UDP10019, the shared EMBER MDB,
preprocessor and display bucket. It preserves existing instance files and archives.
It refuses to overwrite a differing UHF config and saves the old instance list.
No uplink/TC data link is configured for the first telemetry milestone.

From the repository root on the Pi:

```sh
python3 ground/uhf/prepare_yamcs.py
```

Append `compose.uhf.yaml` to the existing `COMPOSE_FILE` value in
`ground/yamcs/.env` (retain its USB override). From `ground/yamcs`, recreate only
the Yamcs service with `docker compose up -d --no-deps yamcs`. This briefly
restarts the server; it preserves the data volume and other services.
Do not remove data volumes. The normal `ground/yamcs/prepare.py` can be followed
by this additive preparation step whenever refreshing the lab.

[UHF EPS display](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember-uhf__realtime)
uses the existing display and dictionary, with UHF-only archive/processor state.
A blank/stale display is expected until actual decoded RF packets arrive.

## Acceptance and remaining work

- [x] Inspect USB/UART/LTE separation and current Pi/LibreSDR inventory.
- [x] Verify custom LibreSDR FPGA hash and absence of active LTE radio ownership.
- [x] Prepare isolated `ember-uhf` configuration and additive port override.
- [x] Deploy and verify UHF Yamcs instance with zero initial RF packet count.
- [x] Implement a separate binary packet bench application without changing AMSAT's text transponder demo.
- [x] Verify software decoding under timing/frequency offsets and noise; reject truncated packets.
- [ ] Broaden malformed-frame and interference rejection tests before operational use.
- [x] Start a bounded receive-only LibreSDR capture using the physical antenna port.
- [x] Send a newly CAN-delivered EPS packet from SDRB over UHF.
- [x] Match original CAN packet, RF decoder output and Yamcs archive byte-for-byte.
- [x] Confirm Yamcs displays that packet's parameters; preserve a paused archived-proof processor.
- [x] Stop radio owners and preserve exact settings/results. Verify native SDRB discovery after cleanup.

No flight modulation, FEC, scheduling, uplink protocol or reliable delivery is
established by this first bench packet. Keep waveform tools optional and
protocol-independent; keep EMBER dictionary validation and Yamcs routing in EMBER.

## Optional binary packet bench applications

`packet_radio.py` carries opaque 1..240-byte payloads. It does not know EMBER
fields. Version2 framing is distinct from AMSAT's version1 UTF-8 demo:

```text
16 × 0x55 | sync 1ACFFC1D | version2 u8 | sequence u32 BE | size u16 BE
          | opaque packet bytes | CRC32 u32 BE
```

CRC32 covers version/sequence/size/payload. Inner EMBER CRC16 is checked by the
EMBER receiver after RF decoding. Symbols are continuous-phase binary FSK,
1200 baud, deviations ±2400Hz, centered −100kHz relative to the UHD tuning.
Default center434.2MHz therefore places the packet at434.1MHz. Rectangular
frequency symbols are a bench waveform; spectral shaping/FEC are future work.

`libresdr_rx.py` uses UHD directly with the preserved custom FPGA; no LTE
software or GNU Radio installation is needed on the Pi. It mixes and decimates
2MS/s to40kS/s, saves the actual received baseband outside Git, and searches
carrier/timing with an outer CRC32 gate. A two-tone integration fallback handles
weak signals. Native IHU POWER_STATUS provenance and CRC validation reuse the
existing validator before optional byte-preserving UDP10019 forwarding. Capture
is limited to60seconds and decoding occurs after capture, so this initial app
is not a realtime modem or a continuous telemetry service.

`sdrb_tx.py` is a separate GNU Radio/UHD application, staged in an optional home
directory. It uses SDRB channel1 / TX1A_Direct1, the same path as the saved native
flow graphs. It emits a finite packet between silence intervals, attenuates to
minimum gain on cleanup and starts no service. It does not use or change the
AMSAT text transponder. The packet file must be extracted on SDRB from a new,
validated CAN monitor record; an arbitrary host-made EPS file does not prove the
IHU→SDRB portion. Save the exact CAN record and IHU return for comparison.

Example receiver invocation (after checking exclusive LibreSDR ownership):

```sh
PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember \
python3 libresdr_rx.py --seconds 60 --channel 0 --gain 40 \
  --frequency 434200000 --forward --output /path/to/new/capture
```

Wait for `UHF_RX_READY` before invoking the SDRB sender. Use the actual RF antenna
ports and a reviewed bench gain setting. Gain is a UHD setting, not calibrated
radiated power. `source_samples_emitted` only proves software consumption; require
an RF CRC-valid packet and a separate matching Yamcs archive record.

Software checks run on a host with NumPy, without opening either radio:

```sh
python3 test_packet_radio.py -v
```

The RF captures stay at `/home/ngrabbs/work/ember-uhf-evidence-20261003` on the Pi;
small sanitized results are retained under `results/2026-10-03/evidence` here.
SDRB optional applications are under `~/ember-uhf-20261003`; the native CAN monitor
remains a separate optional application with application replies suppressed.

## First end-to-end demonstration — October 3, 2026

[Result and byte-identity proof](results/2026-10-03/evidence/result.json):
one native IHU POWER_STATUS packet crossed CAN into SDRB, then antennas/UHF into
LibreSDR, then UDP10019 into the isolated Yamcs archive. The third bounded radio
trial decoded it; the first two did not. Stream errors were absent in all three
LibreSDR captures. Settings and source identities are recorded; success is not
a reliability result or an isolated gain/pipeline/decoder comparison.

[Paused UHF proof dashboard](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember-uhf__eps-uhf-proof)
is held at the actual RF archive reception. It shows VIN10.547V, output10.230V,
and die21.851°C. Realtime correctly expires between packets. The
[screenshot](results/2026-10-03/evidence/yamcs-uhf-proof.jpg), archive bytes and
parameter values are saved. Replay uses Yamcs
[Create Processor](https://docs.yamcs.org/yamcs-http-api/processing/create-processor/)
and [Edit Processor](https://docs.yamcs.org/yamcs-http-api/processing/edit-processor/);
subscribe the display before replaying the single packet, then pause at its
generation time. Recreate this session processor after a server restart.

Follow-on automatic admission and incremental reception results are recorded
below. These components remain outside AMSAT's existing text/transponder core.

## Repeatability and automatic forwarding — October 3, 2026

[Measured results](results/2026-10-03/reliability/result.json): two fully timed
five-burst antenna series recovered 5/5 and 4/5, respectively. All nine received
payloads match the saved native packet and separate Yamcs archive records. This
is a 9/10 bench observation, not a reliability qualification. Burst304 was not
recovered by additional offline decoding of the saved I/Q; its RF/decoder cause
remains unresolved. The earlier series100..104 is excluded from this denominator:
waveform preparation consumed the receive window and later bursts were outside it.
Its old receiver also suppressed distinct outer sequences sharing inner bytes.

Three subsequently generated IHU POWER_STATUS packets (inner sequences4..6,
readout counts5..7) passed automatically through passive CAN monitoring, a bounded
forwarding queue, SDRB TX, incremental ground RX and Yamcs. Their128bytes match
at IHU/CAN/TX/RF/archive. No new telemetry was injected from a ground host.
All three sessions had no RX stream errors or dropped decode windows.

`libresdr_live_rx.py` continuously captures within a finite1..600second session.
A separate decoder process examines8second windows every4seconds, including the
last partial window on stop. It runs both detectors so one decoded strong burst
does not suppress weak bursts. It forwards during capture, records before
forwarding, and suppresses overlapping detections by outer sequence and payload
hash (4096recent identities). It saves low-rate raw complex64IQ in`baseband.cf32`
and separate capture/decoder JSON. A three-window queue bounds memory; overload
is counted explicitly. Window dwell plus decoding adds several seconds of latency.
This is incremental bench reception, not a symbol-by-symbol flight modem.

`can_forward.py` is an EMBER-specific optional application beside the generic
sender. It follows **newly appended** passive monitor records, validates native
POWER_STATUS and producer identity, suppresses repeated producer/inner-sequence
identities, and queues at most two waiting packets. Queue-full observations are
logged and not silently retried. It limits sessions to600seconds and admission
to10packets, paces TX starts at least8seconds apart, and records local TX success
separately from RF delivery. It emits no CAN replies. The underlying monitor and
AMSAT applications are unchanged. Each packet opens a separate finite GNU Radio
sender: measured local processing is about20seconds per packet, so use at least
25seconds between fresh observations until a reusable transmitter owner exists.
The adapter ignores records already present when it starts; restart does not
replay its old backlog. Persistence across IHU resets, stale queue expiration,
ACK/retry and fault recovery still need qualification.

### Repeat a saved-packet series

On SDRB, **before starting ground capture**, prepare the waveform without opening
the radio. Use new filenames and outer sequences for each run:

```sh
python3 ~/ember-uhf-20261003/sdrb_tx.py \
  --packet ~/ember-uhf-20261003/packet-01.bin \
  --output ~/ember-uhf-20261003/prepared-repeat.json \
  --sequence 500 --count 5 --interval 8 --frequency 434200000 --prepare-only
```

Wait for`UHF_TX_PREPARED`. On the Pi, start reception:

```sh
cd ~/work/ember-uhf-20261003
PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember \
python3 libresdr_live_rx.py --seconds 60 --channel 0 --gain 40 \
  --frequency 434200000 --forward --output ~/work/ember-uhf-repeat-rx
```

Wait for`UHF_RX_READY`, then on SDRB:

```sh
python3 ~/ember-uhf-20261003/sdrb_tx.py \
  --packet ~/ember-uhf-20261003/packet-01.bin \
  --prepared ~/ember-uhf-20261003/prepared-repeat.json \
  --output ~/ember-uhf-20261003/tx-repeat-series.json \
  --sequence 500 --count 5 --interval 8 --frequency 434200000 --gain 70 --transmit
```

Preparation produces a temporary sparse IQ file. It remains for the prepared
run; after stopping TX, delete the **exact `iq_path`** recorded in its manifest.
The manifest cannot be reused after that deletion or a reboot. Gain70 is the
successful bench UHD setting, not a calibrated radiated-power measurement.
Use`assess_series.py` with TX JSON, RX`decoder.json` and`capture.json` for measured
delivery and identity. Independently compare each RF payload/reception with Yamcs
archive records on`eps-uhf-in`. TX sample consumption alone is not delivery.

### Repeat fresh IHU automatic forwarding

Use the same wiring and radio ownership checks. On the Pi start the live receiver
as above, with`--seconds 120` and a new output directory. On SDRB start the existing
passive CAN monitor (CAN1's observed actual bitrate is499999Hz for the500kbit/s bus):

```sh
sudo ip link set can1 type can bitrate 499999 restart-ms 0
sudo ip link set can1 up
python3 ~/ember-can-monitor-20261003/sdrb_can.py \
  --interface can1 --seconds 120 --output ~/ember-can-repeat
```

After the monitor reports ready, in another SDRB shell start the optional adapter:

```sh
PYTHONPATH="$HOME/ember-can-monitor-20261003" \
python3 ~/ember-uhf-20261003/can_forward.py \
  --records ~/ember-can-repeat/packets.jsonl --output ~/ember-rf-repeat \
  --seconds 105 --limit 3 --sequence 600 --frequency 434200000 --gain 70 --transmit
```

Wait for`CAN_RF_FORWARD_READY` and ground`UHF_RX_READY`. On the IHU USB console
(115200baud, DTR asserted), issue`hello` once and require`CAN_HELLO_CONFIRMED`.
Issue`eps telemetry` three times, at least25seconds apart. Require correlated
`WALTER_BENCH_RETURN` results. COMMS remains the CAN responder; the SDRB monitor
must stay without`--respond`. Save IHU returns alongside CAN records, adapter
results, RF records and Yamcs archive bytes.

Applications exit after their bounded sessions. Stop reception with Ctrl-C if
needed; it stops capture and drains the decoder before releasing the radio.
Return CAN1 down after the monitor exits with`sudo ip link set can1 down`.
Check native`uhd_find_devices --args type=sdrb` reports`claimed: False`, and confirm
LibreSDR has no USB owner. No startup service or continuous RF transmission is
installed by this procedure. All existing AMSAT demo, FPGA and boot files remain
outside this optional workflow.

### Next work

- Investigate the missing burst using preserved IQ and controlled RF conditions.
- Qualify packet delivery, frequency drift and gain margins on a conducted path.
- Reuse a bounded transmitter owner to remove per-packet UHD initialization cost.
- Define stale queue expiration and test physical disconnect/reset/recovery.
- Expand interference/malformed-frame tests before enabling longer operation.
- Agree flight modulation/FEC, scheduling, uplink and ACK/retry separately.

## Persistent GNU Radio owner and side command

The optional `radio_service.py` holds UHD open once. `add_packet.py` is a separate
standard-library control client: it submits an opaque binary file, requests status,
or requests stop. The GNU Radio process does not import the EMBER dictionary or
parse CAN. The EMBER-specific `can_forward.py --service-socket ...` performs native
packet admission and hands unchanged bytes to this generic local interface.
Existing AMSAT transponder and text/BPSK applications remain unchanged.

```text
RX1 / antenna_in → native FFT low-pass + gain → Add → TX1A_Direct1
                                               ↑
                     pipe source: zeros / queued binary FSK packets
                                               ↑
                     add_packet.py or optional EMBER CAN adapter
```

Transponder mode receives at435.1MHz. The nominal forwarded half-bandwidth is20kHz
around the434.2MHz transmit center, with20kHz filter transition. Telemetry remains
at434.1MHz,100kHz below center. This reserves spectrum beside the forwarded
passband rather than replacing the repeater with telemetry. The filter is new
only in this optional application; it is not a change to the AMSAT baseline.
This is linear IQ frequency translation, not FM audio demodulation/re-modulation.
Telemetry mode uses zeros instead of an RX source and does not open the receiver.
Forwarding scale defaults to0.5 and permits at most16 for measured bench inputs.
The default application uses the original adder. With the separately built
`headroom_mix.so`, `--forward-peak .25` replaces that adder with a native magnitude
limiter/mixer; see the bounded check below. Check input amplitude and total waveform
headroom before increasing gain. RX async errors and TX async errors stop the application before further
admission; burst acknowledgments are recorded without being treated as errors.

[Persistent-mode evidence](results/2026-10-03/persistent/result.json): one saved
packet decoded with persistent telemetry-only TX. Then three fresh IHU packets
(inner sequences13..15) crossed passive CAN monitoring, socket submission, a
single750kS/s transponder flow, RF, LibreSDR and Yamcs. Their128bytes match at each
stage. Preparation was2.71..2.87seconds; no per-packet UHD initialization occurred.
The side stop command closed the81second run cleanly. Queue/IPC checks passed on
Pi and SDRB, and a software GNU Radio test preserved an in-band tone, suppressed
an out-of-band tone, and recovered the added binary packet intact.

**Limits:** SDRB still reported RX overflows and TX underflows. The1.5MS/s full
transponder attempt ended with a native UHD control timeout and watchdog stop.
750kS/s stayed open and delivered the three packets, but has not qualified
uninterrupted repeater service. No independently generated over-the-air amateur
uplink was used: the forwarding/filter/addition path has software proof, while
telemetry during an active native RX/TX flow has RF proof. These are distinct
claims. The earlier750kS/s attempt finished its bounded session before telemetry
submission; its late submissions were rejected and contribute no RF success.
Do not treat `ready`, queue admission or downstream sample counts as RF delivery.

### Start, submit and stop

On **SDRB's petalinux shell**, with a new output directory and both radios free:

```sh
python3 ~/ember-uhf-20261003/radio_service.py \
  --mode transponder --rate 614400 --rx-frequency 435100000 --rx-gain 30 \
  --tx-frequency 434200000 --tx-gain 70 --seconds 120 \
  --output ~/ember-radio-repeat --transmit > ~/ember-radio-repeat.log 2>&1 &
```

Wait for `BINARY_RADIO_READY`, then from the same console or a second SDRB shell:

```sh
python3 ~/ember-uhf-20261003/add_packet.py --status
python3 ~/ember-uhf-20261003/add_packet.py \
  --packet ~/ember-uhf-20261003/packet-01.bin
python3 ~/ember-uhf-20261003/add_packet.py --stop
```

Each submission adds one packet while forwarding continues. The app uses a private
owner-only Unix socket at `~/.cache/ember-binary-radio/control.sock`. A lock is
acquired before opening UHD; unrelated radio applications still require manual
ownership coordination. `--seconds 0` explicitly holds the owner until the side
stop command or a signal; use bounded sessions for bench checks. In telemetry
mode, omit RX settings. Both modes now default to614400S/s, giving512 samples per
1200-baud symbol; the driver chooses the RFIC clock/filter path. Live packet peak
defaults to0.12 and is bounded to0.01..0.15. Earlier750k/1.5MS/s settings remain
explicit experiment choices. The original finite sender remains independent.

The ground `libresdr_live_rx.py --forward` procedure above is unchanged. It must
report `UHF_RX_READY` before submission. Save the console log along with service
`result.json`/`events.jsonl`, received IQ and packet records, and Yamcs archive
comparison. The private queue accepts two waiting packets plus the active packet,
expires waiting packets after15seconds, and never automatically repeats them.
A request ID identifies one submission; repeating an ID with identical bytes
returns the original admission without adding another packet. A conflicting ID
is rejected. The client prints its ID before IPC, so uncertain outcomes can be
correlated with service events. The cache retains64recent IDs, not restart history.

For fresh automatic telemetry, start the passive CAN monitor as above, then:

```sh
PYTHONPATH="$HOME/ember-can-monitor-20261003" \
python3 ~/ember-uhf-20261003/can_forward.py \
  --records ~/ember-can-repeat/packets.jsonl --output ~/ember-forward-repeat \
  --service-socket "$HOME/.cache/ember-binary-radio/control.sock" \
  --seconds 80 --limit 3 --transmit
```

The running service owns RF settings and outer frame sequences. The CAN adapter
uses IHU boot/inner sequence for submission IDs and reports `service_admitted`
separately from local finite-sender completion. Its acknowledgment means queued,
not transmitted or received. Wait for both monitor and adapter readiness, then
issue `hello` and fresh `eps telemetry` commands on the IHU. The successful run
used roughly8seconds between observations. Finish with the side stop command,
wait for `BINARY_RADIO_STOPPED`, and return CAN1 down after the monitor exits.
No startup service was installed.

The [clock/transport correction](CLOCKING.md) establishes a bounded error-free
614.4kS/s operating profile. Next qualify longer operation within that profile,
then perform an independent uplink-tone/receive proof and operator waveform tests.
Retain the same narrow opaque-packet interface for EMBER and the future own board.

## Prepared translated-uplink proof and telemetry cadence

`repeater_probe.py` is optional bench instrumentation. One LibreSDR UHD owner
sends a finite uplink through `TX/RX` and receives the downlink through `RX2`.
Confirm the selected TX connector has an antenna and is free before running it.
The default uplink center is435.1MHz; six-second slots alternate silence,
+5kHz, silence and+11kHz. With SDRB forwarding435.1→434.2MHz, the receiver
looks for translated tones at434.205 and434.211MHz. Matching frequency changes
and silent intervals distinguish forwarding from ambient signals and direct
uplink leakage. It records a spectrum measurement every250ms, TX errors and
hardware timestamps beside the normal telemetry capture/decoder evidence.

Run the persistent SDRB transponder from the earlier procedure first. Then,
on the ground Pi, from the staged UHF directory:

```sh
PYTHONPATH=/home/ngrabbs/work/MSU_Cubesat/ember/ground/ember \
python3 repeater_probe.py --seconds 80 --channel 0 --tx-channel 0 \
  --frequency 434200000 --gain 40 --uplink-frequency 435100000 \
  --uplink-gain 0 --uplink-peak .1 --forward --transmit \
  --output /home/ngrabbs/work/ember-uhf-evidence-20261003/repeater-proof/rx-01
```

Each output directory must be new. This replaces the normal LibreSDR receiver
for that session; it owns both directions. No separate transmitter process may
open the same radio. Two bounded sessions were executed; translated uplink tones were not detected.
Keep startup/readiness, RF tone evidence and decoded telemetry results separate.

`ihu_cadence.py` provides a finite, configurable **host-triggered** cadence for
the existing IHU CAN bench image. It sends `hello` once and `eps telemetry` at
the requested interval; IHU performs the real EPS read and packet encoding.
It validates correlated returns and packet producer/session, and stops on a
pending transaction, reboot or increased CAN error counters. Start the passive
SDRB CAN monitor and existing `can_forward.py` socket follower before triggers.
On m75q, from the staged EMBER checkout:

```sh
python3 ground/uhf/ihu_cadence.py \
  --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 \
  --interval 8 --count 8 --generate \
  --output system/sdrb/evidence/repeater-proof-01
```

This is bench automation through USB, not native autonomous IHU scheduling.
No firmware flash, charger configuration, LTE window or AMSAT core change is
needed. Bounds are1..10 packets,5..60second spacing and at most120seconds.
Radio/CAN forwarding readiness remains the operator/orchestrator's precondition.
The two preparation checks cover tone/noise discrimination and fail-closed CAN
status handling. Hardware cadence now passes16/16 fresh packets through RF and
Yamcs across two separate approximately94second streams, with zero reported
stream/UDP errors. [Recorded verification](results/2026-10-03/repeater-proof/result.json)
keeps that telemetry result separate from the unsuccessful RF repeater proof.

The earlier antenna checks did not detect stable tones at either SDRB receive
channel. The subsequent operator-confirmed conducted path is LibreSDR TXA
(channel0) → DC blocks / approximately40dB attenuation → SDRB `antenna_in`.
SDRB receive-only RX1 capture now detects both tones at approximately37dB spectral
SNR. The downlink remains antennas from SDRB TX1 Direct to LibreSDR RX2/channel0.
No AMSAT core/FPGA/boot change was made.

The initial orchestration took CAN1 down before the finite monitor ended, causing
ENETDOWN after all packets were recorded. Stop or wait for the CAN monitor before
taking the interface down. Conducted integrated runs now use a shorter finite
monitor and wait for it before CAN shutdown; no ENETDOWN was observed in those
runs. A separate short monitor check also verifies natural completion.

## Conducted forwarding and simultaneous telemetry — October 3, 2026

[Exact sources, settings, failures and byte verification](results/2026-10-03/conducted-proof/result.json)
retain the full progression. With digital forwarding scale0.5, another8/8 fresh
telemetry packets reached Yamcs but neither translated tone was measurable.
Raising the scale to16 made both tones visible; its gain-only check also delivered
3/3 fresh packets. This isolates forwarding level as a practical issue in this
bench link, without proving the cause of the earlier antenna receive failure.

The final optional application restores that gain-only sample path and adds
explicit RX/TX async error monitoring. It delivered3/3 fresh packets with exact
IHU/CAN/socket/RF/Yamcs byte identity alongside both translated tones. Settings,
on/off spectral measurements, full logs and UDP counters are in the result.
The final stream lasted62.09seconds with zero reported U/O, empty RX/TX async
error counts, zero UDP receive/send errors and zero ground stream/decode-window
errors. The two tones measured15.5 and16.9dB above silent slots, with median
spectral SNR23.2 and23.7dB. These are finite bench observations, not an endurance
qualification. Both radios were released, the control socket closed and SDRB
CAN0/CAN1 returned down; the AMSAT checkout and LibreSDR FPGA hash stayed intact.

For this **conducted uplink / antenna downlink** setup, start SDRB with:

```sh
python3 ~/ember-uhf-20261003/radio_service.py \
  --mode transponder --rate 614400 --rx-frequency 435100000 --rx-gain 60 \
  --tx-frequency 434200000 --tx-gain 70 --forward-scale 16 --seconds 75 \
  --output ~/ember-conducted-new --transmit > ~/ember-conducted-new.log 2>&1 &
```

Wait for `BINARY_RADIO_READY`; then use `repeater_probe.py` with `--seconds 48`,
`--uplink-gain 20`, `--gain 40` and a fresh output directory. Start passive CAN
monitoring and the socket follower before three IHU triggers at eight-second
intervals. Stop the radio with `add_packet.py --stop`, wait for the CAN monitor
to finish, and return CAN1 down. Scale16 is a measured bench setting; the default
remains0.5. Check the input level and clipping behavior before transferring that
gain to an antenna or amateur-radio setup.

The instrumented IQ graphs and two Python limiter attempts produced stream
errors and are excluded from clean-profile claims. The native limiter candidate
passed the tone/packet function check but had six reported RX overflows and28UDP
receive drops; it was removed from the active application. Experimental sources
and software headroom checks remain in the evidence. The hardware timekeeper
advanced1.00174seconds during1.00317seconds of wall time, with matching614.4kHz
rate/clock readback; it provides no evidence of a gross clock timebase error.
Lowering SDRB TX gain70→40 lost all four telemetry packets and did not isolate
self-interference. Preserve these failures when discussing qualification.

Remaining gates: all-antenna uplink, representative SSB/voice passband behavior,
linear input-level control/AGC, calibrated RF levels/isolation, longer coexistence and
native autonomous IHU cadence. No validated uplink command protocol is implied.

## Optional compiled headroom mixer — October 3

`native/headroom_mix.cpp` replaces the two-input adder with one compiled GNU Radio
work block. It limits forwarded complex magnitude with a common real scale factor,
preserving phase; samples below the threshold pass unchanged. Telemetry has a
separate 0.15 full-scale bound. At `--forward-peak .25`, the sum cannot exceed 0.40
apart from floating-point rounding. Status reports pre/post peaks, sample counts,
clipped samples and invalid values. Invalid IQ or clipped telemetry stops the
service. Forwarded clipping is reported and permitted as protective behavior.
The block handles opaque IQ and has no CAN or EMBER packet dependency.

This is a hard limiter, not an AGC or a guarantee of linear SSB performance.
Clipping a varying envelope can create distortion and out-of-passband products.
The original FFT filter precedes the limiter; no post-limiter spectral mask has
been qualified. Analog ADC/front-end overload and RF output power are separate
checks. Keep normal repeater gain low enough that forwarded clipping is absent;
frequent limiting is a reason to reduce gain and investigate the input path.

The [evidence](results/2026-10-03/headroom/result.json) records one finite conducted
stress run: SDRB RX gain 76/TX gain 70, scale 16; LibreSDR TX gain 30 with 0.015 and 0.15
tone amplitudes; operator-confirmed DC blocks and approximately 40 dB attenuation.
Forwarded peak 1.417 was limited to 0.25000003; telemetry peak 0.12000001; combined
peak 0.37000003. Approximately 76.5% of forwarded samples were limited, so this
does not establish RF gain linearity. Both translated tones were detected:
weak 5 kHz on/off 7.80 dB, strong 11 kHz 29.94 dB. Three fresh 128-byte IHU packets
(inner 74..76) match IHU/CAN/socket/RF/Yamcs; zero RX/TX events or UDP errors over
60.58 seconds. Ground capture had zero errors or dropped decode windows. These
stress gains are specific to the conducted path and are not antenna defaults.

Software checks cover weak transparency, phase preservation, sum bounds,
nonfinite input, invalid settings, filtering and unchanged packet recovery.
Nine existing admission/queue/probe checks also pass. Radios were released,
CAN0/1 left down, custom LibreSDR FPGA hash preserved, and AMSAT Git stayed clean.
The previously paused EPS display was not updated; this run verifies new archive
records, not a new display proof. Recompute the result from saved evidence with:

```sh
python3 ground/uhf/results/2026-10-03/headroom/verify.py
```

Build the module against the exact installed GNU Radio 3.10.10/Python 3.12 runtime.
The current m75q build uses read-only PetaLinux staging and the existing
`vivado:2024.2` container. Stage the files from `ground/uhf/native/` in
`/home/ngrabbs/work/ember-uhf-headroom-20261003/source`, then run on m75q:

```sh
runtime=/media/ngrabbs/BACKUP-A/sdrb-uhd-linux-20260916/sdrb-uhd
taskdir=/home/ngrabbs/work/ember-uhf-headroom-20261003
docker run --rm --user 1000:1000 \
  -v "$runtime:$runtime:ro" -v "$runtime:/build/sdrb-uhd:ro" \
  -v "$taskdir:$taskdir" vivado:2024.2 \
  python3 "$taskdir/source/build_native.py" \
  --runtime-build "$runtime" --output "$taskdir/build"
```

The second read-only mount resolves the toolchain's original ELF interpreter
path. The builder creates its own sysroot/tool symlinks, copies only glibc's text
linker script into that private sysroot for prefix resolution, and uses the
installed GNU Radio/spdlog/fmt compile definitions. It changes no SDK packages
or installed SDRB libraries. `build.json` records sources, compiler flags and the
stripped module hash. The tested hash is
`b893aece99f12be0753eaeecfac528fb69265ee48959e51db2bd6d0773ddbcf5`.

Copy `headroom_mix.so` beside the optional `radio_service.py` in SDRB's home
directory. Run `test_headroom.py` from that directory and
`python3 test_native_mix.py --headroom` before RF use; neither opens a UHD device.
Add `--forward-peak .25` to an already validated transponder command to opt in.
Omitting it retains the previous adder and needs no native module. No startup
service or published AMSAT image change is made. GNU Radio scheduler overhead
and DSP cost remain relevant to U/O; this successful finite run does not qualify
arbitrary graphs, sample rates or indefinite operation.

## Antenna uplink gate — October 3

[Antenna check evidence](results/2026-10-03/antenna-proof/result.json): with antennas
restored, a 59.88-second transponder run delivered 3/3 fresh packets (inner 77..79)
with byte identity at IHU/CAN/socket/RF/Yamcs and zero RX/TX/UDP errors. It used
SDRB RX gain 60/TX gain 70, forwarding scale 16 with the optional 0.25 limiter,
and LibreSDR TX gain 20/amplitude 0.1. The translated tones did **not** pass:
5 kHz on/off 0.17 dB, 11 kHz −0.19 dB. Telemetry success does not qualify uplink
forwarding or SSB operation.

A subsequent 24-second SDRB receiver-only capture repeatedly showed a weak
candidate near 4.2 kHz, consistent with the previously observed offset of the
5 kHz uplink tone. Candidate median spectral SNR was 12.83 dB, maximum 15.94 dB;
the conducted receiver check had approximately 37 dB. LibreSDR's local receive
control saw both tones clearly, but local TX leakage does not establish antenna
efficiency. Receive-only timing is not aligned to ground TX timestamps, and
the 11 kHz slot overlaps only the end of the capture. This does not isolate
self-interference. The first receiver helper aborted on an incorrect sink output
counter; that invalid attempt is retained separately. The corrected input counter
passed a software check and the receiver captured 1,843,200 samples.

The operator then reported stock LibreSDR antennas, a tiny Wi-Fi/900 MHz antenna
on SDRB, and approximately 12 inches of separation. Antenna selection and link
margin were the next checks; the controlled antenna repeats are recorded below. SSB remains pending. Both
radios were released, CAN0/1 left down and the AMSAT checkout stayed clean.

[Controlled SDRB antenna swap](results/2026-10-03/antenna-uhf-swap/result.json):
the operator fitted a UHF antenna to SDRB antenna_in while keeping LibreSDR's
stock antennas, spacing and radio settings unchanged. The 59.55-second repeat
delivered another 3/3 fresh packets (inner 80..82), byte-identical through Yamcs,
with zero RX/TX/UDP errors and zero forwarded/telemetry clipping. Forwarded peak
was 0.208 and the sum peaked at 0.233. The limiter was inactive, so clipping does
not explain the forwarding failure in this run. Tone contrast improved to
1.18 dB and 2.09 dB, still below the forwarding gate. A subsequent check fitted a UHF antenna on LibreSDR TXA, recorded below;
the earlier stock antenna bands remain unverified. Do not promote these telemetry successes to antenna repeater or SSB
qualification.


[Both UHF antennas](results/2026-10-03/both-uhf-antennas/result.json): after the
operator confirmed UHF antennas on both radios, the unchanged profile ran for
60.76 seconds and delivered 3/3 fresh packets (inner 83..85), byte-identical at
IHU/CAN/socket/RF/Yamcs. RX/TX event counters and UDP errors stayed zero. Five
forwarded samples were limited, with no telemetry clipping or invalid samples.
The translated tones still failed: 5 kHz on/off 0.86 dB, 11 kHz 0.94 dB, below
the gate of 10 dB contrast and 15 dB spectral SNR. This finite check passes
telemetry and streaming, while antenna forwarding and SSB remain unqualified.
The archived packets were verified independently of the old paused EPS display.

The [read-only routing review](results/2026-10-03/both-uhf-antennas/routing_review.json)
found no documented mapping mismatch: channel 1 selects RX1/TX1 Direct, and
435.1 MHz selects the documented RLP-470+ receive route. Checkout source hashes
are retained; the deployed module hash and physical switch voltages/path loss
were not verified. The next proposed check is actual LibreSDR TXA output level
with an RF analyzer, followed by measured link margin and duplex isolation.
Further gain/rate sweeps are not justified by these results. Radios were
released, CAN0/1 left down, the custom LibreSDR FPGA hash preserved and the
AMSAT checkout remained clean. Recompute the latest result with:

```sh
python3 ground/uhf/results/2026-10-03/both-uhf-antennas/verify.py
```


## HT transponder and repeated telemetry — October 3

[Saved result](results/2026-10-03/handheld-proof/result.json) and
[test notes](results/2026-10-03/handheld-proof/README.md): the operator transmitted
an HT at 435.1 MHz and monitored the translated 434.2 MHz signal on an RTL-SDR,
reporting that forwarding continued throughout the test. Telemetry remained at
434.1 MHz, with LibreSDR receive-only. SDRB streamed for 203.27 seconds with zero
RX/TX events or UDP errors. Nine fresh IHU packets at 20-second intervals
(inner 86..94) match byte-for-byte at IHU/CAN/socket/RF/Yamcs; ground reception
had no errors or dropped decode windows. This demonstrates the antenna forwarding
path with the HT by operator observation, separately from the earlier failed
LibreSDR source-tone test.

The limiter clipped approximately 7.45% of forwarded samples, with no telemetry
clipping; SSB/distortion and calibrated analog headroom remain unqualified.
The ground receiver's setup allowance was too short, so it ended before the
advertised three-minute observer window completed. SDRB's measured stream lasted
over three minutes; the orchestration failure is preserved separately. No exact
180-second ready-to-stop window claim is made. Future observer sessions should
establish a shared deadline after readiness and stop reception explicitly.

Optional CAN/cadence adapter limits now allow finite sessions up to600 seconds,
retaining existing defaults and the10-packet limit. No AMSAT core/image changes.
Both radios were released and CAN0/1 left down. The old paused EPS display was
not advanced; new Yamcs archive identities were checked independently.


## Native automatic IHU telemetry — October 3

[Verified automatic flow](results/2026-10-03/native-autotelem/result.json): the
IHU CAN bench firmware now generates fresh EPS telemetry locally, using the
existing native packet and CAN chain. Three packets were observed with no USB
telemetry commands at20-second intervals (19.999/20.000 seconds measured from
IHU packet uptimes). A fourth packet was generated with the USB console closed
and DTR released for25 seconds. All four original CAN payloads match the radio
socket, RF decoder and Yamcs archive. First-three IHU return bytes also match;
USB logging was absent for the fourth, whose native timer counter advanced once.
The physical USB cable stayed connected. SDRB streamed118.24 seconds in the
unchanged transponder profile, with zero RX/TX/UDP errors or clipping. No new HT
or SSB observation is claimed by this automatic telemetry check.

The IHU timer starts disabled. After normal CAN mode and a successful HELLO,
with the LTE queue off, use the IHU USB console:

```text
telem on 20
telem status
telem off
```

`telem on` defaults to20 seconds; explicit periods are5..3600 seconds. Enabling
or disabling is a control action; USB does not clock subsequent emissions.
Manual `eps telemetry` still works. Busy/unready periods are skipped without a
backlog; peer loss still needs the existing HELLO recovery. The readout uses the
existing bounded synchronous EPS reader while no CAN transaction is active.
No charger/ADC policy write or SDRB-aware packet field was added. This is the
IHU bench scheduler; production FreeRTOS integration remains separate.

The tested IHU image was backed up, installed and flash-verified; source/build/
recovery identities are retained in the evidence. COMMS/Walter and AMSAT core,
boot, FPGA and libraries were unchanged. Timer and radios are off, CAN0/1 down,
and no startup services are enabled. The later [supervision step](SERVICES.md)
adds optional radio/CAN/ground process ownership; startup reliability remains open.
The old paused EPS
display was not advanced; the proof checks new Yamcs archive bytes independently.
Recompute the saved checks with:

```sh
python3 ground/uhf/results/2026-10-03/native-autotelem/verify.py
```

`ihu_autotelem.py` is an optional finite arm/observe/off helper, with zero USB
packet triggers. The additional closed-console check is preserved in the saved
bench tools; it is not a spacecraft scheduler or operational startup service.
