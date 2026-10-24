# Managed payload VBAT feed — development candidate

2026-10-24. **Not integrated; electrical/package gates remain open.** This
contract targets two unique ANSI B children, `Payload Feed` and `Payload
Permission`, of `hardware/eps/rev_b/eps_rev_b.kicad_sch`. It preserves the
345-part ADC checkpoint and all existing physical interfaces. Do not interpret
the proposed reference map as saved hardware or a completed EPS.

Authority: [EPS plan](rev_b_plan.md), [canonical stack map](../../../system/interfaces/cskb_pinmap.md),
[current carrier pin plan](../../payload_compute/design/payload_carrier_pinmap.md),
[carrier budget](../../payload_compute/design/power_budget.md) and
[bootstrap/unclean-session contract](../../payload_compute/design/bootstrap_input_contract.md).
The [calculation packet](../verification/managed_payload/README.md) records
conditions and counterexamples. Read the root AGENTS.md, entire schematic
policy and net-naming conventions before native work. Konnect only; one owner.

## Boundary and operation

Input is existing `BATT_PERMITTED`, downstream of the still-unfinished hardware
RBF/pack-source boundary. Output is existing canonical `VBAT`, eventually both
H2.45/46 together. This branch powers carrier AON and main paths and the COMMS
voltage-monitor tap. It does not switch EPS/IHU essential supplies or implement
the missing RBF stage. Stack +3V3/+5V remain distinct. USB/bench alternates can
power the carrier separately; flight isolation must cover them too.

IHU retains H1.50 `PAYLOAD_EN`, default-low hard kill. EPS drives no IHU enable
or payload fault pin. EPS PB15, physical17, is board-local request output
`EPS_PAYLOAD_REQ`; PB8, physical32, is proposed board-local
`EPS_PAYLOAD_READY` input, replacing its unused/unwired optional stack-alert
reserve. No H1.49 driver or stack pin changes are authorized by that allocation.
PD2 remains reserved for unfinished RBF status.

Hold `PAYLOAD_EN` low during feed/AON startup. Admit main power only after
valid local carrier measurements and peer startup handshakes; EPS READY is not
an operating-system-ready or shutdown-complete acknowledgment. For normal off,
keep VBAT on through confirmed payload shutdown, then release the EPS request.
Serious faults may cut power immediately. Complete AON loss requires the
carrier's persistent unclean-session handling and fresh arm/recovery policy.

Permissions expire in **firmware**, with an independently running MCU IWDG and
boot/session freshness. This circuit is not an independent hardware lease
timer. MCU reset defaults PB15 off. Exact normal startup/shutdown deadlines,
CAN lease time, watchdog timeout and retry budget remain to be specified and
implemented. Hold the hardware request low at least1ms between attempts as a
development reset rule; validate actual timing before acceptance. An invalid
or never-healthy startup must expire, not run indefinitely.

## Power circuit and programming

U1400 **TPS26630RGER**, stock `Power_Management:TPS26630RGE`, uses active
limiting and MODE open for latch response. Follow TI SLVSE94G Figure9-2,
previously actually inspected: external reverse-blocking N-FET Q1400 source
faces BATT_PERMITTED, drain feeds IN1/2, gate connects B_GATE3. Q1401's source
faces BATT_PERMITTED, drain B_GATE, gate DRV4. Preserve the direction of both
body diodes. IN_SYS5 goes to BATT_PERMITTED; GND8/EP25 to GND; OUT17/18 to
VBAT. Internal pass node is wired locally, without inventing a new variable
rail name. NC19–24 remain unconnected. Stock PGOOD16 is generically typed output,
although the actual device is open-drain; retain that explicit library-model
limitation rather than silently editing its type. This is a proposed real branch, not a
logical two-pin connector standing in for protection.

Select the unchanged stock footprint
`Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm`
without embedded vias. The symbol's default ThermalVias variant has nine0.20mm
holes below the configured0.30mm drill minimum. Thermal vias must be designed
separately at PCB layout; omitting them from the footprint is not thermal
acceptance. The [stock control/protection checkpoint](../verification/managed_payload/control_packages/README.md)
verifies all68 leads across the eFuse, four control ICs and diode. Its generic
eFuse paste windows cover62.25% of EP area versus TI's78% example. Retain
stencil/voiding, generic-land and thermal qualification open.

