# EMBER — Open Work

Index of what needs attention and where. Updated 2026-09-02.

**What lives here:** the current front on each subsystem, plus anything that
doesn't belong to a checklist already in the docs — cross-cutting cleanups,
decisions still owed, and inconsistencies found but not yet resolved.

**What doesn't:** the step-by-step checklists. Those stay in the documents that
own them (`kicad_implementation_plan.md` has 38 open boxes, `tx_test_plan.md`
25, and so on). Duplicating them here guarantees the copy goes stale. This file
points at them.

---

## Communications — flight radio + ground station

The active front. Board is KiCad, project at
[`hardware/comms/kicad/`](hardware/comms/kicad/), plan at
[`hardware/comms/design/kicad_implementation_plan.md`](hardware/comms/design/kicad_implementation_plan.md).

Phase 0 (project setup) is complete. Next, in order:

- [ ] **Run DRC for the first time.** `min_clearance` was `0.0` until now, so
      the 511 already-routed segments have never been checked against
      anything. Expect violations — that is the point.
- [ ] **Re-route RF at 0.358 mm.** 194 segments currently sit at 0.34 mm,
      which is neither the old net-class width nor the new one.
      `transceiver.kicad_dru` will flag anything outside 0.35–0.37 mm.
- [ ] **Set the L1 ground zone clearance to 1.1 mm before pouring.** Keeps the
      RF traces microstrip rather than accidental coplanar — see the decision
      in [`rf_layout_guidelines.md`](hardware/comms/design/rf_layout_guidelines.md).
      Do *not* raise the `RF` net-class clearance to achieve this; it would
      make the filter and mixer pads unroutable.
- [ ] **Rename RF nets to `RF_*` / `LO_*`.** The wildcards are already in the
      net classes; renaming collapses 30 brittle auto-name patterns
      (`NetC24_1`, `NetIC1_3`) into two. Convention in
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

- [ ] **The schematic is not a hierarchy.** `eps.kicad_sch`,
      `Regulation.kicad_sch` and `Solar_Charger.kicad_sch` are three
      independent root sheets from the Altium import — the root has no
      `(sheet ...)` blocks, so opening the project shows only its own 17
      components and the other 59 are invisible to KiCad. 77 refdes across
      the three files vs 76 on the PCB. Fix in KiCad by placing sheet symbols
      on the root and pointing them at the two files; doing it by hand means
      rewriting instance-path UUIDs and risking annotation.
- [ ] **Run DRC.** `min_clearance` was `0.0` until now, with 413 segments
      already routed.
- [ ] Decide **1 oz vs 2 oz copper**. JLCPCB offers up to 4.5 oz on 2-layer;
      with no inner planes, 2 oz halves trace widths and doubles the heat
      spreader under the regulators. Widths currently assume 1 oz.

Open items (from [`hardware/eps/README.md`](hardware/eps/README.md)):

- [ ] Thermistor network finalisation
- [ ] Battery balancing / protection strategy
- [ ] Integrated EPS release package

Detailed checklists: [`altium_eps_schematic_guide.md`](hardware/eps/design/altium_eps_schematic_guide.md)
(22 open), [`altium_eps_layout_guide.md`](hardware/eps/design/altium_eps_layout_guide.md) (15 open),
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
- [ ] Fill in the **load profile** in [`analysis/power/README.md`](analysis/power/README.md) §3
      with measured subsystem currents. The whole budget still rests on a
      200 mW placeholder; the margin claim is 3.7× against that placeholder,
      not against real loads
- [ ] Link budget — [`analysis/link_budget/`](analysis/link_budget/) is an empty stub

---

## Cross-cutting

- [ ] **Subsystem count is inconsistent.** The architecture docs describe four
      subsystems (EPS, IHU, comms, payload); the PDR poster plan commits to
      five, folding the ground station into communications and splitting out a
      command/telemetry/debug interface. `system/` interface docs still
      describe the four-way split.
- [ ] **Five Altium board guides remain** while board design is KiCad-only:
      `altium_comms_schematic.md`, `altium_eps_schematic_guide.md`,
      `altium_eps_layout_guide.md`, `altium_ihu_schematic.md`,
      `altium_payload_schematic_guide.md`, `altium_payload_layout_guide.md`.
      The comms one is the pressing case, since that board is now KiCad.
- [ ] `net_naming.md` worked example still cites `BFR92A` as the tripler; the
      part is `2SC3356`
- [ ] **KiCad template project** — `jlcpcb_baseline.kicad_dru` exists, the
      template `.kicad_pro` with stackup, constraints and net classes does
      not. See [`kicad_jlcpcb_design_rules.md`](hardware/conventions/kicad_jlcpcb_design_rules.md) §13
- [ ] The `JLC04161H-7628` reference stackup file is no longer in the repo.
      Values are recorded in the design-rules doc §2; re-download the single
      file from `gsuberland/jlcpcb_autogenerated_stackups` if a future board
      wants it
- [ ] Two doc references point at files that do not exist yet and are expected
      to: `refdes_conventions.md`, `hardware/payload_compute/bringup/`

---

## Done recently

- Repository renamed and scrubbed of the predecessor project name
- Board CAD policy settled: KiCad tracked, Altium not
- Altium design-rules doc retired, content folded into the KiCad one
- Comms KiCad Phase 0 complete — stackup, constraints, net classes,
  custom rule, pre-defined sizes
- Power budget verified reproducible (`analysis/power/power_budget.py`)
