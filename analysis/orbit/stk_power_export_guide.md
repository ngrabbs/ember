# STK Export Guide — EPS Power Analysis

## Purpose

Generate sun-exposure and eclipse datasets for three reference orbits so the
EPS power budget can be closed against real orbital constraints. This analysis
supports the capstone requirement that EPS has a physical constraint (orbital
geometry) outside the design team's control.

---

## Reference Orbits

Set up three separate STK scenarios (or one scenario with three satellites).
Use a common epoch — **1 Jan 2027 00:00:00 UTCG** — so all three are directly
comparable.

| ID   | Name             | Altitude (km) | Inclination | Notes                                  |
|------|------------------|---------------|-------------|----------------------------------------|
| ORB1 | ISS Release      | 410           | 51.6°       | Realistic CubeSat deployment path      |
| ORB2 | Very Low LEO     | 325           | 51.6°       | Worst-case power; sub-Starlink ref     |
| ORB3 | Sun-Synchronous  | 550           | 97.5°       | Nominal CubeSat orbit; pick LTAN 10:30 |

Use circular orbits (eccentricity = 0) for all three.  RAAN doesn't matter for
ORB1/ORB2 — pick 0°.  For ORB3, set RAAN to match the chosen LTAN at epoch.

---

## Satellite Object Setup

### Spacecraft Body

- Use a 1U CubeSat body (10 × 10 × 10 cm)
- If STK asks for mass, use 1.3 kg (reasonable for a 1U)

### Attitude

Run each orbit under **two attitude cases**:

| Case | Attitude         | Rationale                                      |
|------|------------------|------------------------------------------------|
| A    | Nadir-pointing   | Best-case: one face always toward sun (nominal) |
| B    | Uniform tumble   | Worst-case: average illumination across faces   |

For tumble, STK's "spinning" or "fixed in body" with a slow spin rate
(~2°/s about all axes) works.  The goal is to get an average effective area,
not model exact dynamics.

### Solar Panels

The satellite has **4 body-mounted solar panels** (one per long face of the
1U stack, top and bottom are connector/antenna faces):

- Module: IXYS SM141K10TF (10 internal cells laser-scribed in series, 25% eff, 307 mW @ AM1.5)
- Configuration: 4 modules in series per face, 4 faces in parallel
- Physical footprint per face: 70.4 × 92.8 mm (measured) — ~65% of 1U face
- Module Vmp: 5.58 V → Face Vmp: 22.32 V (4S)
- Module Imp: 55.1 mA → Face Imp: 55.1 mA (series)
- Face Pmp (AM1.5): 1,228 mW
- Face Pmp (AM0, estimated): ~1,708 mW (current scales with 1.361× irradiance)

**Total installed capacity (4 faces): ~6.83 W at AM0 BOL**

LTC4162 input voltage: 22.3 V Vmp nominal, 27.6 V Voc — well within 4.5-35 V
range with excellent margin across full temperature envelope.

In STK, you can model these as 4 flat-plate solar panels offset 90° apart on
the body frame, each 2.67 cm × 10 cm (or equivalent area).

---

## What to Export

### Export 1 — Lighting Intervals (Critical)

**Report:** Satellite → Lighting Times report (or Access to Sun)

Export for each orbit, for a **7-day analysis period** starting at epoch.
Run at two times of year if time allows: epoch (Jan) and equinox (Mar 21).

| Column             | STK Report Field                    |
|--------------------|-------------------------------------|
| Start Time (UTCG)  | Sunlight start                      |
| Stop Time (UTCG)   | Sunlight stop                       |
| Duration (sec)     | Sunlight duration                   |
| Eclipse Start      | Penumbra/Umbra entry time           |
| Eclipse Duration   | Penumbra + Umbra duration           |

**Export format:** `.csv`
**Filename convention:** `lighting_ORB1_jan.csv`, `lighting_ORB2_jan.csv`, etc.
**Save to:** `analysis/orbit/exports/`

#### Checkpoints

- [x] ORB1 ISS Release — lighting intervals exported (Jan epoch)
- [x] ORB2 Very Low LEO — lighting intervals exported (Jan epoch)
- [x] ORB3 Sun-Sync — lighting intervals exported (Jan epoch)
- [x] Repeat all three at equinox epoch (21 Mar 2027)

### Export 2 — Solar Incidence Angles (Important)

**Report:** Custom Data Provider → Solar Incidence Angle on each body face

This tells us the angle between the sun vector and each panel normal over time.
Effective power = Pmp × cos(θ) when the face is illuminated, 0 when in shadow
or θ > 90°.

Export as a **time-series** (60-second time step, 7-day span):

| Column                | Description                         |
|-----------------------|-------------------------------------|
| Time (UTCG)           | Timestamp                           |
| Sun_Incidence_+X (°)  | Angle to +X face normal             |
| Sun_Incidence_-X (°)  | Angle to −X face normal             |
| Sun_Incidence_+Y (°)  | Angle to +Y face normal             |
| Sun_Incidence_-Y (°)  | Angle to −Y face normal             |

