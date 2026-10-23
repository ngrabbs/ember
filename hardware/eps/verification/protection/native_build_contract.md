# Native protection study build contract

**Historical initial-build contract.** The [current latch/source-short correction](../../design/rev_b_5v_latch_and_mosfet_survival.md) supersedes original C9/C112/C119 and rail-divider values, and adds R115/L2. Use its native endpoint verifier and BOM as current authority; this file retains the original build history.

Target repository/worktree: `/Users/nick/Documents/ChatGPT/EMBER/eps-pr-review`.
Policy: `/Users/nick/Documents/ChatGPT/EMBER/eps-pr-review/hardware/conventions/kicad_schematic_policy.md`.

The native build owner must read the entire target root AGENTS.md, policy, net-naming conventions, `hardware/eps/design/interfaces.md`, `rev_b_5v_recovery_design.md`, `rev_b_5v_recovery_fault_containment.md`, and the Konnect/schematic/library skills before work. All KiCad writes through Konnect. No PCB mutations. One mutation owner. This contract is for a **new isolated development study**, not integration into the converter or fabricated Rev A.

Create `hardware/eps/studies/recovery_protection/recovery_protection.kicad_pro` with a root ANSI B source-protection sheet and an attached ANSI B recovery-rail child. Prefer stock symbols/footprints; no new custom part construction is authorized. Existing approved Panasonic footprints in `hardware/eps/libraries/Ember_EPS_Recovery.pretty` may be reused with portable project tables. If a library symbol is missing, an existing generic symbol with the exact physical lead map is permitted; this does not authorize a new custom symbol. Keep missing/unverified footprint or MPN issues explicit and report them. Do not alter the existing recovery_5v project, libraries, controller, PCB or root analysis files.

## Circuit authority

`verification/protection/run_protection.py:deck()` is the circuit topology authority. It contains **test-fixture sources, behavioral tolerance injections and parasitic lumped models** that MUST NOT be drawn as real parts. Build the nominal hardware described below. Match the resulting electrical pin sets to a canonical netlist exported by KiCad; report electrical versus actual rendered-page evidence separately.

Use two LTC4364HDE controllers: source **LTC4364HDE-2#PBF**, rail **LTC4364HDE-1#PBF**. Stock `Power_Management:LTC4364HDE` exists and has the same 15 physical pins. Its pin 5 is called GATE; manufacturer HGATE is the same function. Stock footprint is `Package_DFN_QFN:DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm`; verify before assigning. Exact manufacturer DE lead mapping, component/top view:
1 OUT; 2 SENSE; 3 DGATE; 4 SOURCE; 5 HGATE; 6 VCC; 7 SHDN; 8 UV; 9 OV; 10 GND; 11 FLT open drain; 12 ENOUT open drain; 13 TMR; 14 FB; 15 EP/GND (connect GND).
Source: https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4364-1-4364-2.pdf Rev B.

All power MOSFETs: **IRLR2908TRPBF**, Infineon 80 V logic-level DPAK, physical 1 G / 2 D including tab / 3 S. Use a verified stock GDS symbol and DPAK footprint; there is no stock `Transistor_FET:IRLR2908`. Datasheet: https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlr2908-datasheet-en.pdf . Manufacturer package drawing can be downloaded with cache-busting query if an empty cached response is returned. Main source pass MOSFET: drain input, source COMMON; reverse-blocking MOSFET: drain SENSE, source COMMON. The two sources connect together and controller SOURCE pin observes COMMON. Source uses one per function; rail uses **three parallel FETs per function** for loss/headroom (the final simulator will include all three). Do not assume parallel sharing for fault qualification.

## Shared controller support (both pages, each has independent hardware)

