# Orbit Analysis

Orbit and access modelling supporting the link budget and the onboard
screening argument: how often the spacecraft sees a scene, and how much
contact time the ground station gets to return detections.

## Contents

| Path | What's here |
|---|---|
| `exports/` | STK report exports — lighting intervals and solar incidence angles per orbit, attitude, and season |
| `scenarios/` | Saved STK scenario files (`.sc`) so results can be regenerated |
| `stk_power_export_guide.md` | How to produce the exports above from STK |

## Orbit Modeling
- [ ] Define initial TLE or orbital parameters (LEO, sun-synchronous preferred)
- [ ] Set up the mission satellite object in STK
- [ ] Configure attitude (nadir pointing or passive tumble)

## Ground Station Access
- [ ] Model the fixed ground station and its antenna pattern
- [ ] Generate access reports between the spacecraft and the station
- [ ] Log contact duration, look angles, and revisit times
- [ ] Establish the per-pass data volume the downlink can actually return

## Payload Observation Geometry
- [ ] Define the instrument field of view and ground swath
- [ ] Derive revisit interval over a representative coverage area
- [ ] Correlate observation opportunities against contact windows

## Outputs

Plots, access reports, and written summaries land in this directory alongside
the scenario that produced them. Results to capture as they are produced:

- [ ] Access duration and revisit statistics
- [ ] Geometry constraints and their design implications
- [ ] Contact timelines plotted against detection-report generation rate
- [ ] Coverage map by orbital position
- [ ] Implications for the comms contact schedule

## Solar and Power Inputs

The lighting-time and solar-incidence exports in `exports/` feed the power
budget in `analysis/power/`, which reads them directly — see
`analysis/power/power_budget.py`. `stk_power_export_guide.md` documents the
export procedure.
