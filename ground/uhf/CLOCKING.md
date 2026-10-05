# SDRB clock and stream review — October 3, 2026

The operating profile leaves master-clock selection to UHD, requests **614400
complex samples/second**, and verifies the clock and rate after both directions
configure the shared AD9361. A correct clock alone did not eliminate streaming
loss: packet overhead, GNU Radio startup and telemetry preparation also mattered.
See the [bench evidence](results/2026-10-03/clock-review/) for separate stream and
RF-delivery results. The [final verification](results/2026-10-03/clock-review/result.json)
records a93.24second integrated transponder run with zero reported U/O or UDP
errors and6/6 fresh IHU packets matching through Yamcs. These changes belong to
the optional application; the AMSAT
FPGA, UHD/MPM libraries, boot image and existing transponder examples are unchanged.

## Which clock is which?

| Layer | Deployed behavior | Application policy |
|---|---|---|
| SDRB RF reference | FPGA `clock_select=0` selects the onboard reference. Native UHD assumes40MHz in its BBPLL calculation. External-reference selection is not implemented. | Preserve the supported board contract; this is distinct from sample-clock selection. |
| PS/transport clock | PS-generated bus clocks, including the40MHz clock advertised to RFNoC; local PPS is a free-running PS timebase. | No clock/reset/FPGA change. Local PPS does not demonstrate frequency synchronization. |
| AD9361 converter/filter clocks | Native `_setup_rates()` chooses ADC/DAC clocks, half-band filters, FIR factors and BBPLL divider from the requested radio rate. | Let this driver perform the calculation. |
| Radio sample clock | `CAT_DATA_CLK` drives the retained E310 CMOS interface and `radio_clk`. | Native UHD sets this clock when the application sets its sample rate. |
| FPGA sample conversion | Live `uhd_usrp_probe` lists only `0/Radio#0`, with direct SEP connections; no DDC/DUC or Replay block. | Do not apply B210 FPGA decimation assumptions to SDRB. Stream rate and radio clock must agree. |
| LibreSDR clock | B210-compatible UHD automatically chose32MHz for2MS/s reception: ÷16 hardware decimation. | Removed the UHF receiver's explicit16MHz master-clock argument; preserve the custom FPGA. |
| Ground software rate |50-sample averaging reduces2MS/s to40kS/s for the existing decoder. | Software decimation50 is separate from hardware clock selection. |