- Pass gate node GH drives all pass FETs; reverse gate DG drives reverse FET(s) directly.
- HGATE output → 4.7 kΩ → GH. PNP **MMBT3906LT1G**: emitter GH, base HGATE, collector via 100 Ω to COMMON. Fast diode **1N4148W-7-F**: anode HGATE, cathode GH, protecting the PNP reverse BE junction. This emitter/base/collector mapping is deliberate. MMBT3906 pin 1 B / 2 E / 3 C; stock-symbol query must agree.
- Two **Littelfuse SMBJ8.5A** gate TVS diodes: cathode GH and DG respectively; anodes COMMON. Selected after the 12 V small-zener model exceeded VGS limits during a short. They clamp gate-to-source voltage, not the protected supply. SMB; verify stock pad mapping. Use a Littelfuse SMBJ60A at the source input to GND; the rail PIN clamp remains SMBJ36A. Add source damping: input → 1.0 ohm CRCW12061R00FKEAHP → four parallel GRM32ER72A225KA35L capacitors to GND (minimum 2u effective through60V). This DC-blocked snubber replaces the rejected source36VTVS, which wouldoverheat on sustained60V. The60VTVS isnot a blanket80Vclamp guarantee; boundedRCtransient verification isrequired.
- GH → gate-slew capacitor → 2.2 kΩ → GND. Capacitor sees gate-to-ground voltage: use **100 V C0G**, not 50 V.
- SENSE → 20 mΩ current shunt → OUT/protected output. Use **CRF1206-FZ-R020ELF** for the development identity, same as existing recovery shunt. Its pulse/cold qualification stays open; no accepted fault-energy claim for the shunt.
- OUT → FB-top resistor → FB → 1 kΩ → GND.
- TMR → timer capacitor → GND. No artificial behavioral voltage source or leakage current source from simulation belongs in the schematic.
- FLT → 47 kΩ → existing +3V3 (independent essential control-domain input within RBF). Local named fault signal only; MCU pin allocation not part of this build. ENOUT and SHDN intentionally left NC; no external pull-up on unused ENOUT.
- Required resistor metadata: signal dividers TNPW0603 family 0.1%, 25 ppm/K, P70 0.11 W (exact codes constructed with manufacturer rule; procurement confirmation remains open). Gate/bias/pull-down 100 Ω pulse resistor: **CRCW1206100RFKEAHP**, 1%, 0.75 W P70, 1206. Other gate resistors may use the same TNPW0603 family. Read the final selection record if present for exact MPN list. Do not fabricate missing MPNs; flag them for root resolution.

## Source sheet

- Input supply symbol **SOLAR_PERMITTED**, external source flag. This is already after physical RBF/deployment isolation. No RBF switch is implemented by this study.
- Input → main pass FET D; reverse FET D → SENSE → shunt → **VIN_CHG** output. Use real wires for this entire path.
- Bias: input → 100 Ω pulse resistor → **1N4148W-7-F** anode; diode cathode → controller VCC. Four **GRM32ER72A225KA35L** (2.2 µF, 100 V, X7R, 1210, 10%) in parallel from VCC to GND; this is a required ≥4.7 µF effective reservoir through 9–35 V, with actual DC-bias qualification open. The diode prevents a solar short from immediately draining controller bias. Primary Murata application BOM confirms identity: https://www.murata.com/products/productdata/8807039041566/pah-28-450.pdf p.15; exact device qualification remains open.
- UV divider VCC → 50 kΩ → UV → 10 kΩ → GND; 10 nF from UV to GND.
- Startup/retry OV divider input → 27.8 kΩ → OV → 1 kΩ → GND; 1 nF OV to GND. Nominal inhibit 36 V: **this is not the protected output ceiling**. The independent FB analog clamp protects VIN_CHG; OV prevents restarting into an unbounded high source. Hysteresis only typical: cold reconnect still requires qualification.
- FB divider top 25.8 kΩ / bottom 1 kΩ → nominal clamp 33.5 V.
- Gate-slew cap **1 nF**, 100 V C0G.
- Timer **100 nF**, C0G.
- Output bank: one **EEHZA1H680P**, 68 µF 50 V hybrid, approved Panasonic F footprint; three **CGA5L1X7R1H106K160AC**, 10 µF 50 V X7R 1206; plus existing-compatible 100 nF bypass if useful (log any added part). Nominal bank 98 µF; modeled lower bound 38 µF bulk + 10 µF ceramics, ESR 0.4 Ω bulk + 2 mΩ ceramic. These are development requirements, not measured guarantees.
- Source current is PV limited: study envelope ≤1 A, raw reservoir ≤1 µF, upstream harness ≤1 µH. None of those fixture elements are native parts in this circuit. Show concise development-constraints text.

