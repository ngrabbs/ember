# EPS Phase 1 Validation Plan

## Scope

Phase 1 validates EPS source, charging, and regulation behavior at bench level
before full subsystem integration. This plan targets the rev A board:
LTC4162-LAD MPPT charger feeding two TPS62933F single-channel buck regulators
(3.3 V and 5.0 V rails) from the PowerPath output, with a 4S panel configuration
and 2S2P LG MJ1 battery.

## Companion Documents

When a test fails, switch to the diagnosis docs:

- `hardware/eps/bringup/tps62933_ltspice_debug_guide.md` — TPS62933F feedback
  network theory, LTSpice behavioral model, per-pin scope expectations, and a
  fault tree for "regulator has no output."
- `hardware/eps/design/altium_eps_schematic_guide.md` — schematic source of
  truth (Sheet 1 = LTC4162, Sheet 2 = TPS62933F regulators).
- `analysis/power/` — orbital power balance with the locked
  4S panel configuration (Vmp ≈ 22.3 V, Voc ≈ 27.6 V).

## Provisional Numeric Criteria (Rev A)

These limits are intentionally conservative placeholders so testing can proceed
before final subsystem current budgets are locked.

- `5V_RAIL` steady-state: 4.85 V to 5.15 V for 0.1 A to 2.0 A load
- `3V3_RAIL` steady-state: 3.20 V to 3.40 V for 0.1 A to 2.0 A load
- Ripple target (20 MHz bandwidth limit):
  - 5 V rail: <= 100 mVpp
  - 3.3 V rail: <= 75 mVpp
- Dynamic step response target (25% to 75% load step):
  - Peak droop/overshoot <= +/-5% of nominal rail
  - Recovery to within +/-2% in <= 2 ms
- Thermal screening target:
  - < 40 C rise above ambient on hottest observed component during 10-minute
    hold at 2.0 A per rail equivalent load case

---

## Test 0: Pre-Bring-Up Verification (Do This First)

These checks are cheap, catch most gross errors, and should be done **before**
applying power for the first time on a fresh board.

### Procedure

1. Verify `JP_RBF` (Remove-Before-Flight) jumper is **not installed**.
   Installing it forces `BUCK_EN` to GND and disables both regulators.
2. Continuity check: `VOUT_PP` to GND should read open (no short).
3. Continuity check: `+3V3` to GND should read open.
4. Continuity check: `+5V` to GND should read open.
5. Confirm `Vref` value from your downloaded copy of the TPS62933F datasheet
   (Electrical Characteristics → Internal voltage reference). Record the value
   below — this determines what the rails will regulate to.

### Pre-Bring-Up Measurements

| Check | Expected | Measured / Observed | Pass/Fail |
|---|---|---|---|
| `JP_RBF` removed? | Removed | removed | pass |
| `VOUT_PP` ↔ GND continuity | Open | open | pass |
| `+3V3` ↔ GND continuity | Open | open | pass |
| `+5V` ↔ GND continuity | Open | open | pass |
| TPS62933F Vref (datasheet) | 0.6 V or 0.8 V | 0.8 V | pass |

### Predicted Rail Voltages from Vref (cross-check before powering up)

With BOM resistors R9=31.6 kΩ / R10=10 kΩ (3 V3 rail) and R13=52.3 kΩ /
R14=10 kΩ (5 V rail):

| Vref (datasheet) | "3 V3" rail predicted | "5 V" rail predicted | Action if mismatched |
|---|---|---|---|
| 0.6 V | 2.50 V | 3.74 V | Resistor swap needed: R9 → 45.3 kΩ, R13 → 73.2 kΩ |
| 0.8 V | 3.33 V | 4.98 V | Dividers correct, no action |

**Predicted "3 V3" rail given my Vref:** 3.20-3.40V
**Predicted "5 V" rail given my Vref:** 4.86-5.15V

### Notes / Observations

```
board looks good to me so far, no missing components


```

