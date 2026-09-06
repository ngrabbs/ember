# Tektronix 7L13 A20 2.2 GHz Oscillator Characterization

## Purpose

Use this document as the bench worksheet and evidence record for the surplus oscillator marked:

```text
A20
2.2 GHZ OSC
J20  J28  J29
C20  C22
```

The working identification is a **Tektronix 7L13 A20 second-local-oscillator hybrid**, probably Tektronix part **119-0511-00**. Treat that identification and the interface map below as provisional until checked against primary documentation and the physical assembly.

The goals are to determine:

- What every connector and feedthrough does.
- Required supply polarity, voltage, current, and startup sequence.
- Whether the oscillator starts reliably and remains stable.
- Output frequency, power, tuning range, drift, harmonics, spurs, and phase noise.
- Compatibility with the proposed S-band mixer and BPSK signal.
- Whether an external frequency-lock loop is required.

This is a characterization activity, not a flight-qualified design.

---

## Critical Safety and Handling Rules

- [ ] Do **not** apply power until the C20 and C22 functions and safe voltage ranges are confirmed from documentation or a verified original circuit.
- [ ] Do **not** assume either feedthrough accepts +5 V, +12 V, or another common supply.
- [ ] Current evidence indicates that **C20 is a negative supply input** and **C22 is a collector error/tuning-voltage input**.
- [ ] Do not touch, probe, brush, clean, or blow compressed air across the ceramic substrate, transistor dice, or fine bond wires.
- [ ] Photograph the interior, then reinstall the cover before powered RF measurements. The cover provides shielding and may affect frequency and stability.
- [ ] Use ESD precautions whenever the cover is removed.
- [ ] Do not connect an antenna during characterization. Use coax, 50-ohm terminations, attenuation, and test equipment.
- [ ] Protect the analyzer or SDR with a DC block and at least 30 dB of attenuation during the first test.
- [ ] Keep the analyzer preamplifier off and begin with a conservative reference level.
- [ ] Stop immediately for unexpected current, heating, odor, unstable supply behavior, or loss of current limiting.

### Hold point before power

Powered testing is prohibited until all of these blanks are completed:

- [ ] C20 nominal voltage: __________ V
- [ ] C20 allowable range: __________ V to __________ V
- [ ] C20 expected current: __________ mA
- [ ] C22 startup voltage: __________ V
- [ ] C22 allowable range: __________ V to __________ V
- [ ] C22 source/sink current requirement: __________ mA
- [ ] Required power-up sequence: ___________________________________________
- [ ] Primary source for these values: ______________________________________
- [ ] Independently checked by: ____________________ Date: __________

---

## 1. Identification and Provenance

The Tektronix 7L13 used a nominal 2.2 GHz second LO to convert a 2.095 GHz first IF to a 105 MHz second IF. Its service documentation describes A20 as a hybrid containing the second LO, directional coupling, and filtering.

### Source records

- TekWiki 7L13 overview: <https://w140.com/tekwiki/wiki/7L13>
- Tektronix 7L13 service manual URL/archive: ________________________________
- Manual revision/date: _____________________________________________________
- Relevant manual pages/figures: ____________________________________________
- Part number shown in parts list: __________________________________________
- Other markings discovered: ________________________________________________

### Photographic record

- [ ] Exterior with cover installed.
- [ ] Cover markings.
- [ ] All connector sides and connector types.
- [ ] Interior overview without touching the hybrid.
- [ ] Close-ups of C20, C22, J20, J28, and J29.
- [ ] Photos copied into `photos/2_2_ghz_oscillator/` in the repository.

### Physical record

| Item | Observation |
|---|---|
| Overall dimensions and mass | |
| Connector types | |
| C20 and C22 terminal condition | |
| Cover/contact condition | |
| Corrosion or contamination | |
| Damaged or loose bond wires | |
| Other damage | |

---

## 2. Provisional Interface Map

