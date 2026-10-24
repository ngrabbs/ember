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
  The [24-case transient sensitivity](clamp_transient/README.md) supports a1nF OVP filter; exact cold VF and production reference startup remain unverified.
- The retained-fault concept now arms from the full HEALTHY **level**, using
  an inverter and HC74 asynchronous set/clear. It does not depend on seeing a
  new PGOOD clock edge. Ideal cases show source-cycle, eFuse-fault and PGOOD-loss
  retention until request release, including admission when PGOOD is already
  high. Never-healthy startup remains explicitly unarmed and needs native
  eFuse latch response plus a firmware deadline. PRE/CLR races and brownout
  need physical timing verification.
- Selected T2N7002AK,LM as the development helper:17pF maximum Ciss at the
  specified25°C test point, plus imposed10pF routing, gives27pF. An imposed
  doubling gives44pF against the driver's listed50pF load. These are conditional
  margins, not a full-temperature gate trajectory bound. The
  [stock package fixture](helper_package/README.md) verifies both helper and
  reference pin-pad maps, with electrical/structural and rendered evidence
  reported separately; assembly/courtyard acceptance remains open.
- The24 completed LM4040 nominal macro cases give3.90601V maximum OVP without
  extra filtering and3.74600V with1nF. All stay within the imposed absolute
  window, but cold cases dip millivolts below0V;12/24 meet the full operating
  window. This is a reference subcircuit with behavioral diode assumptions,
  not TPS2663 cutoff, cold/PVT or MOSFET survival acceptance.

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
[Toshiba T2N7002AK 2026-04-14](https://toshiba.semicon-storage.com/info/docget.jsp?did=29712&prodName=T2N7002AK).
The Murata C0G exact source is
[GRM31C5C1H104JA01](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31C5C1H104JA01-01A.pdf).
TPS3839 and approved CSD18543Q3A package sources are retained in the prior
SWD/ADC and charger package checkpoints. Reference URLs are not an assertion
that later download bytes remain identical; `sources.json` records locally
available source hashes and actually inspected page identifiers.

Fresh saved Konnect query results cover the stock TPS26630, HC74, functional
quad/dual AND, OR, historical BSS helper and LM4040 maps and absent TPS3700. The quad AND
geometry is named74LS08; no exact HCS08 symbol exists. Compatible pin/function
reuse requires exact HCS MPN/description and a visible Schmitt-input annotation,
not TTL parts or custom graphics. Search/table absence and full pin counts are
reported distinctly. Query results do not substitute for disposable physical
part acceptance or rendered real-sheet inspection.

The [37-passive manifest](passive_selection/README.md) selects all23 resistor
and14 capacitor MPNs, corrects R1424 to0805 and R1412 to1210, and checks the
configured60% derated resistor-power target. The two TDK filter capacitors now
have an approved [project footprint with disposable verification](tdk_filter_package/README.md);
full native S11 field presentation and assembly qualification remain open.

## Remaining boundary

The [six-part stock control/protection checkpoint](control_packages/README.md)
now verifies68 physical leads/72 pad objects and corrects fixture field
collisions through a discovered existing local Konnect MCP presentation tool.
The eFuse selects the stock no-via footprint because its default0.20mm holes
miss the configured0.30mm minimum. Generic lands,62.25% EP paste coverage,
thermal vias and full placement reservations remain assembly/layout gates.
No real EPS circuit changed. Prior S11 limitations describe earlier checkpoints;
the newly verified field-position route can support subsequent repairs.

Exact parts/lands, helper loading, clamp cold/dynamic response, integrated
startup/short/reverse cases, healthy essential-rail survival, unknown carrier
capacitance/inrush, thermal/vacuum behavior, complete off-state back-power,
permission firmware and RBF/discharge are still open. The raw35V ceiling,
130mΩ feed,1.8× hot FET resistance,0.2A startup load and cold capacitor/diode
envelopes are **imposed sensitivities**, not measured bounds. Do not silently
promote them to accepted device requirements.

Electrical calculations and ideal-state assertions were executed. The added
nominal clamp simulations and two-part stock package fixture have their own
scoped evidence above. Actual new functional circuit rendered-sheet inspection
remains **not applicable: no real EPS sheet was authored**. The fixture's page,
symbol details and five board layers were actually inspected. No fresh real-EPS
ERC, netlist, PCB synchronization, DRC or flight acceptance is claimed.