---

## Test 1: LTC4162 MPPT Charger Bring-Up

### Objective

- Validate solar-to-battery charging behavior with 4S panel architecture
- Verify MPPT response under changing input conditions
- Verify charger telemetry observability via I2C

### Pre-Conditions

- Test 0 passed
- A representative 2S2P LG MJ1 battery pack ready at safe SOC (3.7-3.9 V/cell)
- Bench supply or 4S panel string available; LTC4162 input range is
  4.5-35 V, so you can simulate the full range with a bench supply

### Procedure

1. Connect 2S2P battery pack to BAT terminals (observe polarity)
2. Connect 4S panel input (or bench supply set to ~22 V / 1 A current limit)
   to VIN_SOLAR
3. Sweep input voltage from 6 V → 27 V in steps; observe MPPT settling
4. Log battery voltage, charge current, and input power at each step
5. Read I2C telemetry registers via the controller (or a USB-I2C bridge)
6. Remove input source and observe PowerPath transition (load should run
   from battery)
7. Re-apply input and observe transition back to charge mode

### Measurements

Record at minimum three input conditions: open-circuit panel (Voc ≈ 27 V),
mid-MPP (~22 V), and below-MPP (~12 V).

| Condition | Vin (V) | Vbat (V) | Icharge (mA) | Vout_pp (V) | I2C State Reg | Notes |
|---|---|---|---|---|---|---|
| Open-circuit panel | _____ | _____ | _____ | _____ | _____ | _____ |
| At MPP (~22 V) | _____ | _____ | _____ | _____ | _____ | _____ |
| Below MPP (~12 V) | _____ | _____ | _____ | _____ | _____ | _____ |
| Source removed | n/a | _____ | n/a | _____ | _____ | PowerPath → battery |
| Source re-applied | _____ | _____ | _____ | _____ | _____ | PowerPath → solar |

### Initial Acceptance Criteria

- Charger enters a valid charge state (`CC_CV_CHARGE` or `ABSORB`) and
  transitions are observable via I2C
- No unexpected oscillation or dropout in the 6-27 V input range
- PowerPath transitions cleanly when input source is removed and restored
- `VOUT_PP` stays within 6-18 V across the operating envelope

### Status / Diagnostic Notes

> Boards back from fab. Charger was working on an earlier build but is not
> behaving as of __________ (date). Likely follow-on work: build a
> charger-side fault tree mirroring the regulator one in
> `tps62933_ltspice_debug_guide.md`.

```
[Observations from this run — what failed, scope captures, I2C reads, etc.]




```

---

## Test 2: TPS62933F Buck Regulator Validation (3.3 V and 5 V Rails)

### Objective

- Validate 5 V and 3.3 V rail stability from `VOUT_PP`
- Confirm feedback divider produces correct rail voltage given the actual
  Vref of the part
- Characterize load regulation, ripple, and thermal behavior

### Pre-Conditions

- Test 0 passed and Vref-vs-divider math verified
- `VOUT_PP` stable (either from Test 1 charger output or directly from a
  bench supply at 12 V via the test point on Sheet 3)

### Procedure

1. Drive `VOUT_PP` from a bench supply at 12 V, current limit 1 A initially
2. Observe both rails come up — record startup behavior
3. Measure DMM and scope values at every regulator pin per the table below
   *before* applying load (no-load DC characterization)
4. Apply electronic load to 3.3 V rail: 0.5 A → 1 A → 2 A, settle 30 s each
5. Apply electronic load to 5 V rail: 0.5 A → 1 A → 2 A, settle 30 s each
6. Capture ripple waveform on each rail at 2 A load (20 MHz BW limit)
7. Hold at 2 A on both rails for 10 min, monitor regulator case temp

### Per-Pin DC Measurements (No-Load Startup)

Fill in for both U2 (3 V3) and U3 (5 V). With `VOUT_PP` = 12 V.

#### U2 (3.3 V rail)