| Marking | Provisional function | Status/evidence |
|---|---|---|
| A20 | Complete 2.2 GHz second-LO hybrid | Unverified |
| J20 | Main 2.2 GHz LO output to the second mixer | Unverified |
| J29 | Coupled/filtered LO sample for the frequency-control loop | Unverified |
| J28 | 105 MHz IF path associated with the second-mixer assembly; not a second LO output | Unverified |
| C20 | Fixed negative supply feedthrough | Unverified |
| C22 | Collector error/tuning-voltage feedthrough | Unverified |
| Case | RF and DC ground | Unverified |

### Questions to resolve from documentation

- [ ] Confirm the exact Tektronix part number.
- [ ] Confirm whether J28 is electrically part of A20 or routed through the same mechanical RF deck.
- [ ] Confirm which connector is the full-power oscillator output.
- [ ] Determine coupling/filtering between J20 and J29.
- [ ] Find expected power at J20 and J29.
- [ ] Trace C20 to its original rail and record polarity, voltage, and current.
- [ ] Trace C22 through the error amplifier and record its complete control range.
- [ ] Determine whether the oscillator can start safely with a fixed C22 voltage.
- [ ] Identify required startup sequence and expected transistor current.

---

## 3. Test Equipment Record

| Equipment | Manufacturer/model | Serial/asset number | Calibration/status |
|---|---|---|---|
| Digital multimeter | | | |
| Bench supply for C20 | | | |
| Low-noise control source for C22 | | | |
| Spectrum analyzer | | | |
| Frequency counter, if used | | | |
| Oscilloscope | | | |
| Temperature probe | | | |
| DC block | | | |
| 30 dB or greater attenuator stack | | | |
| 50-ohm terminations | | | |
| RF power meter/coupler, if used | | | |
| Reference/PLL equipment, if used | | | |

Record the frequency range, maximum safe input, and DC rating of every RF instrument and accessory.

---

## 4. Unpowered Inspection and Measurements

### Setup

- Cover: installed / removed
- Ambient temperature: __________ °C
- DMM model: __________________________
- Resistance-test open-circuit voltage: __________ V
- Diode-test voltage/current, if used: ______________________________________

Use a modern, low-energy DMM. Do not use an insulation tester, megohmmeter, or an analog ohmmeter with an unknown internal battery.

### Ground continuity

| Measurement | Reading | Notes |
|---|---:|---|
| Case to J20 shell | | |
| Case to J28 shell | | |
| Case to J29 shell | | |
| Case to C20 body, if applicable | | |
| Case to C22 body, if applicable | | |

### Resistance measurements

Record both lead polarities because semiconductor junctions may be asymmetric. Allow readings to settle; a changing value may be a capacitor charging rather than a short.

| Nodes | Red lead | Black lead | Initial | Settled | Notes |
|---|---|---|---:|---:|---|
| C20 to case | C20 | Case | | | |
| C20 to case, reversed | Case | C20 | | | |
| C22 to case | C22 | Case | | | |
| C22 to case, reversed | Case | C22 | | | |
| J20 center to case | J20 | Case | | | |
| J28 center to case | J28 | Case | | | |
| J29 center to case | J29 | Case | | | |
| J20 center to J29 center | J20 | J29 | | | |
| J20 center to J28 center | J20 | J28 | | | |
| J28 center to J29 center | J28 | J29 | | | |

### Optional diode-mode measurements

Only perform these if the meter's diode-test behavior is documented and safe for the assembly.

| Nodes | Red lead | Black lead | Reading | Notes |
|---|---|---|---:|---|
| C20 to case | C20 | Case | | |
| C20 to case, reversed | Case | C20 | | |
| C22 to case | C22 | Case | | |
| C22 to case, reversed | Case | C22 | | |

### Unpowered checkpoint

- [ ] No unexplained short was found.
- [ ] Asymmetric readings were compared with expected transistor junctions.
- [ ] Every unexpected reading is explained before power is applied.
- [ ] Interior photographs are complete.
- [ ] The cover is reinstalled evenly for RF testing.

Notes:

```text

```

---

## 5. Bias and Control Reconstruction

Draw or attach the reconstructed original bias circuit before powering the unit.

```text
Original supply rail ─────────────── C20 ── internal bias network ── Q20

Reference/phase detector ── error amplifier ── C22 ── collector/resonator control
```

