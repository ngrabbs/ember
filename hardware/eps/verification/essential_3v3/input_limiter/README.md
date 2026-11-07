# Essential 3V3 input-limiter investigation

Development checkpoint, 2026-10-24. **Neither TPS26630 nor LTC4231 is selected or integrated. MOSFET survival remains unproven.** This extends the [guard refinement study](../guard_refinement/README.md). All 218 tracked native design/library/project files remain byte-identical to 66bb97e. The existing main graph remains 318 physical parts / 175 nets / 158 functional nets / 866 endpoints across 13 sheets; those are inherited graph results, not a new export or ERC run.

## What the experiments resolve

A programmed steady current limit cannot alone contain the first fault pulse. The post-limiter buck input capacitors already store energy and bypass that limit. C400/C401/C402 total 4.5 µF nominal; the imposed high-capacitance sensitivity is 5.6925 µF, or 3.487 mJ at 35 V. Preserve the regulator's required local high-frequency decoupling; removing it simply to improve a fault simulation is not accepted. The 650 µF source reservoir remains an imposed development allocation, not the current SYS_PWR BOM sum.

`envelope.py` integrates 648 deliberately imposed current envelopes with linear magnetics. It varies local capacitance, failed-buck inductance, load, protected bank, initial current ceiling/duration and ideal complete-opening delay. The sustained 4.83 A ceiling, initial 20/45/90 A pulses, negative diode approximation and 2/6/10 µs opening times are assumptions, not TPS26630 guarantees. The simulation stops at ideal opening: remaining magnetic energy and actual switch/clamp behavior are not qualified by it.

| Imposed protected effective bank | Worst peak to ideal opening | Cases below 3.6 V at 2 / 6 / 10 µs delay (72 each) |
|---|---:|---:|
| 640 µF / 22.5 mΩ | 4.48843 V | 72 / 42 / 3 |
| 1280 µF / 11.25 mΩ | 3.92566 V | 72 / 71 / 40 |
| 2304 µF / 8.75 mΩ | 3.76869 V | 72 / 72 / 54 |

The 0.5 ns repeat preserves the same 498 below-threshold classifications; the largest protected-peak change is below 0.1 mV. Four independent LTspice solutions of the same imposed equations agree within 0.146 mV in protected peak and 0.95 ps in trip time. Their stop times come from the ODE result; threshold crossing is independently checked. This checks numerical implementation, not a real controller. The envelope also reaches about 276 A in its linear buck inductor and −2.62 V at the limiter output, so these are not physically accepted trajectories.

## TPS26630 candidate: static feasibility, dynamic gate still open