| Pin | Name | Expected | Measured | Pass/Fail |
|---|---|---|---|---|
| 3 | VIN | 12 V | _____ | _____ |
| 2 | EN | 12 × 61.9 / (226+61.9) = 2.58 V | _____ | _____ |
| 7 | SS | Ramp 0 → Vref over ~5 ms, then steady at Vref | _____ | _____ |
| 5 | SW | 500 kHz square, 0 ↔ ~Vin (scope) | _____ | _____ |
| 8 | FB | Vref (your datasheet value) | _____ | _____ |
| - | VOUT (+3V3) | Vref × (1 + 31.6 / 10) | _____ | _____ |

#### U3 (5 V rail)

| Pin | Name | Expected | Measured | Pass/Fail |
|---|---|---|---|---|
| 3 | VIN | 12 V | _____ | _____ |
| 2 | EN | 2.58 V | _____ | _____ |
| 7 | SS | Ramp then steady at Vref | _____ | _____ |
| 5 | SW | 500 kHz square (scope) | _____ | _____ |
| 8 | FB | Vref | _____ | _____ |
| - | VOUT (+5V) | Vref × (1 + 52.3 / 10) | _____ | _____ |

> If any of the above is off, jump to the fault tree in
> `tps62933_ltspice_debug_guide.md` Section 7 before continuing.

### Load Regulation

Measure rail voltage at each load point with `VOUT_PP` = 12 V.

| Rail | 0.1 A | 0.5 A | 1.0 A | 2.0 A | Min | Max | Pass (within ±?) |
|---|---|---|---|---|---|---|---|
| +3V3 | _____ | _____ | _____ | _____ | _____ | _____ | _____ |
| +5V  | _____ | _____ | _____ | _____ | _____ | _____ | _____ |

### Ripple (20 MHz BW limit, 2 A load)

| Rail | Ripple (mVpp) | Target | Pass/Fail |
|---|---|---|---|
| +3V3 | _____ | ≤ 75 mVpp | _____ |
| +5V  | _____ | ≤ 100 mVpp | _____ |

### Thermal (10-min hold at 2 A per rail)

| Component | Ambient (°C) | Final (°C) | Rise (°C) | Pass (≤40 °C rise) |
|---|---|---|---|---|
| U2 (3 V3 IC) | _____ | _____ | _____ | _____ |
| U3 (5 V IC) | _____ | _____ | _____ | _____ |
| L20 (3 V3 inductor) | _____ | _____ | _____ | _____ |
| L21 (5 V inductor) | _____ | _____ | _____ | _____ |

### Initial Acceptance Criteria

- Both rails come up within Test 0 predicted values (FB = Vref, VOUT matches
  the divider math)
- Steady-state voltage within provisional limits (±1.5% on 5 V, ±3% on 3.3 V)
- Ripple within provisional targets at 2 A
- Thermal rise within provisional screening target
- Transient response meets provisional step-response target (covered in Test 4)

### Observations / Notes

```
[What you saw — startup behavior, anything unexpected, scope captures saved
 to `hardware/eps/bringup/screenshots/`]




```

---

## Test 3: SM141K10TF Panel Characterization (4S Configuration)

### Objective

- Verify measured panel behavior matches the orbital power-budget assumptions
- Confirm 4S series string presents valid input to the LTC4162

### Reference (Locked Configuration)

- Module: IXYS SM141K10TF (10 internal cells in series, 25% efficiency)
- Per face: 4 modules in series
- Faces: 4 in parallel
- Module specs (datasheet AM1.5): Voc=6.91 V, Isc=58.6 mA, Vmp=5.58 V,
  Imp=55.1 mA, Pmp=307 mW
- Face Vmp (4S): 22.32 V
- Face Voc (4S): 27.64 V
- Face Pmp (AM1.5): 1.23 W
- Face Pmp (AM0, on-orbit): ~1.71 W

### Procedure

