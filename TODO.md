# EMBER — Open Work

Updated 2026-09-02.

**What lives here:** the current front on each subsystem, plus anything that
doesn't belong to a checklist already in the docs.

**What doesn't:** step-by-step checklists. Those stay in the documents that
own them — the comms implementation plan has 38 open boxes, `tx_test_plan.md`
25, and so on. Duplicating them here guarantees the copy goes stale. This
file points at them.

---

## Where things are

| Path | What's in it |
|---|---|
| `hardware/<board>/design/` | The design record — schematic and layout guides, trade studies |
| `hardware/<board>/kicad/` | The KiCad project. Comms and EPS exist; IHU and payload don't yet |
| `hardware/<board>/bringup/` | Bench procedures and logs |
| `hardware/<board>/releases/` | What was actually fabbed — gerbers, BOM, CPL |
| `hardware/conventions/` | Project-wide: design rules, net naming, the shared `.kicad_dru` |
| `analysis/` | Orbit and access modelling, power budget, link budget |
| `system/` | Board-to-board interfaces, the CSKB pin map, protocols |
| `firmware/` | Housekeeping unit firmware (FreeRTOS on RP2040) |
| `docs/architecture/` | System-level scope and policy |

The payload **instrument** is a separate repository —
[koenig_wildfire](https://github.com/ngrabbs/koenig_wildfire). Optics, capture
software, calibration and flight results live there, not here.

Board CAD policy: **KiCad is tracked, Altium is not.** See the README.

---

## Read this first — the power budget may not close

The budget in [`analysis/power/`](analysis/power/) concludes the design closes
with **3.7× margin**. That rests on a **200 mW placeholder** for the entire
spacecraft. Against real subsystem numbers already in this repo:

| | |
|---|---|
| Worst-case orbit-average harvest | **736 mW** |
| Comms board alone, from its own schematic | 3.3 V × 100 mA + 5 V × 140 mA = **1.03 W** |
| Payload compute (Orin Nano) | **7 W / 15 W** modes |

The comms board by itself is ~1.4× the entire harvest. Duty cycling is
presumably what saves this, but the budget has no notion of modes — §4 has
the Nominal / RX-Only / Safe structure sitting empty.

**Until §3 is filled in with real per-mode loads and duty cycles, we do not
know whether the design closes.** It is also the number the PDR poster's
argument rests on. `power_budget.py` computes harvest and eclipse DOD
already; give it real loads and it answers the question immediately.

---

## Communications — flight radio + ground station

The active front. Board is KiCad, project at
[`hardware/comms/kicad/`](hardware/comms/kicad/), plan at
[`hardware/comms/design/kicad_implementation_plan.md`](hardware/comms/design/kicad_implementation_plan.md).

Phase 0 (project setup) is complete. **The next four are order-dependent** —
doing them out of order means routing the RF twice:

- [ ] **Run DRC for the first time.** `min_clearance` was `0.0` until now, so
      the 511 already-routed segments have never been checked against
      anything. Expect violations — that is the point.
- [ ] **Re-route RF at 0.358 mm.** 194 segments currently sit at 0.34 mm,
      which is neither the old net-class width nor the new one.
      `transceiver.kicad_dru` will flag anything outside 0.35–0.37 mm.
- [ ] **Set the L1 ground zone clearance to 1.1 mm before pouring** (currently 0.5 mm). Keeps the
      RF traces microstrip rather than accidental coplanar — see the decision
      in [`rf_layout_guidelines.md`](hardware/comms/design/rf_layout_guidelines.md).
      Do *not* raise the `RF` net-class clearance to achieve this; it would
      make the filter and mixer pads unroutable.
- [ ] **Rename RF nets to `RF_*` / `LO_*`.** The wildcards are already in the
      net classes; renaming collapses 22 brittle auto-name patterns
      (`NetC24_1`, `NetIC1_3`) into two. 22 remain. Convention in
      [`net_naming.md`](hardware/conventions/net_naming.md).

### RX front end — architecture change not yet made

The schematic is still the **rev 0.5 VHF-uplink design**: 2 m input BPF, CLK1
at 145.90 MHz. The board is moving to **all-UHF** (435 MHz uplink, shared
antenna) because the VHF filters proved too difficult to realise.

- [ ] Rebuild the RX front end per the implementation plan
- [ ] Update the five annotations that describe the old architecture — listed
      in [`hardware/comms/kicad/README.md`](hardware/comms/kicad/README.md)

Until then the RX sheet describes what is drawn, not where the board is going.

### Smaller items

- [ ] `Power.kicad_sch` D4 note: the part was corrected SA612 → PSA4-5043+,
      but the rationale "(both specified for supply down to 4.5V)" was written
      about the SA612. The PSA4-5043+ is resistor-biased and has no supply
      range in that sense — the real question is whether the bias resistor
      still delivers design current at 4.7 V.
- [ ] Tripler bias resistor refdes disagrees: schematic note says `R27`, the
      implementation plan says `R5`. One is stale.
- [ ] Four schematic-export PDFs are referenced before being produced
      (`Comms_schematic_v0.2.pdf`, `EPS_schematic_v0.1.pdf`,
      `FC_schematic_v0.1.pdf`, `satellite_comms_draft_v0.1.pdf`). Note
      `FC_schematic_v0.1.pdf` carries the pre-IHU "flight computer" name.

---

## Electrical Power System

Board is KiCad, project at [`hardware/eps/kicad/`](hardware/eps/kicad/).
**2-layer** — rev A was fabbed 2-layer and the docs, which said 4, have been
corrected.

- [ ] **No `fp-lib-table`.** `SamacSys:` and `Vault:` resolve to nothing,
      so KiCad cannot load either library. Harmless while the board is
      complete — every footprint is embedded in the `.kicad_pcb` — but
      adding any new part from those libraries will fail until they are
      configured. Blocking for the next board revision, not for this one.
- [ ] **Run DRC.** `min_clearance` was `0.0` until now, with 413 segments
      already routed.
- [ ] Decide **1 oz vs 2 oz copper**. JLCPCB offers up to 4.5 oz on 2-layer;
      with no inner planes, 2 oz halves trace widths and doubles the heat
      spreader under the regulators. Widths currently assume 1 oz.

Open items (from [`hardware/eps/README.md`](hardware/eps/README.md)):

- [ ] Thermistor network finalisation
- [ ] Battery balancing / protection strategy
- [ ] Integrated EPS release package

Detailed checklists: [`schematic_guide.md`](hardware/eps/design/schematic_guide.md)
(22 open), [`layout_guide.md`](hardware/eps/design/layout_guide.md) (15 open),
[`phase1_validation.md`](hardware/eps/bringup/phase1_validation.md).

---

## Command and Data Handling (IHU)

Open items (from [`hardware/ihu/README.md`](hardware/ihu/README.md)):

- [ ] Pin-map freeze
- [ ] Watchdog policy
- [ ] Safe-mode entry/exit behaviour

Firmware roadmap: [`firmware/ihu/README.md`](firmware/ihu/README.md) (19 open).
Schematic: [`altium_ihu_schematic.md`](hardware/ihu/design/altium_ihu_schematic.md) (30 open).

---

## Command, Telemetry and Debug Interface

The fifth subsystem on the poster, and **the thinnest in the repo.** What
exists today is four short stubs totalling ~120 lines:
[`system/protocols/command.md`](system/protocols/command.md) (39),
[`system/protocols/telemetry.md`](system/protocols/telemetry.md) (40),
[`system/integration/integration_plan.md`](system/integration/integration_plan.md) (20),
[`system/integration/system_tests.md`](system/integration/system_tests.md) (19).

- [ ] Define the command format — framing, addressing, acknowledgement
- [ ] Define the telemetry format and the beacon contents
- [ ] Decide what the operator-facing debug path is on the bench, and whether
      it is the same path as the flight command link
- [ ] Reconcile with the ground-station half of Communications — the poster
      folds the ground station into comms, so the boundary between "comms"
      and "command/telemetry" needs stating before both are worked in
      parallel

This is the most greenfield of the five. Good candidate to hand to whoever
wants to define something rather than inherit it.

---

## Payload

The instrument lives in its own repository —
[koenig_wildfire](https://github.com/ngrabbs/koenig_wildfire). Optics, capture
software, calibration and flight results are tracked there, not here.

This repo covers the carrier board. Open items in
[`payload_carrier_pinmap.md`](hardware/payload_compute/design/payload_carrier_pinmap.md) §10:

- [ ] Verify the Pi 15-pin CSI ribbon pinout against the official GS Camera
      schematic before fab
- [ ] Verify `CAM_GPIO0` (PWDN) drive voltage — 3.3 V vs 1.8 V decides whether
      a third buffer channel is needed
- [ ] Verify local trace widths for 3× camera 3V3 (rail budget is fine)
- [ ] Camera trigger harness mechanical design

---

## Analysis

- [ ] Confirm the 50 Ω width against JLCPCB's calculator after any stackup
      change — currently **0.358 mm**, verified 2026-09-02 (14.12 mil)
- [ ] Ground-station access modelling — contact duration, revisit, per-pass
      data volume. Checklist in [`analysis/orbit/README.md`](analysis/orbit/README.md) (15 open)
- [ ] **Fill in the load profile** — see the callout at the top of this file.
      This is the highest-value open item in the repo. §3 of
      [`analysis/power/README.md`](analysis/power/README.md) needs per-mode
      currents; §4 needs duty cycles for Nominal / RX-Only / Safe. Everything
      else in Analysis can wait behind it.
- [ ] Link budget — [`analysis/link_budget/`](analysis/link_budget/) is an empty stub

---

## Cross-cutting

- [ ] **Subsystem count is inconsistent.** The architecture docs describe four
      subsystems (EPS, IHU, comms, payload); the PDR poster plan commits to
      five, folding the ground station into communications and splitting out a
      command/telemetry/debug interface. `system/` interface docs still
      describe the four-way split.
- [ ] **Three Altium board guides remain**, all for boards not yet started:
      `altium_ihu_schematic.md`, `altium_payload_schematic_guide.md`,
      `altium_payload_layout_guide.md`. Nothing contradicts reality yet, so
      they can convert when those boards do. Every other doc a KiCad user
      traverses is converted — comms and EPS guides, `net_naming.md`, the
      design rules, RF layout, trace sizing.
      **When converting, expect to repoint 6 inbound links** from
      `cskb_pinmap.md`, `inhibit_and_deployment.md`,
      `component_datasheets.md`, `payload_carrier_pinmap.md` and
      `jetson_module_compatibility_report.md`. The comms rename needed 12
      across 11 files.
      The payload *layout* guide is the hardest of the three: ~40 hits, most
      of them Altium Impedance Profiles for the PCIe/USB/CSI diff pairs,
      which KiCad has no equivalent for. That section needs replacing, not
      translating — see how the comms stackup section was handled.
- [ ] `net_naming.md` worked example still cites `BFR92A` as the tripler; the
      part is `2SC3356`
- [ ] **KiCad template project** — `jlcpcb_baseline.kicad_dru` exists, the
      template `.kicad_pro` with stackup, constraints and net classes does
      not. See [`kicad_jlcpcb_design_rules.md`](hardware/conventions/kicad_jlcpcb_design_rules.md) §13
- [ ] The `JLC04161H-7628` reference stackup file is no longer in the repo.
      Values are recorded in the design-rules doc §2; re-download the single
      file from `gsuberland/jlcpcb_autogenerated_stackups` if a future board
      wants it
- [ ] Write `hardware/conventions/refdes_conventions.md`. [`net_naming.md`](hardware/conventions/net_naming.md)
      names it as the intended home for reference-designator convention and
      carries the interim IPC defaults until it exists.

---

## What's been done

Context for anyone arriving now — this is why the repo looks the way it does.

**Repository.** Renamed from the predecessor project and scrubbed of its name
(456 raw hits, of which 302 were `CSKB` — the Pumpkin CubeSat Kit Bus, an
industry standard, deliberately left alone). Went from 1.3 GB to ~120 MB by
dropping vendored CAD, regenerable simulation output, and 8 MB of embedded
uncompressed bitmaps. A pre-publication book that had been committed by
mistake was removed from history.

**Board CAD policy.** KiCad is tracked, Altium is not — KiCad's formats are
plain text and diff properly; Altium's are binary and its project trees dwarf
the design. All design guides for boards that exist have been converted to
KiCad wording.

**Comms board.** KiCad project set up end to end: stackup entered and verified
field-by-field against jlcpcb.com/impedance, constraints, net classes, custom
width rule, pre-defined sizes. The 50 Ω width is 0.358 mm, confirmed at
14.12 mil. Recorded a decision that was being made by accident — the RF traces
are microstrip, so the L1 ground pour must stay 1.1 mm back or the geometry
becomes coplanar and 0.358 mm stops being 50 Ω.

**EPS board.** Docs corrected from 4-layer to 2-layer — rev A gerbers confirm
2 is what was always fabbed. The schematic was three unlinked files from an
Altium import; it is now a proper hierarchy with all 77 footprints linked to
the PCB, 0 warnings and 0 errors. Recovering that took restoring an
annotation KiCad had silently renumbered.

**Analysis.** The power budget's harvest figures were verified reproducible —
`power_budget.py` recomputes them from the STK exports and matches the
published table exactly. Its *load* side is the open question at the top of
this file.

**Documentation.** Two duplicated design-rules docs merged into one; a stale
copy of the K-line physics primer removed after it was found to describe an
abandoned filter plan (762/766/770 nm rather than the current 750/770/780);
about 190 bare filenames converted to working links.
