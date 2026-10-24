# Managed payload feed calculation checkpoint

2026-10-24. Candidate only; **no payload feed is integrated**. Current native
EPS remains the345-part/14-sheet ADC checkpoint. This packet supports the
[specific power/control contract](../../design/rev_b_managed_payload_feed.md)
and [pending TPS3700 construction rules](../../design/rev_b_payload_tps3700_library_rules.md).

`python3 calculate.py` regenerates `results.json`: independent resistor corners,
source-window/eFuse thresholds, constant-power feed-loss cases, ramp/charge
energy sensitivities, a proposed clamp screen and128 ideal logical state
transitions plus nine scenario traces. These are engineering calculations,
not a vendor transient model, physical latch-timing proof or MOSFET survival.
No encrypted model was decrypted/executed. Assertions check stated arithmetic
and ideal-state invariants; they do not turn open premises into specifications.

## Findings that change the design

- At25.518W allocated input,6.889V source and an imposed130mΩ complete feed,
  the carrier sees6.368V/4.007A. The4.02k current programming sensitivity gives
  a4.174A lower edge under TI's1V-dropout test-point basis.185.8mΩ exhausts
  that current margin; a6V source is not a6V carrier input after loss. The
  proposed nonessential source-UV nominal7.16V rise/7.062V fall preserves room
  for that load case while essential recovery can continue lower.
- The100nF dVdT candidate gives396.5–610.2V/s under the stated sensitivity.
  1mF/5mF imposed carrier cases plus local bypass draw0.612/3.053A capacitive
  current; adding an imposed0.2A AON startup load remains below the programming
  screen.8.4V ramps take13.77–21.18ms. The5mF ideal charge case imposes
  176.5mJ and about27.3W initial pass dissipation including that AON load.
  No thermal/SOA/startup pass is inferred.
- The unclamped68.1k/10k OVP network reaches4.502V at35V and fails the4V OVP
  operating-pin rating. A locally biased LM4040CEM3-2.5/NOPB/BAS116H,115
  clamp has valid screened bias/current/resistor-power margins without using
  +3V3 as its sink. It gives3.447V from the full reference window plus the
  diode's25°C1mA VF maximum, or3.747V with an imposed1.2V cold VF envelope.
  **Cold VF and dynamic clamp/reference turn-on are not verified.**
- The retained-fault concept now arms from the full HEALTHY **level**, using
  an inverter and HC74 asynchronous set/clear. It does not depend on seeing a
  new PGOOD clock edge. Ideal cases show source-cycle, eFuse-fault and PGOOD-loss
  retention until request release, including admission when PGOOD is already
  high. Never-healthy startup remains explicitly unarmed and needs native
  eFuse latch response plus a firmware deadline. PRE/CLR races and brownout
  need physical timing verification.
- The provisional BSS138P helper's50pF maximum Ciss leaves no margin against
  TPS DRV's50pF specified load condition before routing. Keep helper selection
  open rather than claiming minimum DRV drive or fast reverse interruption.

## Sources and library evidence

Primary references: [TI TPS2663 SLVSE94G](https://www.ti.com/lit/ds/symlink/tps2663.pdf),
[TPS3700 SBVS187G](https://www.ti.com/lit/ds/symlink/tps3700.pdf),
[DDC0006A4214841/E](https://www.ti.com/lit/pdf/MPDS124I),
[HCS08 SCLS778D](https://www.ti.com/lit/ds/symlink/sn74hcs08.pdf),
[Nexperia HC74 Rev9](https://assets.nexperia.com/documents/data-sheet/74HC_HCT74.pdf),
[TI2G08 SCES198N](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf),
[TI1G14 SCES218AA](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf),
[LM4040 SNOS633N](https://www.ti.com/lit/ds/symlink/lm4040-n.pdf),
[BAS116H Rev3](https://assets.nexperia.com/documents/data-sheet/BAS116H.pdf),
[BSS138P Rev1](https://assets.nexperia.com/documents/data-sheet/BSS138P.pdf).
The Murata C0G exact source is
[GRM31C5C1H104JA01](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31C5C1H104JA01-01A.pdf).
TPS3839 and approved CSD18543Q3A package sources are retained in the prior
SWD/ADC and charger package checkpoints. Reference URLs are not an assertion
that later download bytes remain identical; `sources.json` records locally
available source hashes and actually inspected page identifiers.

Fresh saved Konnect query results cover the stock TPS26630, HC74, functional
quad/dual AND, OR, BSS helper and LM4040 maps and absent TPS3700. The quad AND
geometry is named74LS08; no exact HCS08 symbol exists. Compatible pin/function
reuse requires exact HCS MPN/description and a visible Schmitt-input annotation,
not TTL parts or custom graphics. Search/table absence and full pin counts are
reported distinctly. Query results do not substitute for disposable physical
part acceptance or rendered real-sheet inspection.

## Remaining boundary

Exact parts/lands, helper loading, clamp cold/dynamic response, integrated
startup/short/reverse cases, healthy essential-rail survival, unknown carrier
capacitance/inrush, thermal/vacuum behavior, complete off-state back-power,
permission firmware and RBF/discharge are still open. The raw35V ceiling,
130mΩ feed,1.8× hot FET resistance,0.2A startup load and cold capacitor/diode
envelopes are **imposed sensitivities**, not measured bounds. Do not silently
promote them to accepted device requirements.

Electrical calculations and ideal-state assertions were executed. Actual
rendered-sheet inspection: **not applicable to a new circuit here; no sheet
was authored**. Only the manufacturer TPS3700 pin/application and DDC
outline/land/stencil page images were inspected this turn. No fresh EPS ERC,
netlist, PCB synchronization, DRC, package construction or flight acceptance
is claimed by this packet.