Q1400 is CSD18543Q3A with its approved project manufacturer-pattern footprint.
Q1401 development selection is **Toshiba T2N7002AK,LM**, unchanged stock
`Transistor_FET:T2N7002AK`, G1/S2/D3 and SOT23. Its60V/±20V ratings and
17pF maximum Ciss at VDS10V/VGS0/25°C improve on the former BSS138P's50pF
test-point maximum. With imposed10pF routing capacitance the screen is27pF;
an imposed2× Ciss sensitivity gives44pF against TPS DRV's50pF listed load.
Neither factor bounds the full trajectory/PVT. Vth maximum2.1V at25°C does
not prove sink resistance/timing at minimum3V DRV over temperature. Keep
drive/loading and reverse interruption conditional. Manufacturer delivery
suffix/MOQ must be confirmed at purchase. The stock glyph simplifies the
internal gate protection; annotate it explicitly. The
[disposable fixture](../verification/managed_payload/helper_package/README.md)
verifies both helper/reference pin-pad maps and saved metadata, with actual
page/detail and board-layer inspection separate from ERC. Generic land and
courtyard acceptance remain open; Q1401 needs a full4.0×3.5mm reservation.

| Ref | Proposed connection/value |
| --- | --- |
| R1400 | ILIM10 to GND,4.02kΩ |
| R1401/R1402 | BATT_PERMITTED to UVLO6 to GND,41.2kΩ/10kΩ |
| R1403/R1404 | BATT_PERMITTED to OVP7 to GND,68.1kΩ/10kΩ, with clamp below |
| R1405/R1406 | VBAT to PGTH15 to GND,36.5kΩ/10kΩ |
| R1407 | IMON13 to GND,18kΩ; no ADC allocation or current telemetry claim |
| R1408/R1409 | SWITCH_EN to SHDN12,1kΩ series;20kΩ SHDN to GND |
| R1410/R1411 | FLT14/PGOOD16 pullups, each10kΩ to essential+3V3 |
| C1400 | BATT_PERMITTED to GND,2.2µF/100V X7R1210, GRM32ER72A225KA35L |
| C1401 | IN1/2 local bypass to GND,100nF/100V X7R0603, GRM188R72A104KA35D |
| C1402/C1403 | VBAT to GND, same2.2µF and100nF parts as input |
| C1404 | dVdT9 to GND,100nF/50V C0G1206, GRM31C5C1H104JA01L |
| C1405 | SHDN12 to GND,1nF/50V/5% C0G0603, TDK CGA3E2C0G1H102J080AA |
| C1406 | OVP7 to GND, same TDK1nF part and approved project footprint as C1405 |

The [37-passive sourcing manifest](../verification/managed_payload/passive_selection/README.md)
selects all23 resistor and14 capacitor MPNs. R1424 uses0805 for1MΩ; the
precision0603 range stops at332kΩ. C1405/C1406 use the approved, separately
[verified TDK footprint](../verification/managed_payload/tdk_filter_package/README.md),
with project review/assembly and native S11 field-display limitations retained.
Resistor electrical screen assumes0.1% initial plus25ppm/°C over65K,
independent corners. Select and verify exact MPNs, package/power/voltage/TCR
and S11 fields before placement. Nominal values alone do not release parts.
The100nF C0G's published30ppm data over25..125°C does not establish the cold
combined bound; calculation uses a labelled sensitivity.

The9.4V OVP divider alone fails the imposed35V source case:4.502V on OVP,
above its4V operating rating. Proposed clamp: U1401
**LM4040CEM3-2.5/NOPB**, K1 local2.5V reference/A2 GND/NC3 floating; R1412
10kΩ from BATT_PERMITTED to K; D1400 **BAS116H,115**, A2=OVP, K1=reference.
The C/E ordering choice provides the extended temperature grade; the screen
uses its full−40..125°C reference window. Use stock
`Reference_Voltage:LM4040DBZ-2.5`/SOT23 and `Device:D_Small`/
`Diode_SMD:D_SOD-123F` after exact package checks. This requires no newly
authored symbol or changed pin map. R1412 requires at least0.25W under the
specified derating calculation; select TNPW121010K0BEEA,0.330W P70 General,
1210 to meet the configured60% power limit at85°C under a full35V screen.
The earlier1206 option misses that conservative utilization target. Bias is after RBF and independent of+3V3;
nominal8.4V source cost is4.956mW. Draw these local connections with wires,
not detached label-only parts. If a power port is used, its fixed-rail Value
is `2V5_PAYLOAD_CLAMP`. Do not join it to an essential supply.