### C20 fixed supply

| Parameter | Confirmed value | Source/page | Confidence |
|---|---:|---|---|
| Polarity | | | |
| Nominal voltage | | | |
| Allowable range | | | |
| Expected steady current | | | |
| Maximum safe current | | | |
| Required filtering | | | |

### C22 tuning/error input

| Parameter | Confirmed value | Source/page | Confidence |
|---|---:|---|---|
| Polarity | | | |
| Startup voltage | | | |
| Minimum operating voltage | | | |
| Maximum operating voltage | | | |
| Expected source/sink current | | | |
| Source impedance | | | |
| Required noise filtering | | | |

### Expected behavior

| Parameter | Expected value/range | Source/derivation |
|---|---:|---|
| Center frequency | Approximately 2.2 GHz | 7L13 architecture |
| Tuning range | | |
| J20 power | | |
| J29 power | | |
| C20 current | | |
| Tuning sensitivity | | |

Do not proceed until the hold point near the beginning of this document is complete.

---

## 6. Controlled First Power-Up

### Initial RF connection

```text
J20 → DC block → at least 30 dB attenuation → spectrum analyzer

J29 → 50-ohm termination
J28 → 50-ohm termination
```

If evidence changes the connector map, update this diagram before making connections.

### Instrument settings

| Setting | Value |
|---|---:|
| Analyzer center frequency | 2.200 GHz |
| Initial span | |
| Resolution/video bandwidth | |
| Reference level | |
| Internal input attenuation | |
| External attenuation correction | |
| Analyzer preamplifier | Off |
| C20 current limit | |
| C22 current limit | |
| Ambient temperature | |

### Stop criteria

Turn both supplies off immediately if current unexpectedly reaches its limit, a supply collapses or oscillates, the case/feedthrough heats noticeably, there is odor or discoloration, or the RF level approaches the analyzer's safe-input limit.

### First-power sequence

- [ ] Confirm a safe grounding arrangement.
- [ ] Verify both supply polarities at disconnected leads with a DMM.
- [ ] Set outputs off/zero before connecting the oscillator.
- [ ] Connect C20 and C22 using clearly labeled leads.
- [ ] Install the DC block and attenuation.
- [ ] Terminate unused RF ports.
- [ ] Apply only the documented startup conditions and sequence.
- [ ] Watch current continuously.
- [ ] Search broadly around 2.2 GHz before declaring that oscillation did not start.

| Time | C20 V | C20 mA | C22 V | C22 mA | Frequency | Analyzer level | Corrected J20 power | Case °C | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 s | | | | | | | | | |
| 10 s | | | | | | | | | |
| 1 min | | | | | | | | | |
| 5 min | | | | | | | | | |
| 15 min | | | | | | | | | |
| 30 min | | | | | | | | | |

```text
J20 power (dBm) = analyzer reading
                  + external attenuation
                  + measured cable loss
                  - calibrated gain, if any
```

---

## 7. Frequency Versus C22 Control Voltage

Only sweep C22 within its verified safe range. Hold C20 at its verified nominal value and watch both currents continuously.

| C22 V | C22 mA | C20 mA | Frequency | Corrected J20 power | Stable? | Notes |
|---:|---:|---:|---:|---:|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

- Minimum usable frequency: __________________ GHz
- Maximum usable frequency: __________________ GHz
- Total tuning range: __________________ MHz
- Approximate tuning sensitivity: __________________ MHz/V
- Evidence of mode hopping: yes / no
- Any unreliable-start regions: _____________________________________________

---

## 8. RF Output Characterization

### J20 fundamental

| Condition | Frequency | Analyzer reading | Path correction | Corrected power |
|---|---:|---:|---:|---:|
| Cold start | | | | |
| 5-minute warmup | | | | |
| 30-minute warmup | | | | |
| Minimum safe C22 | | | | |
| Maximum safe C22 | | | | |

### J29 sampled output

Move the protected analyzer connection to J29 and terminate J20. Do not assume J29 is safe without attenuation until its level is established.

