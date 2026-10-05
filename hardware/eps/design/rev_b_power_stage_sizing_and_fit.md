# EPS Rev B power-stage sizing and fit checkpoint

2026-10-04. Carry forward the LMR51635XDDCR 3.3 V buck and LM5177DCPR 5 V buck-boost for development. **No complete circuit, output-current rating or physical fit is accepted.** The operator reports 16 mm top standoff before the next board. This permits evaluation of taller inductors; subtract upper-board underside protrusions and mechanical tolerances before defining usable component height. The standoff reference faces remain to be confirmed.

[Architecture](rev_b_plan.md) · [Voltage/cutoff candidates](rev_b_regulator_and_ov_candidates.md) · [Calculator](../verification/power_stage_sizing.py) · [Numerical evidence](../verification/evidence/2026-10-04_power_stage_sizing.json)

## Load assumptions

Use 2 A per rail as a development sizing case, not an agreed requirement. Actual COMMS, IHU, payload and startup currents remain unknown. The operator's estimate of 2 A or more concerns pack load. Calculations assume 90% efficiency and use 4.5 V converter input as a sensitivity case for a provisional 5 V pack floor and 0.5 V path drop. Neither efficiency nor that drop has been measured.

| Illustrative case | 3.3 V / 5 V current | Output power | Input at 4.5 V | Input at 7.27 V |
|---|---|---|---|---|
| Idle | 0.05 / 0.1 A | 0.665 W | 0.164 A | 0.102 A |
| Recovery | 0.2 / 0.5 A | 3.16 W | 0.780 A | 0.483 A |
| Both rails at 2 A | 2 / 2 A | 16.6 W | 4.099 A | 2.537 A |

These exclude charger demand and other direct battery loads. Preserving regulated 5 V also requires coordinating protection thresholds, path losses, startup and autonomous load shedding; buck-boost topology alone does not guarantee recovery.

## 3.3 V development stage