1. Build a single-face 4S string (4 modules in series)
2. Under sun lamp or natural sunlight, measure `Voc` (open-circuit) and
   `Isc` (short-circuit through low-side ammeter)
3. Sweep an electronic load (or resistive decade) across the I-V curve
4. Identify the knee — measure `Vmp` and `Imp` at the maximum-power point
5. Connect the 4S string to the LTC4162 VIN_SOLAR input and observe
   startup, MPPT settling, and `Vout_pp` behavior

### Measurements

Fill in actual measurements; lab-bench values will differ from datasheet
AM1.5 because indoor lighting is far below 1 sun.

| Parameter | Datasheet (AM1.5) | Measured | Lighting Condition |
|---|---|---|---|
| Voc (face, 4S) | 27.64 V | _____ V | _________________ |
| Isc (face) | 58.6 mA | _____ mA | _________________ |
| Vmp (face) | 22.32 V | _____ V | _________________ |
| Imp (face) | 55.1 mA | _____ mA | _________________ |
| Pmp (face) | 1.23 W | _____ W | _________________ |

### Charger Coupling

| Condition | Vin_solar (V) | LTC4162 MPP target (V) | Vout_pp (V) | Notes |
|---|---|---|---|---|
| 4S to charger, indoor | _____ | _____ | _____ | _____ |
| 4S to charger, full sun | _____ | _____ | _____ | _____ |

### Initial Acceptance Criteria

- Measured Voc and Isc consistent with module count and lighting condition
- LTC4162 settles to a stable MPPT operating point within ±2 V of measured Vmp
- Charging current to battery is non-zero and stable

### Observations / Notes

```




```

---

## Test 4: Dynamic Load Behavior

### Objective

- Validate EPS output robustness under load-step conditions
- Characterize droop/overshoot and recovery behavior

### Procedure

1. Apply programmable electronic load to 5 V and 3.3 V rails
2. Sweep static load from 0.1 A to applicable max current points
3. Execute 25%↔75% step-load transitions (e.g., 0.5 A ↔ 1.5 A) at 1 kHz
4. Capture rail waveforms (scope, 20 MHz BW, single-shot)
5. Record droop, overshoot, and recovery time

### Measurements

| Rail | Step (A→A) | Droop (mV) | Overshoot (mV) | Recovery to ±2% (µs) | Pass/Fail |
|---|---|---|---|---|---|
| +3V3 | 0.5 → 1.5 | _____ | _____ | _____ | _____ |
| +3V3 | 0.25 → 0.75 | _____ | _____ | _____ | _____ |
| +5V  | 0.5 → 1.5 | _____ | _____ | _____ | _____ |
| +5V  | 0.25 → 0.75 | _____ | _____ | _____ | _____ |

### Initial Acceptance Criteria

- Rails recover to within ±2% in ≤ 2 ms after defined load steps
- Peak droop/overshoot remains ≤ ±5% of nominal rail
- No unsafe thermal or stability behavior under defined profiles

### Observations / Notes

```




```

---

## Evidence Capture Requirements

- Save scope screenshots and instrument logs per test case to
  `hardware/eps/bringup/screenshots/<date>/`
- Record test setup (sources, load settings, ambient conditions) inline in
  this doc's Notes blocks
- Photograph the bench setup once per session
- Save I2C telemetry log from the LTC4162 alongside scope captures

## Exit Condition for Phase 1

- Core charge and regulation behavior is repeatable and documented
- Open EPS risks are narrowed to integration-level items
- All four test sections have measured values filled in and Pass/Fail recorded
- Inputs are ready for integrated system validation planning

## Bring-Up Session Log

Add a row each session so we can review history together.

| Date | Operator | Tests Run | Outcome | Issues / Follow-Ups |
|---|---|---|---|---|
| _____ | _____ | _____ | _____ | _____ |
| _____ | _____ | _____ | _____ | _____ |
| _____ | _____ | _____ | _____ | _____ |
