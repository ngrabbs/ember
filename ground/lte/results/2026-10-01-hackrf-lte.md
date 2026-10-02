# Independent RF capture and LTE-M access failures — 2026-10-01

## Hardware and receiver

User connected HackRF One and Thingy:91 X to M75q. A USB hub/cable enumeration
failure initially disconnected Walter and prevented Thingy enumeration; after
reconnection both appeared. Walter remains on its stable Espressif by-id path.
Thingy exposes Nordic by-id interfaces ending `if01` and `if04`, USB VID/PID
1915:910a. Neither responded to a short 115200-baud AT probe. Its application
and modem firmware are unidentified; no Thingy firmware was flashed.

HackRF One serial suffix 31805783 reports firmware 2024.02.1, API 1.08.
Installed Ubuntu hackrf/libhackrf 2023.01.1-9build1. Reloaded udev rules and
triggered the USB device to resolve access permissions. User confirms a nearby
HackRF antenna, all LibreSDR connectors with antennas, and approximately six
inches between Walter and LibreSDR. The antenna path is not calibrated.

HackRF receive-only captures used center 751 MHz, 16 Msps, signed interleaved
8-bit I/Q, RF amplifier off and antenna power off. Initial gains were LNA/VGA
16/16 dB; later captures used 32/32 dB. Capture transfer lengths completed;
this is not proof of hardware sample continuity. No observed ADC rail clipping
occurred in analyzed portions. Total raw/resampled capture storage is about
647 MiB, moved off M75q root to:

`/media/ngrabbs/BACKUP-A/ember-lte/captures`

Captures and detailed logs are private and outside EMBER Git.

## Transmit path checks

The new `scripts/check-tx-rx.py` selects the checksum-verified custom FPGA,
transmits a bounded 125 kHz-offset tone on TX channel 0, and measures RX channel
1 at center 751 MHz and 2 Msps. RX uses RX2; TX uses TX/RX. At UHD TX gain 0,
digital amplitude 0.1, and RX gain 20, the tone rose 18.98 dB over baseline and
fell 20.78 dB afterward, with no reported RX metadata errors or TX send errors.
This self-check alone includes possible internal coupling.

A coordinated longer tone test at UHD TX gain 49.75 was also received by
HackRF independently: its peak appeared near +131.8 kHz (rather than exactly
+125 kHz) during the transmit interval, approximately 24 dB above the nearby
spectral background, and disappeared afterward. The frequency difference is
consistent with relative free-running oscillator offset; it is not an absolute
frequency calibration. The same-SDR tone measurement rose/fell about 69 dB.
Neither receiver showed sample clipping in the analyzed windows.

First helper attempts had an end-of-burst array-shape error and, after extending
the interval, an insufficient RX deadline. Both were fixed before the successful
coordinated test. Do not treat those early attempts as clean streaming passes.

## Independent LTE synchronization

OAI's RU TX setting is attenuation: logged UHD gain is maximum gain minus
`att_tx`. Experimental runtime copies exercised attenuation 40, 30 and 20,
yielding TX gains 49.75, 59.75 and 69.75 dB respectively. RX remained 35 dB.
These gains are not calibrated radiated power. The tracked starting config still
uses attenuation 60; do not silently equate it with these later experiments.

At attenuation 30, resampled HackRF I/Q (16 Msps to 1.92 Msps, ratio 3/25), with
an approximately 6.8 kHz frequency correction based on the tone observation,
produced consistent expected-cell PSS/SSS detections using the existing srsRAN
`pss_file` test binary (source ec29b0c1f). FFT size 128, PCI 0, threshold 2.5,
80 five-millisecond windows. Final reported average PSS peak-to-sidelobe ratio
was about 6.6, detection fraction 1.00, SSS misses 0/0/0, normal CP 100%.
This is independent LTE synchronization evidence, not a PLMN or Cat-M1 SIB decode.
The earlier threshold-0.4 noise trials are not useful cell-detection evidence.

Detailed OAI PHY logs also showed repeated PBCH generation, nonzero time/frequency
sample energy, and increasing southbound send counts. Those logs alone would
not establish RF output, which is why HackRF was added.

The new offline PBCH helper compiled against the Pi's existing srsRAN PHY library
but returned MIB-not-found on this short capture. No CRC-validated MIB, decoded
PLMN, or decoded SIB1-BR is claimed.

## LTE-M random access and concrete stack failures

During the attenuation-30 Walter attempt, OAI logged:

1. A CE-level-0 bandwidth-reduced random-access response.
2. Decoding an uplink CCCH message.
3. Generation of a 41-byte `RRCConnectionSetup`.
4. A fatal assertion at `eNB_scheduler_RA.c:1124`:
   `Msg4 Retransmissions not handled yet for BL/CE UEs`.

This is substantial LTE-M access-path progress during the Walter attempt, but
without a subscriber identity it does not conclusively attribute the request to
Walter. Walter's subsequent scan returned no listed network after the cell
aborted. No authentication or bearer appeared in the EPC log.

The attenuation-20 repeat produced repeated BR random-access responses, then
aborted at `fapi_l1.c:676`: no existing UE ULSCH for the scheduled temporary
RNTI. The exact source assertion requires an available UE ULSCH slot. UE allocation
and failed-random-access cleanup must be investigated rather than bypassing
assertions. A stronger downlink alone did not produce registration.

Walter remained unregistered through bounded CEREG polling. Afterward its original
standard LTE-M band list was restored and CFUN 0 confirmed. No eNodeB/EPC process
remained running after the bounded tests. Subscriber credentials remain private.

## Next engineering work

Keep Walter as the primary spacecraft candidate. Thingy remains a second modem
for comparison once its application/AT interface is established. The immediate
software targets are OAI's CE-mode-A Msg4 transmission/feedback/retransmission
handling and resource reclamation after failed random access. Preserve the
unmodified pinned baseline for comparisons and implement any fixes as tracked
patches with bounded regression captures. Removing a fatal assertion alone is
not an LTE-M retransmission implementation.

Relevant pinned source:
[eNB random-access scheduler](https://github.com/OPENAIRINTERFACE/openairinterface5g/blob/29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f/openair2/LAYER2/MAC/eNB_scheduler_RA.c).