If STK doesn't give per-face incidence directly, export the **Sun Unit Vector
in Body Frame** (3 components) and we'll compute cos(θ) per face in the
spreadsheet.

**Export format:** `.csv`
**Filename convention:** `sun_angle_ORB1_nadir_jan.csv`, `sun_angle_ORB1_tumble_jan.csv`
**Save to:** `analysis/orbit/exports/`

#### Checkpoints

- [x] ORB1 nadir — sun incidence/vector exported (epoch + equinox)
- [x] ORB1 spinning — sun incidence/vector exported (epoch + equinox)
- [x] ORB2 nadir — sun incidence/vector exported (epoch + equinox)
- [x] ORB2 spinning — sun incidence/vector exported (epoch + equinox)
- [x] ORB3 nadir — sun incidence/vector exported (epoch + equinox)
- [x] ORB3 spinning — sun incidence/vector exported (epoch + equinox)

### Export 3 — Beta Angle (Nice-to-Have)

**Report:** Satellite → Beta Angle over time

Beta angle drives eclipse fraction seasonally.  Export over a **full year**
(1-day time step) for each orbit.

| Column       | Description                              |
|--------------|------------------------------------------|
| Time (UTCG)  | Date                                     |
| Beta (°)     | Angle between orbit plane and sun vector |

**Export format:** `.csv`
**Filename convention:** `beta_ORB1_yearly.csv`
**Save to:** `analysis/orbit/exports/`

#### Checkpoints

- [ ] ORB1 — yearly beta angle exported
- [ ] ORB2 — yearly beta angle exported
- [ ] ORB3 — yearly beta angle exported

### Export 4 — Orbit-Average Summary (Quick Sanity Check)

Before exporting all the time-series data, grab these summary numbers from STK
for each orbit and jot them here:

| Parameter                        | ORB1 (ISS) | ORB2 (VLEO) | ORB3 (SSO) |
|----------------------------------|------------|-------------|------------|
| Orbital period (min)             | 92.8       | 91.0        | 95.8       |
| Sunlight fraction — Epoch (%)    | 61.0       | 59.8        | 63.6       |
| Sunlight fraction — Equinox (%)  | 63.4       | 64.5        | 64.1       |
| Max eclipse duration (min)       | 35.6       | 36.1        | 34.0       |
| Min eclipse duration (min)       | 34.5       | 35.1        | 22.8       |
| Avg eclipse duration (min)       | 35.0       | 35.6        | 33.9       |
| Eclipses per day                 | ~15.6      | ~15.9       | ~15.2      |
| Beta angle at epoch (°)          |            |             |            |

**Design driver:** ORB2 VLEO at epoch — 59.8% sun, 36.1 min worst-case eclipse.

Fill this in first — it's the quickest sanity check that the scenarios are
set up correctly.  ISS should be ~92 min period, ~35-40% eclipse.  VLEO should
be ~91 min.  SSO at 550 km should be ~96 min.

---

## STK Settings / Gotchas

1. **Lighting model:** Use "Dual Cone" (penumbra + umbra), not "Rectangular".
2. **Atmospheric refraction:** Leave OFF for consistency — refraction effects
   are negligible for power analysis.
3. **Solar flux:** STK defaults to 1361 W/m² (AM0). This is correct — don't
   change it. Our panel specs are already at AM0.
4. **Time step for time-series exports:** 60 seconds is a good balance.
   Finer than orbit-average, coarse enough to not generate massive files.
5. **Coordinate frame for sun vector:** Export in **Body frame**, not ECI/ECEF.
   We need the angle relative to the panel normals, which are fixed in body.
6. **Save the .sc scenario files** to `analysis/orbit/scenarios/` so
   anyone can reopen and re-export later.

---

## File Inventory After Export

When done, `analysis/orbit/exports/` should contain:

```
lighting_ORB1_jan.csv
lighting_ORB2_jan.csv
lighting_ORB3_jan.csv
sun_angle_ORB1_nadir_jan.csv
sun_angle_ORB1_tumble_jan.csv
sun_angle_ORB2_nadir_jan.csv
sun_angle_ORB2_tumble_jan.csv
sun_angle_ORB3_nadir_jan.csv
sun_angle_ORB3_tumble_jan.csv
beta_ORB1_yearly.csv
beta_ORB2_yearly.csv
beta_ORB3_yearly.csv
```

And `analysis/orbit/scenarios/` should contain the `.sc` files.

---

## What Happens Next

These exports feed directly into the power budget in `analysis/power/` where we
compute:

1. Per-orbit energy harvested (Wh) = Σ(panel power × cos θ × Δt) over sunlit arcs
2. Per-orbit energy consumed (Wh) = load profile × orbit period
3. Energy balance = harvested − consumed (must be ≥ 0 over any 24h window)
4. Battery DOD per eclipse = eclipse load × eclipse duration / battery capacity
5. Pass/fail against requirement: SOC stays above 20% in worst-case orbit
