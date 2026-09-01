# EPS Power Budget

## Requirement

> The EPS shall maintain positive energy balance over any 24-hour period under
> nominal load, with battery state-of-charge remaining above 20%.
>
> **Physical constraint:** Eclipse fraction and solar incidence geometry are
> determined by orbital parameters outside the design team's control.

---

## Definitions

| Term | Meaning |
|------|---------|
| AM0  | Air Mass Zero — solar irradiance in space with no atmospheric filtering (1361 W/m²). All solar cell specs in this budget use AM0, since the panels operate in orbit. Ground-level specs use AM1.5 (1000 W/m²). |
| BOL  | Beginning Of Life — panel performance when new, before radiation degradation. |
| EOL  | End Of Life — panel performance after accumulated radiation damage. The EOL factor estimates remaining output after the mission duration. |
| DOD  | Depth Of Discharge — percentage of battery capacity used during an eclipse. A 20% DOD means 20% of total energy was consumed. |
| SOC  | State Of Charge — remaining battery capacity as a percentage (SOC = 100% − DOD from full). |
| MPPT | Maximum Power Point Tracking — the LTC4162 charger algorithm that adjusts the operating point to extract peak power from the solar array. |

---

## 1 — Solar Array Parameters

| Parameter                    | Value       | Source / Notes                    |
|------------------------------|-------------|-----------------------------------|
| Cell type                    | SM141K10TF  | IXYS/Anysolar (10-cell Si module) |
| Module Voc                   | 6.91 V      | Datasheet, AM1.5, 25°C           |
| Module Isc                   | 58.6 mA     | Datasheet, AM1.5, 25°C           |
| Module Vmp                   | 5.58 V      | Datasheet, AM1.5, 25°C           |
| Module Imp                   | 55.1 mA     | Datasheet, AM1.5, 25°C           |
| Module Pmp                   | 307 mW      | Datasheet, AM1.5, 25°C           |
| Module efficiency            | 25%         | Datasheet                         |
| Modules per face (series)    | 4           | 4S string                         |
| Face Vmp (AM1.5)             | 22.32 V     | 4 × 5.58 V                       |
| Face Imp (AM1.5)             | 55.1 mA     | Series — current unchanged        |
| Face Pmp (AM1.5)             | 1,228 mW    | 4 × 307 mW                       |
| Face Vmp (AM0, est.)         | 22.8 V      | ~+2% voltage at higher irradiance |
| Face Imp (AM0, est.)         | 75.0 mA     | Scales linearly: 55.1 × 1.361    |
| Face Pmp (AM0, est.)         | 1,708 mW    | 22.8 V × 75.0 mA                 |
| Panels (faces)               | 4           | Body-mounted, ±X and ±Y, parallel |
| Total installed Pmp (AM0 BOL)| 6,832 mW    | 4 × 1,708 mW (all faces normal)  |
| Physical footprint (4 modules)| 70.4×92.8mm | Measured — 65% face coverage      |
| Temperature derating         | 0.85        | Estimate — cells reach 60-80°C    |
| EOL degradation factor       | 0.90        | ~10% after 1-2 yr radiation       |
| Packing / cosine loss budget | (from STK)  | Orbit-dependent geometry factor   |
| MPPT efficiency (LTC4162)    | 0.93        | Datasheet typical                 |

**Effective array power = Pmp_face(AM0) × temp_derate × EOL × MPPT_eff × geometry_factor**

Note: AM1.5 specs (1000 W/m²) are the datasheet standard test condition.
AM0 values (1361 W/m²) are estimated by linear irradiance scaling on current
and ~2% voltage increase.  This is the operating condition in orbit.

---

## 2 — Battery Parameters

### Cell (LG INR18650 MJ1)

| Parameter                  | Value      | Notes                                |
|----------------------------|------------|--------------------------------------|
| Chemistry                  | Li-ion NMC | Single cell, datasheet 25°C          |
| Nominal voltage            | 3.635 V    | Datasheet — often rounded to 3.6 V   |
| Max charge voltage         | 4.20 V     |                                      |
| Discharge cut-off          | 2.50 V     |                                      |
| Typical capacity           | 3500 mAh   | At 0.2C discharge, 25°C              |
| Minimum capacity           | 3400 mAh   | Spec floor                           |
| Typical energy per cell    | ~12.7 Wh   | 3500 mAh × 3.635 V                   |