| Condition | Frequency | Analyzer reading | Path correction | Corrected J29 power |
|---|---:|---:|---:|---:|
| Nominal operating point | | | | |
| Minimum safe C22 | | | | |
| Maximum safe C22 | | | | |

```text
J20-to-J29 port difference (dB) = J20 power (dBm) - J29 power (dBm)
```

Measured difference: __________ dB

This is an end-to-end port difference, not necessarily the bare coupler factor, because the J29 path appears to include filtering.

### Harmonics and spurs

| Component | Frequency | Corrected power | Relative level | Notes |
|---|---:|---:|---:|---|
| Carrier | | | 0 dBc | |
| Largest non-harmonic spur | | | | |
| Second harmonic, near 4.4 GHz | | | | |
| Third harmonic, near 6.6 GHz | | | | |
| Supply-related spur | | | | |
| Other | | | | |

- Worst spur: __________ dBc at __________ GHz
- Second harmonic: __________ dBc
- Analyzer noise floor: __________ dBm
- Measurement noise-floor limited? yes / no

---

## 9. Stability and Phase Noise

### Warm-up drift

| Elapsed time | Ambient °C | Case °C | Frequency | Change from 30-min value | Output power |
|---:|---:|---:|---:|---:|---:|
| 0 min | | | | | |
| 1 min | | | | | |
| 2 min | | | | | |
| 5 min | | | | | |
| 10 min | | | | | |
| 20 min | | | | | |
| 30 min | | | | 0 Hz | |
| 60 min | | | | | |

### Temperature sensitivity

Do not heat the vintage assembly aggressively. Change ambient temperature slowly and conservatively.

| Case °C | Frequency | Frequency change | Output power | Notes |
|---:|---:|---:|---:|---|
| | | | | |
| | | | | |
| | | | | |

Approximate temperature coefficient: __________ kHz/°C

### Phase noise

Record the method, analyzer settings, instrument floor, and whether the measurement is instrument-limited.

| Carrier offset | Free-running phase noise | Locked phase noise, if tested | Instrument floor |
|---:|---:|---:|---:|
| 100 Hz | | | |
| 1 kHz | | | |
| 10 kHz | | | |
| 100 kHz | | | |
| 1 MHz | | | |

Save close-in spectrum screenshots with reference level, span, RBW, VBW, detector, averaging, and sweep time visible.

---

## 10. Mixer and S-Band Compatibility

```text
FPGA BPSK/IF source ─┐
                     ├─ mixer → 2.4 GHz band-pass filter → amplifier → test load/receiver
A20 near 2.2 GHz ────┘
```

### Frequency plan

| Parameter | Value |
|---|---:|
| Desired RF center frequency | |
| Measured usable A20 frequency | |
| Required IF frequency | |
| Selected product: LO + IF or LO - IF | |
| Image-product frequency | |
| LO-leakage frequency | |
| RF-filter passband | |
| Required occupied bandwidth | |
| Target symbol rate | |

### LO-drive compatibility

| Parameter | Value/source |
|---|---|
| Candidate mixer model | |
| Required mixer LO level | |
| Measured J20 power | |
| Loss before mixer LO port | |
| Available LO level at mixer | |
| LO drive margin | |
| Buffer, pad, or limiter needed? | |

Frequency coverage alone does not establish mixer compatibility; compare measured J20 power with the mixer's specified LO drive.

### Modulated-signal test

| Measurement | Result | Target | Pass/fail |
|---|---:|---:|---|
| RF center frequency | | | |
| Symbol rate | | | |
| Occupied bandwidth | | | |
| Carrier-frequency error | | | |
| EVM, if available | | | |
| Constellation stability | | | |
| BER in cabled test | | | |
| LO leakage | | | |
| Image rejection | | | |
| Largest spur | | | |

If the free-running oscillator causes excessive constellation rotation, carrier-recovery difficulty, or occupied-bandwidth growth, repeat with a stabilized or phase-locked LO.

---

## 11. External Frequency-Lock Assessment

The original instrument sampled the LO through J29 and drove C22 with an error signal.