## Rail sheet

- Input supply symbol **5V0_RECOVERY_REG**, external regulator source flag. Converter feedback and its existing output bank remain upstream, outside this study. Do not connect the output back to this input.
- Input → **XAL1510-472MED** nominal 4.7 µH fault-slew inductor → protected-stage input PIN. Effective inductance must remain ≥2.5 µH through modeled fault current; magnetic qualification open. Stock `Inductor_SMD:L_Coilcraft_XAL1510-472` exists, physical drawing: https://www.coilcraft.com/getmedia/cd1cef27-13f0-4568-8894-f7311475209b/xal1510.pdf . No PCB placement.
- PIN → four GRM32ER72A225KA35L 2.2 µF 100 V capacitors to GND (minimum effective total 2 µF requirement); **Littelfuse SMBJ36A**, cathode PIN/anode GND. TVS handles the inductor turn-off pulse, not a sustained 35-to-5 V clamp. SMB footprint; source: https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf .
- PIN → pass FET drains (three in parallel); their sources COMMON. Three reverse FET sources COMMON, drains SENSE; SENSE → shunt → existing shared **+5V**.
- PIN → 100 Ω pulse resistor → VCC; **GRM188R72A104KA35D**, 100 nF 100 V X7R 0603, VCC to GND.
- UV divider VCC → 20 kΩ → UV → 10 kΩ → GND. **MMBT3904LT1G** collector UV, emitter GND, base from local `REC5_RESET` through 47 kΩ with 100 kΩ base-emitter pull-down. Reset holds UV below 0.5 V for a deliberate 2 ms pulse; it cannot override hardware clamp/current limits. Independent EPS control input only; no new external stack pin.
- OV to GND (rail controller latches and has no automatic retry).
- FB top 3.20 kΩ / bottom 1 kΩ → nominal 5.25 V clamp. Accuracy below 12 V VCC is not guaranteed by cited datasheet row; explicitly mark development qualification open.
- Gate-slew cap **C1210C683J1GACTU**, 68 nF, 100 V C0G, 5%, 1210.
- Timer **220 pF**, C0G.
- Protected +5V bank: two **EEHZK1V101XP**, 100 µF 35 V hybrids using approved Panasonic D8 footprint; eight **CGA6P3X7R1E226M250AB**, 22 µF 25 V X7R 1210. Nominal bank 376 µF; require ≥112 µF bulk / ≤0.4 Ω cold ESR and ≥48 µF low-ESR ceramic total; actual qualification open. Additional external stack capacitance ≤100 µF. Start unavoidable load ≤0.5 A; full 2 A only after local hardware qualification and delay. Restore that state after faults.

C0G identities can use KEMET C1210C family 100 V / 5%: `C1210C102J1GACTU` 1 nF, `C1210C103J1GACTU` 10 nF, `C1210C104J1GACTU` 100 nF, `C1210C221J1GACTU` 220 pF. Codes constructed from manufacturer ordering table; procurement confirmation stays open. Datasheet https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf (20-Feb-2025), p.1 coding and pp.7–8 range matrix. Use verified stock generic capacitors and standard 1210 footprints, not new symbols.

## Acceptance and reporting

Make source symbols/native wiring electrically complete for the scope, with legitimate input power flags and no fake flags hiding mistakes. Query saved native geometry and required fields; export fresh netlist and CLI ERC. Classify any legitimate external-interface caveats explicitly. Render every actual B sheet and inspect full page and detail crops, fixing wire/text/overlap issues. S11 visible custom-field API limitation may remain; report it separately. All custom Panasonic parts remain review candidates as already approved; no new custom construction. Do not call the study a fabrication release or a qualified protection system. Send root the project paths, exact endpoint assertions, ERC counts, actual render paths and unresolved library/field issues.