### Pack (2S2P)

| Parameter                  | Value           | Notes                                |
|----------------------------|-----------------|--------------------------------------|
| Configuration              | 2S2P            | 4 cells total, 2 series × 2 parallel |
| Pack nominal voltage       | 7.27 V          | 2 × 3.635 V (rounded to 7.2 V elsewhere in doc) |
| Pack max voltage           | 8.40 V          | Fully charged, end of CV phase       |
| Pack min voltage           | 5.00 V          | At cut-off                           |
| Nameplate capacity         | 7000 mAh (typ)  | 2P at typical; 6800 mAh at spec floor |
| Nameplate energy           | **50.4 Wh**     | 7000 mAh × 7.2 V (canonical for this doc) |
| Max charge rate            | 3.2 A           | LTC4162 limit (cell-level ~0.46C, well under MJ1's 1C spec) |

### Usable energy — what to actually budget against

Nameplate is what you *have*; usable is what you can *spend* and still close the mission.

| Scenario                       | Effective capacity | Energy   | When to use                          |
|--------------------------------|--------------------|----------|--------------------------------------|
| Nameplate (BOL, 25°C, 100% DoD) | 7000 mAh          | 50.4 Wh  | Marketing math only — never budget against this |
| Requirement floor (100→20% DoD) | 5600 mAh          | 40.3 Wh  | Absolute worst-case ride-through (single deep eclipse, end of mission) |
| **LEO cycling target (~30% DoD)** | **2100 mAh**    | **~15 Wh** | **Default per-orbit eclipse budget** — leaves room for 5000+ cycles of cycle life |
| EOL nameplate (~80% retained)   | 5600 mAh          | ~40 Wh   | After ~1 yr LEO. Apply on top of DoD limits. |

**The number to remember:** ~15 Wh of energy you can actually pull each eclipse without trashing the pack. Anything more is digging into cycle life or EOL margin.

### Temperature derating

LG MJ1 is rated at 25°C. On-orbit pack temps vary:

| Condition       | Capacity retained | Note                                  |
|-----------------|-------------------|---------------------------------------|
| +25°C           | 100%              | Datasheet baseline                    |
| 0°C             | ~90%              | Mild loss                             |
| −10°C           | ~80%              | Significant — heaters become attractive |
| −20°C           | ~65–70%           | Don't discharge here if avoidable     |
| Below 0°C charge | Do not charge    | Plating risk. LTC4162 NTC should inhibit. |

**Rule of thumb:** if the pack can drop below 0°C in eclipse, knock another 10–15% off the usable-energy numbers above when sizing for worst-case orbits.

### Quick-reference summary

- **Nameplate: 7.0 Ah / 50.4 Wh** at 7.2 V nominal
- **Useful per eclipse (default budget): ~15 Wh** (30% DoD for cycle life)
- **Hard floor (requirement): 40.3 Wh** (80% DoD, EOL, cold — only at end-of-mission worst case)
- **Charge current cap: 3.2 A** (LTC4162-limited, not pack-limited)

---

## 3 — Load Profile

Fill in measured or estimated current draw per subsystem at each rail.

### 3.3 V Rail Loads

| Subsystem          | Mode     | Current (mA) | Power (mW) | Duty (%)  | Avg Power (mW) |
|--------------------|----------|--------------|------------|-----------|-----------------|
| Internal Housekeeping Unit  | Active   |              |            | 100       |                 |
| Internal Housekeeping Unit  | Sleep    |              |            | 0         |                 |
| Comms RX (SA612A)  | Listen   |              |            |           |                 |
| Comms RP2040       | Active   |              |            |           |                 |
| EPS telemetry I2C  | Active   |              |            | 100       |                 |
| Payload sensors    | Sample   |              |            |           |                 |
| Payload sensors    | Idle     |              |            |           |                 |
| **3.3V subtotal**  |          |              |            |           |                 |

### 5 V Rail Loads

| Subsystem          | Mode     | Current (mA) | Power (mW) | Duty (%)  | Avg Power (mW) |
|--------------------|----------|--------------|------------|-----------|-----------------|
| Comms TX chain     | Transmit |              |            |           |                 |
| Comms TX chain     | Idle     |              |            |           |                 |
| Burn wire deploy   | Deploy   |              |            | one-shot  |                 |
| **5V subtotal**    |          |              |            |           |                 |

### System-Level

| Parameter                         | Value       | Notes                    |
|-----------------------------------|-------------|--------------------------|
| TPS62933F 3.3V efficiency         | 0.90        | Estimate at light load   |
| TPS62933F 5V efficiency           | 0.92        | Estimate at light load   |
| Total avg load at rails           |             | Sum of subtotals         |
| Total avg load at VOUT_PP         |             | Rail loads / efficiencies |

---

## 4 — Operating Modes

Define 3 modes for the power budget calculation:

| Mode        | Description                         | 3.3V Load (mW) | 5V Load (mW) | Total at Bus (mW) |
|-------------|-------------------------------------|-----------------|---------------|--------------------|
| **Nominal** | All systems active, TX at duty cycle |                 |               |                    |
| **RX-Only** | TX off, payload sampling, IHU active  |                 |               |                    |
| **Safe**    | IHU + EPS telem only, 5V gated off   |                 |               |                    |

---

## 5 — Per-Orbit Energy Balance

This is where the STK exports plug in.  One row per orbit × mode combination.

### Computed Results (from STK exports, Jan epoch — worst season)

Parameters: Pmp/face(AM0) = 1,708 mW | Derating = ×0.85 × 0.90 × 0.93 = 1,215 mW per unit geometry

| Orbit | Attitude | Period | Sunlit% | Geo Factor | Orbit-Avg Harvest (mW) | Harvest/Orbit (mWh) |
|-------|----------|--------|---------|------------|------------------------|---------------------|
| ORB1  | Nadir    | 92.8   | 61.7%   | 1.010      | 758                    | 1,173               |
| ORB1  | Spinning | 92.8   | 61.7%   | 1.179      | 885                    | 1,368               |
| ORB2  | Nadir    | 91.0   | 60.5%   | 1.001      | 736                    | 1,117               |
| ORB2  | Spinning | 91.0   | 60.5%   | 1.179      | 867                    | 1,316               |
| ORB3  | Nadir    | 95.8   | 64.1%   | 1.063      | 828                    | 1,322               |
| ORB3  | Spinning | 95.8   | 64.1%   | 1.179      | 918                    | 1,466               |

**Design driver:** ORB2 VLEO / Nadir / Jan epoch — 736 mW orbit-average, 1,117 mWh per orbit.

### Load budget comparison (placeholder — update Section 3 with real values)

At a placeholder load of 200 mW continuous:

| Orbit | Attitude | Harvest/Orb (mWh) | Load/Orb (mWh) | Balance (mWh) | Eclipse DOD | Min SOC | Pass? |
|-------|----------|-------------------|----------------|---------------|-------------|---------|-------|
| ORB1  | Nadir    | 1,173             | 309            | +863          | 0.23%       | 99.8%   | YES   |
| ORB1  | Spinning | 1,368             | 309            | +1,059        | 0.23%       | 99.8%   | YES   |
| ORB2  | Nadir    | 1,117             | 303            | +814          | 0.24%       | 99.8%   | YES   |
| ORB2  | Spinning | 1,316             | 303            | +1,012        | 0.24%       | 99.8%   | YES   |
| ORB3  | Nadir    | 1,322             | 319            | +1,002        | 0.23%       | 99.8%   | YES   |
| ORB3  | Spinning | 1,466             | 319            | +1,146        | 0.23%       | 99.8%   | YES   |

Even at 200 mW continuous load, worst-case harvest is 3.7× the load.
Eclipse DOD is negligible — a single 36-min eclipse at 200 mW draws only
120 mWh = 0.24% of the 50.4 Wh battery.

### How Each Column Was Computed

- **Geometry Factor:** orbit-average of Σ max(0, cos(θ)) across all 4 faces
  during sunlit arc only.  Computed from STK body-frame sun vector exports
  cross-referenced with lighting interval data.  cos(θ) = dot product of
  sun unit vector with each face normal (+X, −X, +Y, −Y in body frame).

- **Orbit-Avg Harvest (mW):**
  `1,215 mW × geometry_factor × sunlit_fraction`
  where 1,215 = Pmp_face(AM0) × temp × EOL × MPPT = 1708 × 0.85 × 0.90 × 0.93

- **Harvest/Orbit (mWh):**
  `orbit_avg_harvest × period_min / 60`

- **Load/Orbit (mWh):**
  `bus_power_for_mode × period_min / 60`

- **Balance (mWh):**
  `harvest - load` (must be ≥ 0 for sustainability)

- **Eclipse DOD (%):**
  `(bus_power × eclipse_min / 60) / battery_energy_Wh × 100`
  where battery_energy_Wh = 50.4 Wh (2S2P MJ1)

- **SOC Min (%):**
  `100 - eclipse_DOD` (must stay ≥ 20%)

---

## 6 — Pass/Fail Summary

**All cases PASS with large margin.**  The design driver is ORB2 VLEO / Nadir /
Jan epoch with 736 mW orbit-average harvest.

| Orbit | Attitude | Harvest (mW) | Margin over 200mW load | Min SOC (%) | **Pass?** |
|-------|----------|-------------|------------------------|-------------|-----------|
| ORB1  | Nadir    | 758         | 3.8×                   | 99.8%       | **YES**   |
| ORB1  | Spinning | 885         | 4.4×                   | 99.8%       | **YES**   |
| ORB2  | Nadir    | 736         | 3.7×                   | 99.8%       | **YES**   |
| ORB2  | Spinning | 867         | 4.3×                   | 99.8%       | **YES**   |
| ORB3  | Nadir    | 828         | 4.1×                   | 99.8%       | **YES**   |
| ORB3  | Spinning | 918         | 4.6×                   | 99.8%       | **YES**   |

**Design closes.** Even the absolute worst case (ORB2 nadir Jan) provides 3.7×
margin over the placeholder load.  The battery is effectively a "ride-through"
buffer for 36-minute eclipses — DOD per eclipse is negligible at <0.25%.

The system could sustain loads up to ~700 mW continuous before the worst-case
orbit fails to close.  This provides substantial headroom for TX duty cycle,
payload operations, or heater power if needed.

**Remaining action:** Fill in Section 3 (Load Profile) with measured/estimated
subsystem currents to replace the 200 mW placeholder with real values.

---

## 7 — Notes

- All panel specs are AM0 (space), BOL, 25°C.  The temperature derating
  factor accounts for on-orbit panel temps (~60-80°C in sun).
- Face Vmp is 22.32 V at 25°C (AM1.5).  With ~10 internal cells per module
  and 4 modules in series (40 junctions total), tempco is approximately
  −2 mV/°C per junction × 40 = −80 mV/°C for the full string.  At 80°C
  panel temp, face Vmp drops to ~22.32 − (55 × 0.080) = ~17.9 V — still
  well above LTC4162 minimum input of 4.5 V.  Excellent margin.
- Face Voc (cold, −40°C) = 4 × 6.91 × ~1.15 = ~31.8 V — still under
  LTC4162 absolute max of 35 V.  Safe across full temperature range.
- LG MJ1 capacity is rated at 25°C.  On-orbit battery temps may reduce
  effective capacity by 5-15% — not modeled here but should be a margin note.
- The MPPT efficiency of 0.93 assumes the LTC4162 is tracking near Vmp.
  If the panel voltage is far from Vmp (e.g., partial illumination), actual
  efficiency may be lower.
- This budget is steady-state per orbit.  Transient worst-case (e.g., battery
  starts at 20% SOC entering a long eclipse) should be checked separately
  if any case is marginal.

---

## 8 — Worked Example: How the Numbers Were Computed

This section walks through the full calculation chain so a team member can
reproduce or modify the results.  We'll use the worst-case scenario as the
worked example: **ORB2 VLEO / Nadir / January epoch**.

### Step 1: Solar Module Electrical Specs

The SM141K10TF datasheet gives performance at AM1.5 (1000 W/m², 25°C):

```
Module Vmp = 5.58 V
Module Imp = 55.1 mA
Module Pmp = 5.58 × 0.0551 = 307.4 mW
```

Each module contains 10 silicon cells laser-scribed in series internally.
We have **4 modules in series** on each face panel.

```
Face Vmp = 4 × 5.58 = 22.32 V
Face Imp = 55.1 mA   (series connection — current is same through all)
Face Pmp (AM1.5) = 22.32 × 0.0551 = 1,229.8 mW ≈ 1,228 mW
```

### Step 2: Scale from AM1.5 to AM0

In orbit, solar irradiance is AM0 = 1,361 W/m² (no atmosphere).  The
datasheet specs are at AM1.5 = 1,000 W/m².  To convert:

- **Current scales linearly** with irradiance (more photons = more current):
  ```
  Imp(AM0) = 55.1 mA × (1361 / 1000) = 55.1 × 1.361 = 75.0 mA
  ```

- **Voltage increases slightly** (logarithmic relationship, ~+2%):
  ```
  Vmp(AM0) ≈ 5.58 × 1.02 = 5.69 V per module
  Face Vmp(AM0) = 4 × 5.69 = 22.76 V
  ```

- **Face power at AM0:**
  ```
  Pmp_face(AM0) = 22.76 × 0.0750 = 1,707 mW ≈ 1,708 mW
  ```

### Step 3: Apply Derating Factors

Real on-orbit performance is less than BOL AM0 due to:

| Factor       | Value | Why                                           |
|--------------|-------|-----------------------------------------------|
| Temperature  | 0.85  | Panels reach 60-80°C in sun; Si loses ~0.4%/°C |
| EOL radiation| 0.90  | ~10% degradation from proton/electron damage   |
| MPPT tracking| 0.93  | LTC4162 doesn't track Vmp perfectly            |

Combined derating:
```
derated_power_per_face = 1,708 × 0.85 × 0.90 × 0.93
                       = 1,708 × 0.7117
                       = 1,215.6 mW per unit geometry factor
```

This is the power you get from ONE face when the sun hits it at normal
incidence (cos θ = 1.0), after all real-world losses.

### Step 4: Geometry Factor from STK

The satellite has 4 body-mounted panels on faces ±X and ±Y.  At any
instant, the sun illuminates some faces at various angles.  The power
from each face depends on cos(θ), where θ is the angle between the sun
vector and the face normal.

From the STK export, at each 1-minute time step during sunlit arc, we get
the sun unit vector in body frame: (x, y, z).  The face normals are:

```
+X face normal = (1, 0, 0)   →  cos(θ) = x      (use if x > 0, else 0)
-X face normal = (-1, 0, 0)  →  cos(θ) = -x     (use if x < 0, else 0)
+Y face normal = (0, 1, 0)   →  cos(θ) = y      (use if y > 0, else 0)
-Y face normal = (0, -1, 0)  →  cos(θ) = -y     (use if y < 0, else 0)
```

At each time step, the total instantaneous power contribution is:
```
face_sum = max(0, x) + max(0, -x) + max(0, y) + max(0, -y)
```

The **geometry factor** is the average of face_sum over all sunlit minutes:
```
geometry_factor = (1/N) × Σ face_sum   (summed over N sunlit samples)
```

For ORB2 nadir January, this came out to **1.001**.

**Why is it close to 1.0?**  In nadir-pointing mode, the body Y-axis is
aligned with the orbit normal.  The sun angle to the orbit plane is ~23°
in January (declination), so the +Y face gets a constant cos(23°) ≈ 0.61,
while the X faces alternate between illuminated and shadowed as the
satellite orbits.  On average: ~0.61 from +Y + ~0.40 average from X faces
≈ 1.0.

For the **spinning** case, all faces get swept through the sun, and the
geometry factor is higher (~1.18) because both ±Y faces contribute.

### Step 5: Sunlit Fraction from STK

The lighting intervals export tells us when the satellite is in sunlight
vs. eclipse (umbra/penumbra).  For ORB2 January:

```
Orbital period:     91.0 min
Avg sunlight:       55.0 min
Avg eclipse:        36.0 min  (umbra + penumbra)
Sunlit fraction:    55.0 / 91.0 = 0.605 = 60.5%
```

We only harvest power during the sunlit arc.  During eclipse, harvest = 0.

### Step 6: Orbit-Average Harvest Power

```
orbit_avg_harvest = derated_power × geometry_factor × sunlit_fraction
                  = 1,215.6 mW × 1.001 × 0.605
                  = 736 mW
```

This is the power averaged over the full orbit (sunlit + eclipse).

### Step 7: Energy Harvested Per Orbit

```
harvest_per_orbit = orbit_avg_harvest × period / 60
                  = 736 mW × 91.0 min / 60
                  = 1,116 mWh per orbit
```

### Step 8: Load Energy Per Orbit

Using the placeholder load of 200 mW continuous:
```
load_per_orbit = 200 mW × 91.0 / 60 = 303.3 mWh per orbit
```

### Step 9: Energy Balance

```
balance = harvest - load = 1,116 - 303 = +813 mWh per orbit
```

Positive balance means the battery charges more per orbit than it
discharges.  The system is sustainable.

### Step 10: Eclipse Depth-of-Discharge

During each eclipse, the battery alone powers the spacecraft:
```
eclipse_energy = load × eclipse_duration / 60
               = 200 mW × 36.0 min / 60
               = 120 mWh = 0.120 Wh

eclipse_DOD = eclipse_energy / battery_capacity × 100
            = 0.120 Wh / 50.4 Wh × 100
            = 0.24%
```

### Step 11: Minimum State-of-Charge

```
min_SOC = 100% - eclipse_DOD = 100% - 0.24% = 99.76% ≈ 99.8%
```

This is the SOC at the end of the longest eclipse, assuming the battery
started that eclipse at 100%.  Our requirement is min_SOC ≥ 20%.

### Step 12: Pass/Fail

```
Balance > 0?    +813 mWh > 0     ✓ PASS
Min SOC > 20%?  99.8% > 20%      ✓ PASS
```

### Summary of the Calculation Chain

```
Datasheet (AM1.5)
  → Scale to AM0 (×1.361 on current, ×1.02 on voltage)
    → Apply deratings (×0.85 temp × 0.90 EOL × 0.93 MPPT)
      → Multiply by geometry factor (from STK sun vector + face normals)
        �� Multiply by sunlit fraction (from STK lighting intervals)
          → Result: orbit-average harvest power (mW)
            → Compare to load power → energy balance
            → Compute eclipse DOD → min SOC → pass/fail
```

### Python Script

The script that produces the tables above is [`power_budget.py`](power_budget.py), in this
directory. Run it from the repository root:

```bash
python3 analysis/power/power_budget.py
```

It reads the STK exports in `analysis/orbit/exports/` directly and needs
no dependencies beyond the standard library. Its output reproduces the
geometry factors, sunlit fractions and harvest powers in Section 5 exactly;
orbital periods agree to within 0.2%, because the script takes the median
lighting-interval length rather than reading the period from STK.

Core logic for a single scenario:
```python
import csv
from datetime import datetime

def parse_time(s):
    return datetime.strptime(s.strip(), "%d %b %Y %H:%M:%S.%f")

# Load sunlight intervals (start, stop) from lighting CSV
def load_lighting(filepath):
    intervals = []
    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for r in reader:
            if len(r) >= 2 and r[0].strip() and r[1].strip():
                intervals.append((parse_time(r[0]), parse_time(r[1])))
    return intervals

# Check if timestamp falls within a sunlit interval (binary search)
def is_sunlit(t, intervals):
    lo, hi = 0, len(intervals) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if t < intervals[mid][0]:
            hi = mid - 1
        elif t > intervals[mid][1]:
            lo = mid + 1
        else:
            return True
    return False

# Process sun vector CSV + lighting intervals
def compute_geometry(sun_vector_csv, lighting_csv):
    lighting = load_lighting(lighting_csv)
    total_cos = 0.0
    sunlit_count = 0
    total_count = 0

    with open(sun_vector_csv) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) < 8 or not row[0].strip():
                continue
            total_count += 1
            t = parse_time(row[0])
            if not is_sunlit(t, lighting):
                continue

            # Unit vector components (columns 5, 6, 7)
            x = float(row[5])  # x/Magnitude
            y = float(row[6])  # y/Magnitude
            z = float(row[7])  # z/Magnitude

            # Sum cos(theta) for each illuminated face
            face_sum = max(0,x) + max(0,-x) + max(0,y) + max(0,-y)
            total_cos += face_sum
            sunlit_count += 1

    geometry_factor = total_cos / sunlit_count
    sunlit_fraction = sunlit_count / total_count
    return geometry_factor, sunlit_fraction

# Run it
geo, sun_frac = compute_geometry(
    "VeryLowLEO_SolarIncidenceAngles_nadir_epoch.csv",
    "VeryLowLEO_Lighting_Times_Epoch.csv"
)

# Compute harvest
Pmp_face_AM0 = 1708       # mW
derated = Pmp_face_AM0 * 0.85 * 0.90 * 0.93  # = 1215.6 mW
orbit_avg_mW = derated * geo * sun_frac
print(f"Geometry factor: {geo:.3f}")
print(f"Sunlit fraction: {sun_frac:.3f}")
print(f"Orbit-avg harvest: {orbit_avg_mW:.0f} mW")
```