UHD's recommendation concerns an **integer, preferably even ratio between master
clock and stream rate**, not merely writing an even integer in the sample-rate
box. See the [UHD4.8 sample-rate notes](https://files.ettus.com/manual_archive/v4.8.0.0/html/page_general.html).
This SDRB image has no FPGA rate converter, so that ratio is1. The RFIC still
uses its own automatically selected decimation/interpolation filters. At614400S/s,
the native driver chooses2×2×2×4=32 in both directions, with nominal ADC/DAC rate
19.6608MHz. The telemetry modulator additionally gets512 samples per1200-baud
symbol. This is a convenient power-of-two symbol geometry, not a universal
requirement on RF sample rates.

## Source trace and actual readback

The reviewed deployed-source checkout is
`/media/ngrabbs/BACKUP-A/sdrb-can-20260917/source-checkout` on m75q, branch
`can-dual-20260917`, commit`543d3f6d77d278e19badd728d8e32d6f974b2586`.
The originally supplied Docker checkout contains the older IIO-era tree; it is
not the source used to explain this running native UHD image. Upstream UHD and
FPGA sources are pinned to`308126a479ca19dfaebfe4784b375e608788d763`.

1. `software/petalinux/meta-user/recipes-radio/mpmd/files/sdrb.py` and
   `sdrb_radio.py` initialize a native session at18.432MHz when no clock argument
   is provided. This is a startup default, not an immutable stream clock.
2. UHD `multi_usrp_rfnoc::set_rx_rate/set_tx_rate` use the radio's `set_rate()`
   directly when there is no DDC/DUC in the channel chain.
3. `e3xx_radio_control_impl::set_rate()` calls native AD9361 `set_clock_rate()`.
   The SDRB host patch updates radio/timekeeper rate from the **actual** returned
   clock rather than the request.
4. AD9361 `_setup_rates()` selects the RFIC filters and `_tune_bbvco()` calculates
   a power-of-two VCO divider and fractional PLL value. The40MHz `fref` here is
   the hardware-reference assumption, not a forced application master clock.
5. The unmodified AMSAT `sdrb_uhd_demo.py` only adds `master_clock_rate` when its
   operator explicitly supplies a nonzero `--master-clock`. Its old text overlay
   requests1.5MS/s. Neither establishes error-free operation at that rate.
   The four packaged `.grc` examples also default `master_clock` to0 and their
   UHD block `clock_rate` to0.0; a clock argument is added only for an explicit
   override. Their4.608MS/s sample-rate default is separate from forcing a clock.

Primary source anchors:
[RFNoC rate API](https://github.com/EttusResearch/uhd/blob/308126a479ca19dfaebfe4784b375e608788d763/host/lib/usrp/multi_usrp_rfnoc.cpp),
[E3xx radio control](https://github.com/EttusResearch/uhd/blob/308126a479ca19dfaebfe4784b375e608788d763/host/lib/usrp/dboard/e3xx/e3xx_radio_control_impl.cpp),
[AD9361 clock/filter calculation](https://github.com/EttusResearch/uhd/blob/308126a479ca19dfaebfe4784b375e608788d763/host/lib/usrp/common/ad9361_driver/ad9361_device.cpp).

Actual paired RX/TX readback was750000Hz in the old profile and
614400.0034706265Hz in the new one, for both stream rate and master clock.
The0.00347Hz difference is native PLL quantization, approximately5.65ppb. UHD's
strict floating-point comparison prints a rounded “0.614MHz vs0.614MHz” warning;
the application's tolerance check passes. No18.432MHz running-clock mismatch was
found. Requests/readbacks alone are not independent oscillator metrology.

## Corrections in the optional applications

- Both SDRB and LibreSDR UHF applications omit forced `master_clock_rate`.
- SDRB defaults to614400S/s in both telemetry and transponder modes. Requested
  analog bandwidth tracks that rate instead of remaining fixed at4.608MHz.
- Shared RX/TX rates and clocks are checked after both blocks are constructed.
- The local int0 interface has MTU9000 and this FPGA's CHDR MTU is8192bytes.
  Application transport frames are8000bytes, with RX packets of1024 samples,
  reducing packet processing overhead. This policy is specific to this deployed
  local transport; it is not a default for unrelated USRPs or Ethernet paths.
- TX starts250ms in the future on hardware time, allowing the upstream graph to
  fill before the sink's initial start-of-burst. GNU Radio otherwise sends an
  empty start-of-burst before the upstream samples necessarily arrive.
  [GNU Radio3.10.10 sink implementation](https://github.com/gnuradio/gnuradio/blob/v3.10.10.0/gr-uhd/lib/usrp_sink_impl.cc).
- Integer-symbol waveform preparation uses two short tone tables and one phase
  per symbol. It preserves continuous phase and the packet format while avoiding
  a complex exponential for every RF sample. Measured preparation fell from the
  previous2.71..2.87seconds to about0.2seconds.
- The service records TX asynchronous events and Linux UDP error-counter deltas.
  Preserve its console log too: this GNU Radio source reports RX overflow there.
  Counts concern the bounded observation; Linux UDP counters cover the whole host.

The weak-signal receiver envelope gate was also too restrictive in the first
corrected-rate trial. Two missing packets were independently recovered from saved
IQ with a1.35× median-power candidate threshold instead of1.8×. CRC32, framing,
inner EMBER validation and overlap suppression remain mandatory. Live telemetry
peak is now0.12, with a configurable0.01..0.15 bound and forwarding scale at most
0.5. The initial0.08 trial remains recorded as3/6 live reception; offline recovery
is not counted as live Yamcs delivery. This receive/link-margin work is separate
from the sample-stream corrections.

## Focused bench observations

| Check | Duration | Observation |
|---|---:|---|
| Native UHD benchmark,750kS/s full duplex |10s |0 overruns/underruns, dropped samples, sequence errors, late commands or timeouts. |
| Direct GNU Radio forwarding,750kS/s |10s |1 reported RX overflow and83 UDP receive-buffer errors; running clock readback was correct. |
| Filtered forwarding,512kS/s |10s |No reported U/O or additional UDP errors. |
| Filter + idle telemetry pipe,512kS/s |10s |No reported U/O or additional UDP errors. |
|614.4kS/s, larger transport frames, immediate TX |15s |No UDP receive drops;1 startup underflow. |
| Same profile with250ms timed TX |15s |No reported U/O or additional UDP errors. |
| Corrected persistent transponder + passive CAN +6 fresh IHU submissions |111.575s |No TX async errors, reported RX overflow, UDP receive errors or cleanup failure.3/6 decoded live, with two additional packets subsequently recovered offline. |
| Same clock/transport profile, weak-burst envelope1.35× and packet peak0.12 |93.242s |No TX async errors, reported RX overflow, UDP receive errors or cleanup failure.6/6 fresh packets decoded live and matched byte-for-byte through Yamcs. Preparation0.178..0.194s. |
| Automatic-clock LibreSDR receive-only check |8s |32MHz/÷16;16million received samples, no errors or dropped decode windows. |

This isolates a supported operating profile; it does not prove that arbitrary
sample rates or CPU loads are sustainable.1.5MS/s full duplex previously timed
out, and4.608MS/s remains unqualified. The optional307.2kS/s choice has software
waveform checks but no live radio qualification. Higher rates would need their own bounded
benchmark and may require transport/DSP improvements. Do not change core FPGA
clocks, external-reference routing or published boot artifacts based solely on
this application result. No independently generated amateur uplink was used in
that clock-profile trial.

## Conducted-uplink follow-up

The [subsequent evidence](results/2026-10-03/conducted-proof/result.json) adds a
hardware-time sanity check:614400.00347Hz TX/RX/clock readback,1.00174seconds of
hardware time during1.00317seconds of wall time. It does not support a gross
timekeeper-rate mismatch as the cause of the diagnostic late-command errors.

Receive-only conducted RX1 captures detect the two uplink tones at approximately
37dB spectral SNR. Scale0.5 forwarding was too weak to observe at the ground
downlink receiver. Scale16 forwarding made both tones visible alongside3/3
fresh telemetry packets, without changing RF gains, sample rate or driver clocks.

Extra FIR/file IQ branches and Python limiter work blocks produced U/O or late
TX commands at the same rate. Increasing diagnostic priming to one second and
batching the Python limiter did not qualify those graphs. The batched Python
attempt stopped on TX async errors in1.42seconds, before readiness or packet
generation. Keep these failures separate from clean operating-profile claims.

The native clipping / one-second priming candidate delivered3/3 packets and the
tones but logged six RX overflows and28UDP receive-buffer drops. Its function
check is not error-free stream qualification; it was removed from the active
application. The final gain-only path retains250ms TX priming and adds explicit
RX/TX async counters and fail-closed handling. Scale0.5 remains the default;
scale16 is the measured conducted setting, with manual input/headroom checks.
Strong-input level control and longer operation remain open. Clock selection,
RFIC rate, FPGA and published AMSAT sources were not changed by this follow-up.

The [subsequent headroom check](results/2026-10-03/headroom/result.json) replaces
Add with one optional compiled native mixer, avoiding extra stream stages and
Python work callbacks. With the same automatic 614.4 kS/s clock profile and 250 ms
priming, a 60.58-second conducted stress run reported zero RX/TX/UDP errors and
delivered 3/3 byte-identical fresh packets through Yamcs. Forwarded input reached
1.417 full scale; the mixer bounded it to 0.25 and the sum to 0.37 at packet
peak 0.12. Approximately 76.5% of forwarded samples were limited at these stress
gains. This proves bounded digital headroom under that workload; it does not
qualify analog headroom, linear SSB, AGC or endurance. The original adder remains
the default; the module is selected only with `--forward-peak`. No driver clocks,
FPGA, boot files, rootfs libraries or AMSAT core were changed.