The clamp passes the stated DC-current/power arithmetic and a labelled1.2V
cold-diode sensitivity. A [24-case nominal subcircuit study](../verification/managed_payload/clamp_transient/README.md)
uses TI's unchanged unencrypted reference macro with imposed diode/parasitic
envelopes. Adding C1406 lowers the maximum simulated OVP from3.90601V to
3.74600V. Cold cases also show millivolt negative OVP excursions: only12/24
meet the complete0..4V operating window, while24/24 meet the imposed absolute
window. With1nF, simulated first threshold crossings after a1ns source edge
are0.233..0.363µs warm and2.634..2.767µs cold; eFuse/output delay is absent.
The macro's reference node peaks5.008V. These results support the filter as a
development direction, not pin-rating/dynamic/PVT acceptance. **Cold VF,
production reference startup, coupled cutoff and MOSFET survival remain open.**
Source35V itself is an imposed study ceiling, not an accepted flight bound.

The4.02k programming screen gives4.174–4.828A only from TI's listed
VIN−VOUT=1V test window and resistor scaling; it does not guarantee the limit at
arbitrary dropout or bound the initial short pulse. At the conservative
source-UV falling corner6.889V,25.518W input allocation and imposed130mΩ total
path, the carrier sees6.368V/4.007A. The current-margin screen fails before
the6V floor at sufficiently large resistance; maximum calculated resistance
for that current screen is185.8mΩ. Reserve130mΩ as a development budget,
including FETs, both supply/return paths, contacts, PCB and harness. The1.8×
hot external-FET resistance is a sensitivity, not a proven hot maximum.

Proposed source UV nominal rise7.16V, fall7.062V; corner windows7.049–7.272V
and6.889–7.200V. This intentionally sheds nonessential payload before the
essential recovery supply's5V pack floor. It does not move a BMS cell threshold.
Source OV nominal rise9.44V. Actual transient cutoff thresholds/delays, weakest
carrier/COMMS input stress and coordinated pin ratings still need acceptance.

No quick-discharge device is selected. The1mF/5mF imposed carrier cases store
about35mJ/176mJ at8.4V before other energy paths. Source disconnection alone
does not prove prompt depowering. Resolve RBF residual energy, alternate-source
feeds and discharge stress without dumping an independently powered carrier
into an unqualified bleeder.

## Permission and retained fault logic

All control ICs use essential+3V3 with individual100nF local bypasses. Proposed
U1410 TPS3839K33DBZR is a **new dedicated qualifier**, with its already
verified stock map VDD3/GND1/RESET2; do not load/migrate ADC or SWD qualifiers.
Output is local SUPPLY_OK,10kΩ pulldown. Supervisor timing/brownout limits
remain the same open qualification class as those interfaces.

U1411 **SN74HCS08PWR** reuses the stock `74xx:74LS08` functional AND geometry:
all14 physical pin functions/types match; set actual HCS MPN/Value/description
and explicitly annotate **Schmitt inputs — HCS part required**. This is stock
geometry reuse, not a newly authored symbol, and does not permit fitting an LS
or HC part instead. U1412 is **74HC74PW,118**, stock `74xx:74HC74`.
U1413 is **SN74LVC2G08DCUR**, stock `74xGxx:74LVC2G08`; U1414
**SN74LVC1G32DBVR**, stock1G32; U1416 **SN74LVC1G14DBVR**, stock1G14.
Verify exact selected package lands, source fields and physical maps before
placement; incompatible ordering suffixes are not substitutions.
The linked stock checkpoint now checks U1411/U1412/U1413/U1414 contact maps
with all multi-unit power pins, corrected saved field presentation and actual
page/detail inspection. Use full placement reservations: HCS08/HC74
7.70×5.90mm,2G08 4.56×2.90mm,1G32 4.76×4.05mm and eFuse5.26×5.26mm.
These supplement stock notched courtyards for maximum body/flash dimensions;
they are not edited vendor footprints or assembly approval.

U1415 **TPS3700DDCR**, construction subject to the
[pending exact rules](rev_b_payload_tps3700_library_rules.md), monitors the raw
BATT_PERMITTED input independently of U1400's supply. VDD5=+3V3/GND2=GND;
UV divider169kΩ/10kΩ to INA+3; OV divider226kΩ/10kΩ to INB−4. Join OD outputs
OUTA1/OUTB6 to RAW_OK with one10kΩ+3V3 pullup. Independent dividers replace
the reference application's shared three-resistor ladder; thresholds are
calculated with the actual input currents. The monitor's450µs maximum
power-up delay is distinct from its only-typical source-fault delays. Do not
claim every brief input interruption is detected.