- [ ] Is the C22 tuning curve continuous and monotonic?
- [ ] Can its tuning range cover startup error, warm-up drift, and temperature drift?
- [ ] Does it mode-hop within the intended range?
- [ ] Is J29 strong and clean enough for a prescaler, mixer, or phase detector?
- [ ] What reference frequency and loop architecture would be used?
- [ ] What loop bandwidth is appropriate?
- [ ] How much C22 control-voltage noise can be tolerated?
- [ ] Does locking improve the phase noise relevant to the target symbol rate?
- [ ] What happens if lock is lost?
- [ ] Must lock detect inhibit the RF amplifier?

```text
J29 → divider/mixer → phase/frequency detector → loop filter → C22
                          ^
                          |
                   stable reference
```

PLL notes and candidate parts:

```text

```

---

## 12. Final Suitability Assessment

### Measurement summary

| Property | Result |
|---|---|
| Confirmed identity/part number | |
| Required C20 supply | |
| Required C22 range | |
| Total DC power | |
| Cold-start frequency | |
| Warm frequency | |
| Usable tuning range | |
| J20 output power | |
| J29 sample power | |
| Largest spur | |
| Second harmonic | |
| Warm-up drift | |
| Temperature coefficient | |
| Free-running phase noise | |
| Locked phase noise | |
| Startup reliability | |
| Mixer compatibility | |
| BPSK EVM/BER result | |

### Decision matrix

| Candidate use | Decision | Evidence |
|---|---|---|
| Educational microwave oscillator experiment | Pending | |
| Bench LO for 2.2 GHz + IF upconversion | Pending | |
| Free-running LO for image-transfer BPSK | Pending | |
| Phase-locked LO for image-transfer BPSK | Pending | |
| Ground test hardware | Pending | |
| Flight experiment hardware | Pending | |

Decision vocabulary:

- **Accept as-is:** Adequate without an external control loop.
- **Accept with PLL:** Adequate after frequency locking.
- **Bench-only:** Educationally useful but insufficiently stable, efficient, documented, repeatable, or robust for flight.
- **Reject for transmitter:** Cannot meet frequency, power, spectral-purity, modulation, reliability, or power-budget requirements.

### Open risks

| Risk | Evidence | Mitigation | Owner | Status |
|---|---|---|---|---|
| Unknown absolute-maximum bias ratings | | | | Open |
| Unknown condition after long storage | | | | Open |
| Exposed fragile bond wires | | | | Open |
| Unknown output power | | | | Open |
| Free-running drift and phase noise | | | | Open |
| Narrow tuning range | | | | Open |
| Possible need for external PLL | | | | Open |
| Vintage-part availability/repeatability | | | | Open |
| Mechanical/thermal flight suitability | | | | Open |

### Final conclusion

```text
Date:
Investigators:

Decision:

Supporting measurements:

Limitations:

Recommended next action:
```

---

## 13. Test Session Log

Duplicate this section for every session.

### Session __________

- Date/time:
- Investigators:
- Objective:
- Assembly configuration:
- Cover installed: yes / no
- Ambient temperature:
- Equipment used:
- Correction factors:
- Photos, screenshots, and data-file locations:

Procedure changes:

```text

```

Results:

```text

```

Unexpected behavior:

```text

```

Next steps:

```text

```

---

## 14. Data to Bring Back for Joint Review

- [ ] Source and confirmation for C20 voltage/current.
- [ ] Source and confirmation for C22 safe control range.
- [ ] Unpowered resistance readings in both polarities.
- [ ] First-power voltage and current readings.
- [ ] Carrier screenshot with all analyzer settings.
- [ ] Corrected J20 output power.
- [ ] Corrected J29 sample power.
- [ ] Frequency-versus-C22 table.
- [ ] Warm-up drift table.
- [ ] Wide-span harmonic/spur screenshot.
- [ ] Close-in carrier or phase-noise results.
- [ ] Exact mixer model and required LO drive.
- [ ] Intended RF center frequency and target symbol rate.

These results are enough to assess the oscillator quantitatively rather than merely checking whether it produces a visible 2.2 GHz peak.