Primary sources: [TI TPS2663 Rev G](https://www.ti.com/lit/ds/symlink/tps2663.pdf) and [SLVMD03A PSpice package](https://www.ti.com/lit/zip/slvmd03a). The downloaded PDF SHA-256 is `bb61314ace65ed37684bd07f541fc676081d7cf81cb24020e7c5c2065bfe16b2`. The model archive SHA-256 is `bb66cba26abc6fb237563c04eaf5f035b868b7a84da683557f8e6572dc413997`; its encrypted `tps2663_trans.lib` is `f14c6f777d33b93dea46154d9cb3ebe530b2c41c17bd0ec408932eabdc729acb`. The encrypted PSpice model was not executed in LTspice or decrypted. Its clear public header excludes temperature characteristics and fast-trip overdrive from modeled coverage.

`static.py` records resistor/divider/slew/headroom calculations, with their test conditions. A 4.02 kΩ ILIM resistor gives 4.174–4.828 A only at the specified current-limit test point, not an initial short-circuit bound. The 9 kΩ alternative gives 1.835–2.166 A. An external UVLO divider is required for low battery operation; grounding UVLO selects an unsuitable roughly 15.5 V threshold. Grounded MODE selects retry. PGOOD needs a programmed PGTH and an enhanced internal gate: grounding PGTH keeps PGOOD low. No new MCU dependency is assumed. Available source current, inrush, dropout, efficiency, fault timing and thermal behavior remain open.

Saved Konnect stock queries identify `Power_Management:TPS26630RGE` and its RGE0024H footprint. The stock PGOOD pin is generic output rather than the datasheet's open drain. Stock peripheral lands, via count and paste differ from TI's example: these are not claimed manufacturer-exact lands. The two proposed net migrations in `static_results.json` are **not executed**.

## LTC4231 alternative: completed functional cases expose limits

Primary source: [ADI LTC4231 Rev B](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4231.pdf). Its source-referenced gate drive and negative SOURCE-pin tolerance make it worth investigating. Registered symbol search returned no LTC4231. No new library construction is authorized by the earlier LTC4368 approval, and none occurred.

The unmodified installed LTC4231-2 model and unmodified TI CSD18543Q3A model were used. Model/interface hashes are archived. UVL, UVH, OV and shutdown are forced into a test state; these decks are not complete programmable protection circuits. The input-only deck uses a constant-power load proxy. Four cases complete: low input, battery input, direct high-voltage short and low-voltage retry. Low-input retry restores about 4.365 V after fault removal, supporting nominal retry behavior only.

Two important rejection findings remain:

* At 4.5 V input, the model produces about 11.06 V gate-to-source. The datasheet low-input gate-drive table has a 10 V maximum under its stated conditions. Do not use that model voltage to qualify low-input on-resistance or gate headroom; exact low-input loading, leakage and temperature still need bounds.
* A 35 V, nearly zero-inductance direct short reaches 824.8 A and 8.91 kW instantaneous MOSFET port power. The computed positive-port energy of 15.49 mJ does not establish linear SOA or avalanche survival. This imposed circuit exceeds the CSD18543Q3A's listed 156 A pulse rating and is not accepted.

## Coupled input/output experiment

`coupled.py` joins the typical LTC4231 input controller and LTC4368 output barrier with actual CSD18543 models, an imposed finite source, linear failed-buck/guard inductors, a behavioral pre-fault buck proxy, and a generic negative gate clamp. It does not model the real converter loop, saturation, physical fault-loop parasitics, a selected clamp diode or guaranteed PVT. The pre-fault proxy stays established until the 300 ms fault; it is then disconnected before the failed high-side path takes over.

| Imposed failed-buck L / load | Protected peak, Gear | Input current peak | Failed-buck L current peak |
|---|---:|---:|---:|
| 0.1 µH / 2 A | 3.29309 V | 161.63 A | 227.85 A |
| 0.5 µH / 2 A | 3.25448 V | 99.12 A | 111.55 A |
| 3.136 µH / 2 A | 3.23896 V | 51.37 A | 48.71 A |
| 0.1 µH / no load | 3.39057 V | 161.13 A | 227.67 A |

All four Gear runs complete at 340 ms with 0.5 µs maximum step. Their first-pulse protected peaks are encouraging, but the worst input current exceeds the listed pulse rating and the magnetic currents are outside the qualified linear model. These numerical results do not release the topology. Protected voltage subsequently decays under load after isolation; sustained recovery from the now-failed converter is not shown.

The late trapezoidal run completes only the 3.136 µH / 2 A case; its other three cases fail with timestep errors. For the completed case, protected peak differs from Gear by about 9 µV, while peak input current differs by about 0.52 A. Do not extend that agreement to the nonconvergent cases. Four earlier 100 ms fault attempts are retained as diagnostics: the output gate had not settled, one completed trace had only 0.756 V before fault, and partial/externally terminated runs are not acceptance evidence. `results.json` preserves every status and exclusion rather than replacing failures with Gear results.

## Verification and remaining design gate

`archive.py` checks original deck/log/raw hashes, archives portable decks and normalized logs, and makes a plot/CSV. Vendor models and large raw files remain external. `verify.py` checks the archive, numerical repeat/crosscheck, completed versus excluded cases, native freeze and artifact bindings. It does not re-run SPICE or claim a hardware pass. Reproduction requires the model hashes recorded here and the scripts' external runtime paths; the portable decks use `${LTSPICE_LIBRARY}` and `${TI_MODEL}` placeholders.

The root actually opened `coupled_faults.png`. Manufacturer source pages actually opened this investigation: TPS2663 PDF pages 3, 29, 30, 31, 52, 53, 54 (including the reference circuit and package/land/stencil examples), and CSD18543Q3A page 6 (SOA/thermal curves). LTC4231 manufacturer-page pixel inspection remains open after retrieval failure. Simulation-plot/source-page review is separate from native sheet inspection: no new native circuit, sheet render, ERC or PCB review was performed.

The next selection gate is a bounded, physically credible initial fault pulse and interruption path, including stored local energy, source/loop inductance, negative node behavior, hot MOSFET SOA and low-input gate drive. A larger FET alone does not establish that boundary. Keep the existing solar/battery recovery intent; do not silently narrow the rail to battery-only operation to improve a test result.