The [LMR51635 datasheet](https://www.ti.com/lit/ds/symlink/lmr51635.pdf), SLUSF64B Rev B, supplies the 400 kHz 5.6 µH starting point and two 47 µF effective output capacitors for 3.3 V. Capacitance after voltage/temperature derating is the relevant quantity. At 35 V input, the ideal continuous-conduction ripple estimate is:

| Case | Inductance / frequency | Ripple p-p | Peak at 2 A | Peak at 3.5 A |
|---|---|---|---|---|
| Nominal | 5.6 µH / 400 kHz | 1.334 A | 2.667 A | 4.167 A |
| Initial tolerance and frequency | 4.48 µH / 360 kHz | 1.853 A | 2.927 A | 4.427 A |
| Additional magnetic/dither sensitivity | 3.136 µH / 329.4 kHz | 2.893 A | 3.447 A | 4.947 A |

The last row applies an illustrative 0.7 magnetic-inductance multiplier and frequency dither; it is not a guaranteed worst-case envelope. The 4.2 A minimum peak limit already constrains the 3.5 A case in the initial-tolerance row. Valley limit, losses, control behavior and thermal performance also require checking. Do not interpret the IC's 3.5 A label as a qualified rail rating across this application.

Inductor selection must address the applicable 6.0 A maximum peak-limit threshold during faults as well as normal ripple. [Coilcraft XAL50xx](https://www.coilcraft.com/getmedia/49bc46c8-4b2c-45b9-9b6c-2eaa235ea698/xal50xx.pdf) lists only 6.3 A typical saturation current at 30% inductance drop for XAL5050-562MEC. The larger [XAL60xx](https://www.coilcraft.com/getmedia/ea51f14b-7f32-4dc6-8dfe-d4b70549040f/xal60xx.pdf) lists 9.9 A for XAL6060-562MEC and 15.9 mΩ maximum DCR. Carry the latter as a fit reference; typical room-temperature saturation and published air-cooled current ratings do not establish hot flight performance.

## 5 V development stage

Start evaluation at 10 µH and a 10 mΩ, 1% peak-current shunt. The [LM5177 datasheet](https://www.ti.com/lit/ds/symlink/lm5177.pdf), SNVSBU4F Rev F, gives a 38.5–58.5 mV peak-sense range, corresponding to approximately 3.812–5.909 A including resistor tolerance. Nominal 5 A shunt dissipation is 0.25 W before thermal derating and pulse requirements.

The ideal mode-specific 2 A calculations give peaks of 2.525 A at 4.5 V boost input and 2.536 A at 35 V buck input. A separate 5.6 µH effective / 300 kHz sensitivity case gives 2.603 A and 3.276 A respectively. These approximate steady-state modes; operation near 5 V input requires a buck-boost transition model, not a zero-ripple extrapolation. Startup, short circuit and compensation remain open.

XAL5050-103MEC's 4.9 A typical saturation reference is below the shunt's maximum trip calculation. XAL6060-103MEC, with 7.6 A typical saturation at 30% drop and 29.8 mΩ maximum DCR, is a larger fit reference requiring temperature/current qualification. The top standoff makes evaluating this size practical; it does not qualify its height or cooling.

The [LM5177 EVM guide](https://www.ti.com/lit/pdf/SNVU797), SNVU797 Rev D, documents 400 kHz and schematic resistor **R21 = 78.7 kΩ on RT**. Use that as a documented development starting point. The datasheet frequency-section discrepancy remains unresolved; do not copy the EVM's 16 V / 150 W compensation into a 5 V design. PSM selection also requires COMMS noise evaluation.

Four [CSD18543Q3A](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf) MOSFETs provide a 3.3 × 3.3 mm physical-package reference. Their specified resistance at 4.5 V gate drive does not cover a lower gate voltage: depleted input, VCC behavior and bootstrap drops must be reconciled before selecting them. An all-four-switching charge budget using maximum 7.3 nC at 4.5 V and 400 kHz gives 11.68 mA gate-charge current, 0.053 W gate-drive power and 0.356 W additional linear-bias loss from 35 V. This is a sensitivity budget, not actual converter dissipation; conduction, switching and controller losses remain to be added.

Output capacitance depends strongly on the COMMS current step. For a hypothetical 1.9 A step unserved for 25 µs with 0.25 V allowed droop, ideal effective capacitance is 190 µF; at 100 µs it is 760 µF. These are charge-balance examples, not capacitor selections. ESR, loop response, bias derating and permitted droop must be established from the real load.

## Package and board reservations

[Konnect package readbacks](../verification/evidence/2026-10-04_power_package_readback.json) give a 7.7 × 10.2 mm courtyard for the installed generic HTSSOP-38 reference and 4.1 × 3.4 mm for generic SOT-23-6. Neither is an accepted manufacturer land pattern. In particular, the generic HTSSOP exposed pad is 2.74 × 4.75 mm while TI's DCP0038A example land uses 2.9 × 4.7 mm. Verify lead/pad mapping, thermal-pad geometry, paste and vias before native placement.

| Complete stage reservation | Previous | Revised |
|---|---|---|
| 3.3 V buck | 24 × 12 mm, 288 mm² | 24 × 18 mm, 432 mm² |
| 5 V buck-boost | 24 × 12 mm, 288 mm² | 32 × 24 mm, 768 mm² |
| Conversion total | 576 mm² | 1200 mm² |

The [revised floorplan](rev_b_floorplan.svg) adds 624 mm² for conversion stages. Its rectangles represent 5367 mm², about 62.1% of the nominal 96 × 90 mm board, including connectors/access reservations. The calculator checks rectangle bounds and overlap only. That percentage is not PCB utilization or proof of routing/fit. Exact outline, mounting holes, holder, harness bends, stack geometry, thermal paths and interference remain unverified. The 450 mm² source-isolation/solar-OV allowance may also grow.

Next implementation checkpoint: verify the exact buck symbol and land pattern through Konnect, define its full passive/enable network and thermal layout, then export and check the isolated stage. In parallel design work, resolve the buck-boost low-gate-voltage choice, transition model and compensation before freezing its BOM. Solar cutoff trip/reset and source-fault coordination remain separate blocking acceptance items. No Rev A native KiCad file was changed for this checkpoint.

The [essential buck draft](../verification/essential_buck_stage_draft.md) now records the isolated passive/enable circuit and verified six-pin package. It also establishes that 5 V output-fed BIAS does not avoid the LM5177’s high-input linear-bias loss; low-pack gate drive and an independently starting bias alternative remain open.