Local logic equations:

```text
REQ       = PB15_REQUEST & SUPPLY_OK
SRC_REQ   = REQ & RAW_OK
FAULT_OK  = RAW_OK & EFUSE_FLT_N
HEALTHY   = FAULT_OK & EFUSE_PGOOD
ARM_PRE_N = NOT HEALTHY
FAULT_PRE_N = HEALTHY | ARM_BAR
SWITCH_EN = SRC_REQ & FAULT_BAR
READY     = SWITCH_EN & HEALTHY
```

U1411 gates:1/2→3=REQ,4/5→6=SRC_REQ,9/10→8=FAULT_OK,
12/13→11=HEALTHY;7GND/14VCC. U1413:1/2→7=SWITCH_EN,
5/6→3=READY;4GND/8VCC. U1414:1/2→4=FAULT_PRE_N;3GND/5VCC.
U1416:2→4=ARM_PRE_N;3GND/5VCC;NC1 floating.

U1412 both halves are **asynchronous level memory**, with D/CLK grounded;
their unused Q outputs are explicit no-connects. ARM half: PRE4=ARM_PRE_N,
CLR1=REQ,D2/CLK3=GND,Q5NC,Qbar6=ARM_BAR. FAULT half:
PRE10=FAULT_PRE_N,CLR13=REQ,D12/CLK11=GND,Q9NC,Qbar8=FAULT_BAR.
Power7GND/14+3V3. This avoids an edge-only arming hole when PGOOD is already
high on a new request. First fully healthy state arms retention; subsequent
RAW_OK, FLT_N or PGOOD loss sets the retained fault. Clearing the source/eFuse
fault alone cannot re-enable the branch while REQ remains asserted.

At REQ low, EN is masked and memory is cleared. Both-low PRE/CLR can briefly
occur and HC74 Q/Qbar then both go high; do not describe that as a valid stored
state or prove timing from a Boolean abstraction. Verify all release races,
minimum pulse widths, propagation/skew, recovery/removal and supply collapse.
The1kΩ/1nF SHDN filter is a proposed glitch filter, not proof of arbitrary-race
suppression. A startup that never becomes fully HEALTHY remains unarmed:
native MODE latch behavior and the firmware startup deadline must cover it.

PB15 gets10kΩ pulldown and1kΩ series into local logic. READY reaches PB8 via
1kΩ with1MΩ MCU-side pulldown. Reserve R1420–R1429 for these five resistors,
RAW_OK pullup and four source-window resistors; C1410–C1416 for seven local
100nF bypasses. Proposed power page25parts and control page24parts,49 total;
refs must be queried unused before work. No fictitious manufacturer MPNs for
test pads or new logical connectors are introduced.

## Drawing and verification boundary

Draw left-to-right power flow, gate/helper wiring and dividers together on
Payload Feed; keep qualifier/window detector, local gates and both memories
together on Payload Permission. Use real wires, downward grounds and upward
power symbols; separate T-junctions. Globals only for true page crossings:
EPS_PAYLOAD_REQ, EPS_PAYLOAD_READY, EPS_PAYLOAD_SWITCH_EN,
EPS_PAYLOAD_FLT_N and EPS_PAYLOAD_PG. Same-page signals remain local. Preserve
all accepted rail names and ground domains. Set actual relevant POWER and
digital/analog net classes by exact exported names without adding unused
classes or weakening ERC. Do not modify other boards, firmware or real PCB.

Before integration: resolve helper drive/loading, clamp transient/cold
premises, exact passive metadata and complete package verification; obtain
the TPS3700 construction approval and disposable package acceptance. Freeze
the current native state, then delegate the complete two-sheet build under
the Konnect skill with one mutation owner. Preserve every old physical UUID,
metadata field, hierarchy and unrelated setting. Query transformed coordinates
before wiring, read all saved instance fields back, and verify full-root CLI
netlist/ERC/classes with actual page/detail renders as separate gates.

Fresh exported source-capacitor inventory must then include the additional
raw2.2µF/100nF and conditional output2.2µF/100nF, clamp bias and all seven
control bypasses. Recompute RBF/source energy and retained power at that real
graph; historical packets stay frozen. Update full footprint inventory and
only then assess real placement against the confirmed mechanical sources.
No circuit source or PCB was changed by this contract.
