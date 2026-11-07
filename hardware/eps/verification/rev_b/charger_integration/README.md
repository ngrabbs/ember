# Integrated LTC4162 charger development checkpoint

2026-10-24, basis `8d03a7604b8e1cd6c25f8a6391ffdc8884f8577a`.
The unique B child `hardware/eps/rev_b/charger.kicad_sch` is attached to
`eps_rev_b.kicad_pro`. The root now contains **187 unique physical parts,
103 nets and 83 functional nets**. This closes the declared native charger
topology/metadata integration boundary, not full EPS power acceptance.
No real PCB synchronization or historical fixture/library mutation was made.
The isolated connector fixture was closed cleanly before the final hashes;
KiCad normalized only its new project file to meta version 3 defaults.
`fixture_close.json` records that expected normalization and closed-board state.

## Circuit and source boundaries

The saved, reference-wired PowerPath is `VIN_CHG -> Q300 -> R300 ->
SYS_PWR_PERMITTED`, with Q300 physical source pins 1/2/3 toward VIN_CHG and
drain 5 toward the input shunt. The battery path has Q301 drain 5 at SYS and
source pins 1/2/3 at the new agreed variable rail **BATT_PERMITTED**. Charging
flows from U300 SW25/26 through L300 and the separate R301 shunt to that rail.
Both 33 mΩ shunts are CRF1206-FZ-R033ELF; their distinct sense connections and
Kelvin-layout intent are retained. No wire directly joins the source rails.

U300 is LTC4162IUFD-LADM#TRPBF, using the accepted project symbol/land.
L300 is XAL6060-153MEC, 15 µH; require at least 7.52 µH at actual current and
temperature under the sizing assumptions. R302 is 63.4 kΩ. For 2S, CELLS1
connects to **5V0_CHG_INTVCC**, CELLS0 to **2V5_CHG_LOGIC**, and unused SYNC
to GND. The four 10 µF/50 V VOUT ceramics, two 10 µF/50 V battery ceramics,
10 µF INTVCC bypass, 4.7 µF/10 V logic bypass, three 100 nF/100 V bypasses and
22 nF/100 V bootstrap capacitor have exact MFG fields. Effective capacitance,
LC behavior, pulse/ripple, thermal and procurement acceptance remain open.
The prior [sizing](../../charging/power_stage/README.md) and
[sensor calculations](../../charging/README.md) retain those assumptions.

**SOLAR_PERMITTED and BATT_PERMITTED are explicit external, already-interlocked
development fixtures. Physical RBF and BMS hardware are still absent.** Every
charger battery sense/Kelvin connection is on BATT_PERMITTED, after that
boundary. Charger return is system GND; no raw BMS VSS is joined here.
The existing #FLG0400 retains its UUID/location but now models the actual
passive PowerPath output rather than an independent external SYS source.
#FLG0300 identifies the future BMS/RBF battery fixture only. #FLG0301 models
the real internal INTVCC diode/SW-bootstrap energy path. Existing source,
GND and +3V3 flags were not duplicated.

New SYS bypass raises the nominal shared converter/charger SYS bank from
102.6 to **142.7 µF**. VIN_CHG has **98.1 µF nominal** including its new
100 nF bypass. These are separate nodes, not an accepted combined startup
allocation. Bias/other networks and operating-state/tolerance bounds also
matter. The proposed RC input damper was not installed: footprint, combined
source impedance and actual charger-loop acceptance remain open.

**A 35 V failed-short charger path to the pack is not autonomously contained.**
This is called out on the charger page. Weak-solar/MPPT startup, BMS recovery,
source handover, default charge/sensor limits, minimum C/L, hot SOA, 3V3 OV,
CAN branch isolation, actual loads and physical fit remain system gates.

## MCU and external temperature interface

PB6/U100.30, PB7/.31 and PA8/.18 now join EPS_CHG_SCL, EPS_CHG_SDA and
EPS_CHG_ALERT_N respectively. R108/R109/R110 are their single 4.7 kΩ
TNPW06034K70BEEA pullups to the same essential +3V3 as DVCC. The old CAN
termination R106/R107 are unchanged. This does not allocate PB8 or change
stack ownership. Development bus rate is 100 kbit/s; approximately 251 pF is
the ideal 1 µs-rise RC budget. Actual timing/capacitance and full-temperature
logic margins are not accepted by this schematic.

R303 is the separate local 10 kΩ NTC bias. J300.1 carries THM_CHG_NTC;
J300.2 is dedicated quiet system return. A separate pack-mounted Semitec
103AT-2 is specified; no dummy sensor or BMS sensor-sharing path is present.
TP300/TP301/TP302 are bare PCB test features at NTCBIAS/NTC/return, not
procured components. Mounting, sensor limits and fault-response acceptance
remain in the temperature contract.

