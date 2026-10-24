# Isolated BMS input branch: reservoir and startup tradeoff

2026-10-24. Conditional engineering sensitivity, **not a selected integrated circuit, guaranteed TPS2553 response or UCC startup model**. The root remains at243 parts/137 nets. This work addresses the remaining isolated-supply input-current/fault-containment gate.

## Decision changed by this screen

Do not copy the proposed CAN branch's110–151 mA limit and small local capacitance onto the UCC module. Its average demand and burst demand differ. A larger local reservoir helps during bursts, but slows initial charging and can interact with the latch-off timer. Current-limit selection and capacitors must be checked together.

Run `python3 screen.py` then `python3 check_numeric.py`. The first analytically integrates the RC/current-clamped pieces over1000 pulse periods; the second independently integrates the governing ODE with a midpoint method and ≤20 ns time steps for representative cases. Last-cycle extrema agree within1 µV in the checked cases. This verifies the calculation implementation, not its device assumptions.

The imposed source is3.232799 V, series path1 Ω plus135 mΩ, capacitor ESR10 mΩ, baseline15 mA and0.8 A bursts for8.16 µs. The pulse period183.017 µs makes average demand50 mA. The source remains stiff; the limiter is instantaneous. These deliberately simplified assumptions omit actual clamp delay, soft start, latch/reset, source sag, trace inductance and UCC UVLO. The0.8 A current is a sizing scenario, not a published maximum. Supply nodes below3.0 V reject the scenario; they do not predict valid converter behavior outside its recommended range.

| Effective input capacitance | Minimum pin voltage at110 mA limit | Consequence in this imposed case |
|---|---:|---|
| 10 µF | 2.6399 V | Outside recommended operation; cannot reuse this small reservoir |
| 47 µF | 3.0786 V | About79 mV margin, before source sag or parameter uncertainty |
| 100 µF at200 mA limit | 3.1318 V | More burst margin, with larger charging demand |

The full28-case grid includes10/22/33/47/54/68/100 µF effective and110/150/200/300 mA ideal limits. Raising the clamp alone has limited benefit once the1.135 Ω path rather than the clamp sets source current during a pulse. It does not remove the need for local energy storage.

## Startup is a competing constraint

A separate charge-balance sensitivity uses nominal44/66/88 µF banks, +10% tolerance and +15% temperature expansion, charging to3.3244 V with a simultaneous assumed50 mA load. At110 mA available limit, ideal times are3.08/4.63/6.17 ms. At200 mA they are1.23/1.85/2.47 ms. These are not actual TPS output-ramp times: UCC load starts after its UVLO and changes during conversion, while the TPS timer can reset when limiting stops. The88 µF/110 mA case therefore **does not demonstrate** completion before the TPS minimum5 ms deglitch; it is not proof that the real circuit must trip. Do not use charge balance alone as acceptance.

TI [TPS2553-1 SLVS841F](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf) distinguishes the5–10 ms latch delay from the2 µs **typical** short response at5 V. A maximum initial short-response time at3.3 V is not specified. The earlier [CAN branch study](../../controller_rev_b/branch_selection/README.md) remains the source for the exact210 kΩ limit equation and initial-fault caveat. This input study does not establish survival of another shared essential load during a module short. The switch is also not a replacement for the open essential3V3 overvoltage barrier.

## Next circuit checks

Select an exact programmed-limit range with startup reserve; determine whether UCC enable must wait for reservoir charging. Check minimum effective capacitance at3.3 V and the maximum zero-bias charging bank separately. Include the LDO's post-regulator capacitor current, actual module startup bursts, essential-source reservoir/loop response, initial short pulse and resistor pulse survival. Provide a deliberate latch-reset path and default state; an in-orbit latched branch cannot depend on manually cycling RBF. Preserve all existing MCU/stack interface names and record any new GPIO allocation before integration.

The TPS2553 custom-library construction proposal is separate from this electrical selection and now has explicit S08 agreement for construction only. No native design or library was changed by this analysis. Hardware testing remains necessary to qualify current, timing, temperature, repeated faults and brownout recovery.

## Exact capacitor candidate and resistor-range screen

`capacitors.py` reads three unmodified CSVs downloaded through TDK's part-page DC-bias, temperature and ESR controls on2026-10-24; source hashes are in `capacitors.json`. The [manufacturer page](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA5L1X7R1H106K160AC) explicitly calls the characteristic curves reference data rather than guarantees. Raw source files retain the manufacturer part identity and creation date. The attempted model ZIP download did not complete; no nonlinear capacitor model was obtained or simulated.

Select **CGA5L1X7R1H106K160AC**,10 µF±10%,50 V,X7R,1206,−55..125°C as the development bulk-capacitor family. A concrete bank candidate is **eight** at the primary reservoir, **three** at isolated5 V, and **one** at the LT3014 output. The eighth primary part adds margin to the initial seven-part sensitivity, rather than treating a sub-2% calculated capacitance excess as sufficient.

Linear interpolation of TDK's25°C reference curve gives about9.874 µF each at3.3244 V,9.361 µF at5.2 V and9.855 µF at3.401 V. With independent−10% initial tolerance,−15% X7R temperature guard and an **assumed10% aging allowance**, the respective banks screen at54.38/19.33/6.79 µF. These exceed the47 µF primary sizing target and4.7 µF LDO target **conditionally**. The aging allowance is not a manufacturer lifetime guarantee, and combined voltage/temperature/aging behavior is not proven multiplicative. Verify actual effective capacitance over the operating envelope before closing that gate.

The primary charging upper sensitivity includes+10% tolerance,+15% temperature and the reference curve's+1.289% capacitance peak: about102.50 µF. At50 mA assumed simultaneous load, the210 kΩ setting's≈110 mA minimum gives about5.68 ms ideal charge time, offering no proof of startup before5 ms minimum deglitch. A **115 kΩ** resistor instead screens to **202.81–266.30 mA** with the existing0.1%/25 ppm/K/65 K assumptions, and reduces that ideal charge estimate to about2.23 ms. This is the preferred BMS-primary limit range for the next coupled check; it does not change the separate CAN210 kΩ candidate. The programmed range, normal reservoir behavior and initial-fault current are distinct quantities.

At250 kHz the reference ESR curve gives about1.63 mΩ per capacitor. Parallel-bank reference values omit cold effects, layout, ESL and current imbalance; retain the independent10 mΩ input-reservoir scenario until physical impedance is checked. A capacitance sum or reference ESR point does not establish high-frequency module stability. Nominal bank size, startup range, TPS thermal/pulse behavior, GPIO/reset ownership and measured essential-source response remain open before native circuit integration.

`average_load_sensitivity.py` additionally varies imposed average primary load50/75/100 mA at54 µF effective, retaining the same burst amplitude/width and adjusting repetition rate. At the115 kΩ screened minimum limit, input minima are3.0928/3.0752/3.0530 V; ideal charging sensitivities become2.23/2.67/3.31 ms. This exposes the importance of average-load reserve rather than treating50 mA as a guaranteed maximum. The100 mA case is a planning stress, not a datasheet current bound. Coupled source sag can consume its53 mV margin; do not claim the ideal source result closes brownout immunity.
