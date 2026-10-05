# HT transponder with repeated telemetry — October 3, 2026

The operator requested a three-minute HT/RTL-SDR test and selected HT uplink
435.1 MHz, transponder downlink 434.2 MHz and telemetry 434.1 MHz. LibreSDR was
receive-only. Both radios had operator-confirmed UHF antennas. The unchanged
614.4 kS/s automatic-clock profile used RX gain 60/TX gain 70, forwarding scale
16 and the optional native magnitude limit 0.25.

SDRB streamed for 203.27 seconds with zero RX/TX events and zero UDP errors.
Nine fresh IHU POWER_STATUS packets, inner sequences 86..94, were generated
at 20-second intervals. All nine original 128-byte payloads match at IHU, passive
CAN, control socket, RF decoder and separate Yamcs archive records. The ground
receiver captured 210 seconds without errors or dropped decode windows. The
operator reported seeing the HT signal retransmitted down the band and that
it continued throughout the test; no external RTL-SDR IQ or audio was saved.

The optional mixer limited 9,295,996 of 124,857,651 forwarded samples (7.45%).
Pre-limit peak was 3.109, post-limit 0.25000003; telemetry peak 0.12000001 and
sum peak 0.37000003. No telemetry clipping or nonfinite samples occurred. This
observation does not qualify SSB linearity, distortion, RF power or isolation.
It also does not retroactively pass the earlier failed LibreSDR uplink-tone gate.

The orchestration receiver deadline started before radio/console setup, leaving
insufficient allowance for the advertised 180-second ready-to-stop observation
window. The receiver exited normally before that window completed, causing the
coordinator to stop SDRB. Exact observation-window end was not recorded. Radio
stream duration, complete packet identities and the operator report are verified
separately; the orchestration failure is retained in session.json. Future timed
observer sessions should share a deadline established after all readiness gates,
with separately bounded setup lifetimes and explicit receiver shutdown.

Only the optional bench tools' maximum session bounds increased from 120 to600
seconds; the packet limit remains10 and defaults are unchanged. Three CAN
admission tests passed, changed Python files compiled, and diff whitespace checks
passed. AMSAT source/core, boot, FPGA and rootfs libraries were unchanged. The
custom LibreSDR FPGA hash was preserved. Both radios were released, CAN0/1 left
down, and the AMSAT checkout remained clean. Yamcs archive records were verified;
the old paused EPS display was not advanced.

Recompute the saved evidence checks from the EMBER worktree root:

```sh
python3 ground/uhf/results/2026-10-03/handheld-proof/verify.py
```

Raw telemetry-band IQ remains outside Git on the ground host under
`/home/ngrabbs/work/ember-uhf-evidence-20261003/handheld-proof/rx-01`.