J300 is JST BM02B-GHS-TBT(LF)(SN), GHR-02V-S housing with
SSHL-002T-P0.2 contacts. `connector_physical_map.csv` joins the two contacts,
two symbol pins and **four raw footprint pads**, including two intentionally
repeated floating mechanical `MP` objects. JST's front mounting view is
rotated 180 degrees into the stock footprint, so pin 1 is left/bottom without
swapping identities. Stock signal lands are 0.6 x 1.7 mm versus the printed
0.6 x 1.35 ±0.1 mm reference; this longer-toe stock footprint is a development
choice, not an exact manufacturer land claim. US −25…85 °C versus updated
Japan −40…105 °C information is unresolved; **−40 °C screening is not passed**.
Assembly, mating/crimp/retention and flight qualification remain open.

## Electrical and package verification

From repository root run:

```
python3 hardware/eps/verification/rev_b/charger_integration/verify_charger.py
python3 hardware/eps/verification/rev_b/charger_integration/verify_connector.py
python3 hardware/eps/verification/rev_b/charger_integration/verify_annotations.py
```

`endpoint_contract.csv` specifies 19 complete added/expanded endpoint sets.
Every physical lead on U300 (29), both FETs including stacked sources, every
passive terminal, connector contact/testpoint and migrated MCU endpoint is
checked. Raw component-reference uniqueness is asserted before dictionaries;
all **511 ref.pin endpoints occur exactly once**. All 160 previous physical
UUIDs, values, footprints, library identities and fields are unchanged.
BOOST is solely U300.1/C311.1; BATFET gate solely U300.22/Q301.4.
The annotation gate additionally checks **359 total native references**,
including 172 power/flag symbols, their instance records and normalized power
numbers. All 304 pre-charger native symbols retain reference, UUID, position
and instance annotations. The newly introduced duplicate automatic #PWR001
was corrected only on the charger NTC return to #PWR0322, preserving its UUID
and connectivity. Fresh CLI export no longer emits the annotation warning;
physical-only XML uniqueness would not have established that result.
`verify_charger.py` also runs this annotation gate automatically.
The full root graph must equal the old graph plus the declared circuit,
replacing only the three formerly unconnected MCU singleton sets.

Fresh CLI ERC has **14 errors, zero warnings**: 13 still-unimplemented MCU
pins and the intentional same-IC **U300.25/U300.26 power-output pair**.
Both physical SW pins must be joined; their datasheet-derived electrical
types were preserved. No suppression or weaker pin types manufacture a pass.
The isolated connector fixture separately has two singleton nets and two
expected unconnected-pin errors, with no fake NCs or source flags.

All 83 functional nets match exactly one intended saved class, including the
new I2C class and meaningful internal power/switch/sense/gate names. Three
previous `/Controller/REC5_*` / `/Controller/SRC_FAULT` patterns remain
provably unmatched; the exposed API cannot delete them. Routing widths are
defaults, not accepted PCB constraints. The native-source hash manifest and
exact six-modified/four-added protected-path guard work before and after
commit. All earlier protected sources outside that scope and 83 previous
charger/BMS/PowerPath fixture/evidence files remain unchanged.

Geometry includes explicit junctions **and wire endpoints** when detecting
connected fourways. Charger/controller have 120/72 orthogonal 1.27 mm-grid
segments, zero joined fourways, and zero component/power/ground/flag pin
anchors on branches. Actual API pin queries include all symbols, including
the `#` power symbols. The 19/12 unconnected crossings are enumerated in
`geometry.json`, with no dot, endpoint or label anchor at a crossing.

## Actual rendered inspection and presentation limits

All eight full pages, the eight-page PDF and saved details were actually
opened and inspected. `charger_power.png`, `charger_ic.png`,
`charger_ntc.png`, `controller_charger_bus.png`, `controller_pullups.png`
and the root/buck/recovery/source current-note details show the saved design.
The independent connector fixture's symbol and actual saved-board copper/fab
renders were also inspected. Tiny fab pad-number strokes overlap body
graphics; exact raw saved geometry and live numeric maps corroborate them.

The bright-green CUSTOM review callout remains on the real charger page;
the approved alternative does not claim the symbol body itself is green.
Existing unrelated candidate markers and unfinished physical debug/stack
connectors remain open. S11 field typography/visibility/layout and S03 native
fourway ERC severity still lack exposed setters. Root/standalone page IDs
retain the known S04 metadata limitation.

The API has no free-text edit/delete operation. Old pre-charger notes were
therefore retained and **explicitly marked obsolete by prominent dated
superseding notes** on root, controller, buck, recovery and source pages.
Those five pages were re-rendered and inspected. This is an acknowledged
presentation limitation, not silent authority for an external SYS bypass.

`native_source_sha256.json`, `evidence_sha256.json`, `bom.csv`,
`new_reference_map.csv` and `changed_files.txt` identify the bounded handoff.
Ordinary preview/log/cache/PRL/lock/history files are not deliverables.
