# TPS2553-1 nominal transient diagnostics

2026-10-24. Seven completed LTspice26.0.2 runs use TI's external unencrypted switch model with synthetic source and converter loads. **These are not a UCC/system qualification simulation.** Together with previous static/LDO/TI-calculator evidence, they support the [essential3V3 development drawing decision](../../../design/rev_b_bms_isolated_supply_integration.md). They do not close source/fault/temperature gates or authorize PCB release.

## Source and simulator compatibility

The [TI product page](https://www.ti.com/product/TPS2553-1) links [SLVM426A](https://www.ti.com/lit/zip/SLVM426), downloaded2026-10-24. ZIP SHA256 `5d4e7d9c4787ae4aafe46a794a20d0facd9ec60aecd3c12db9e44a4b842185f7`; extracted `tps2553-1_trans.lib` SHA256 `2c4436b54cf8efc9dd522e110708fcb942e741a9620d6f442c577f787f451622`. TI identifies Final1.00,2011-10-19, PSpice16.2, DRV EVM and SLVS841D. The file is an external runtime dependency, not redistributed here.

An unmodified compatibility probe completed numerically but **failed functionally**: OUT stayed off. Its log warned that LTspice interprets the PSpice XNOR caret as exponentiation. `adapt()` replaces only that subcircuit's Boolean expression with an explicit inequality implementation; every other source byte after text newline normalization is retained. The derived external library hash is `354d0e0c2e67a8d750fb0c1174b98e369139719d69d4d0df027b6d7ce9ef22f9`. Four separately simulated truth cases pass1/0/0/1 in `xnor_verified.json`. No caret warning remains. A syntax repair is not vendor approval of this simulator/model combination.

The model ports are IN/GND/EN/PWPD/FAULT_B/ILIM/OUT, **not the DBV physical pin order**. Ground/PWPD are tied to0 in these runs. This older DRV-referenced behavioral model does not bound DBV hot135mohm Ron, thermal shutdown, physical fault survival or PVT. Its fixed nominal thresholds/timing are not manufacturing limits. All runs set25C, with no claimed temperature sweep.

TI's [UCC33020 product page](https://www.ti.com/product/UCC33020) links [SLUM931](https://www.ti.com/lit/zip/SLUM931). Its90777-byte ZIP SHA256 is `d8c6baa088d51ec9a73a8059cda1a50c59b549142516c0abd77b855e7c170767`. It contains `UCC3302x_V0_enc.sxsch`, an encrypted SIMPLIS model. SIMPLIS is not installed. No conversion/decryption or UCC run is claimed. The separate TI startup-calculator and LT3014 diagnostics remain separate evidence.

## Imposed circuit and results

Source ramps in100us, followed by a **stiff50mohm source and96uF/10mohm shared reservoir**. These values are scenarios, not an accepted essential regulator/source model. TPS enables at1ms, drives1ohm into the candidate primary bank/10mohm ESR and3.9k bleeder. The load is either a voltage-limited constant sink or the earlier imposed0.8A pulse family. No real UCC UVLO, burst adaptation, efficiency, secondary capacitor charging, LDO limit or feedback is coupled here. Stop interpreting valid module operation if its pin voltage is below3V.

| Case | Settled reservoir minimum | Consequence in this nominal imposed case |
|---|---:|---|
|3V3,115k,102.65uF,50mA |3.17550V |startup completes without latch |
|3V3,210k,same bank/load |3.17550V |also starts nominally; less current/timing reserve |
|3V3,115k,102.65uF,100mA |3.11915V |higher planning load starts; no guaranteed UCC current bound |
|4.8V,115k,12.96uF,50mA |4.74126V |smaller-bank alternative has input headroom |
|3V3,115k,54.38uF,imposed bursts |3.09360V |positive margin in this source/load scenario |
|4.8V,115k,6.79uF,imposed bursts |4.13760V |more voltage margin; switch input current peaks0.52346A |

The5V/bank alternative is **not a controlled source-only comparison**: both bank and source differ, and the same imposed pulse is not asserted to be the actual UCC load at either voltage. It demonstrates a candidate tradeoff and real model overshoot, not an optimized source selection. Carry essential3V3 forward to preserve pack telemetry when the recovery+5V rail is off. Keep115k rather than reverting to the lower-current CAN setting; its full conditional range and inrush reserves remain documented separately.

The seventh case shorts the reservoir through10mohm from10–30ms. Full raw data shows a2.60497A input-current peak, shared input minimum3.16169V in the initial1ms, FAULT low at17.4947ms and switch current below1mA at17.5396ms. From23–29ms FAULT is below19.3mV and model input current is about100uA. EN low35–55ms clears the latch; reservoir exceeds3V again at57.0111ms. This demonstrates the model's nominal latch/reset behavior. The source is imposed; **healthy CAN/IHU survival, maximum short-response time and MOSFET/resistor survival remain unqualified**. The20ms low pulse in this model test is not the proposed2s firmware attempt or a guaranteed UCC power cycle.

`assembly_screen.py` includes the new discharge resistors in the previous conditional LDO/bus calculation: output static current becomes9.300mA, leaving2.700mA within the12mA allocation. Including the isolated5V bleeder and1mA LDO-ground allocation gives14.109mA intermediate demand. Side2 low/high/current/rise-time screens retain margin; the isolated rail no longer uses the old shared-positive shunt-offset correction. These are static screens and preserve the old bias/temperature/load-test caveats.

`assembly_calculator.py --source /absolute/UCC3302X-CALC-V1.xlsx` independently reuses the previously checked TI formulas without saving the workbook. Six selected-capacitance/load cases (3.0/3.3V input and14.109/50/100mA imposed output loads) estimate925–1900us startup. At the allocated load, estimated burst-on time is3.76–4.94us. Neither calculation couples the primary limiter/source or explicitly models LDO output-capacitor charging. These results update component choices; they do not close that coupled gate.

## Reproduction and actual visual inspection

Run with bundled Python/numpy:

```
python3 run_screen.py --model /absolute/external/tps2553-1_trans.lib --output /new/runtime/directory
python3 plot.py
```

Each simulator process has a45s limit. Completion requires zero process exit, the final log timing marker and raw end time20ms or60ms as appropriate. `results.json` records full-raw hashes/counts/extrema. Full raw files remain `/tmp/ember-tps2553-screen-20261024`; portable CIR templates refer to `${TPS_ADAPTED_MODEL}` and are **not KiCad source**. Logs retain Fontconfig/runtime text as generated. No simulator process remains running.

CSV exports preserve min/max of every channel in each bucket, plus all samples around the initial short; they are decimated and not substituted for full raw extraction. Six ReportLab LinePlot pages in `output/pdf/waveforms.pdf` show startup, both burst alternatives, latch/restart, the initial current pulse and the internal timer. All six actual rasterized pages were opened/inspected; the initial uniformly thinned short zoom was corrected to retain its pulse and tail, then re-rendered and inspected. Titles, axes, legends, units, source assumptions and limitations are readable and unclipped. This is **waveform visual inspection**, not schematic-sheet inspection; no native CAD was changed by these scripts.

The initial PDF operation marker invocation found no `node` on PATH. It was corrected using the discovered bundled Node runtime; the marker completed before regeneration of the final deliverable. Final source/data/artifact hashes are in `artifact_sha256.json`.
