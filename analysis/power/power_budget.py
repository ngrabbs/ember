#!/usr/bin/env python3
"""Reproduce the orbit-average solar harvest table in README.md.

Reads the STK exports in analysis/orbit/exports/ and recomputes, for each
orbit and attitude, the geometry factor, sunlit fraction, and orbit-average
harvest power. Run from the repository root:

    python3 analysis/power/power_budget.py

The derating chain and the face-normal model are documented in README.md §8.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

EXPORTS = Path("analysis/orbit/exports")

# Panel chain — see README.md §1 and §8 step 3.
PMP_FACE_AM0_MW = 1708.0
TEMP_DERATE     = 0.85
EOL_DERATE      = 0.90
MPPT_EFF        = 0.93
DERATED_MW      = PMP_FACE_AM0_MW * TEMP_DERATE * EOL_DERATE * MPPT_EFF

# Placeholder load until README.md §3 is filled in with measured currents.
LOAD_MW = 200.0

BATTERY_WH = 50.4

ORBITS = [("ORB1", "ISSRelease"), ("ORB2", "VeryLowLEO"), ("ORB3", "SunSync")]
ATTITUDES = ["nadir", "spinning"]


def parse_time(s):
    return datetime.strptime(s.strip(), "%d %b %Y %H:%M:%S.%f")


def load_sunlit_intervals(path):
    """First interval group in an STK lighting export is the sunlight set."""
    intervals = []
    with open(path) as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            if len(r) >= 2 and r[0].strip() and r[1].strip():
                intervals.append((parse_time(r[0]), parse_time(r[1])))
    intervals.sort()
    return intervals


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


def lighting_durations(lighting_path):
    """Mean sunlight, penumbra and umbra durations in minutes.

    An STK lighting export carries three interval groups side by side:
    columns 0-2 sunlight, 3-5 penumbra, 6-8 umbra. The orbital period is
    their sum; eclipse is penumbra + umbra.
    """
    cols = {0: [], 1: [], 2: []}
    with open(lighting_path) as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            for group, idx in ((0, 2), (1, 5), (2, 8)):
                if len(r) > idx and r[idx].strip():
                    cols[group].append(float(r[idx]))
    # Median, not mean: the first and last interval in an export are
    # truncated by the scenario bounds and would bias a mean downward.
    def median(v):
        if not v:
            return 0.0
        v = sorted(v)
        n = len(v)
        m = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
        return m / 60.0
    sun, pen, umb = median(cols[0]), median(cols[1]), median(cols[2])
    return sun + pen + umb, pen + umb


def compute(sun_vector_csv, lighting_csv):
    """Geometry factor and sunlit fraction for four body-mounted faces (+-X, +-Y)."""
    lighting = load_sunlit_intervals(lighting_csv)
    total_cos = sunlit = total = 0
    with open(sun_vector_csv) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 8 or not row[0].strip():
                continue
            total += 1
            if not is_sunlit(parse_time(row[0]), lighting):
                continue
            x, y = float(row[5]), float(row[6])
            total_cos += max(0, x) + max(0, -x) + max(0, y) + max(0, -y)
            sunlit += 1
    if not sunlit:
        raise SystemExit(f"no sunlit samples in {sun_vector_csv}")
    return total_cos / sunlit, sunlit / total


def main():
    if not EXPORTS.is_dir():
        raise SystemExit(f"{EXPORTS} not found — run from the repository root")

    print(f"Derated power per face at unit geometry: {DERATED_MW:.1f} mW")
    print(f"Placeholder load: {LOAD_MW:.0f} mW continuous\n")
    hdr = f"{'Orbit':6} {'Attitude':9} {'Period':>7} {'Sunlit%':>8} {'Geo':>6} " \
          f"{'Harvest':>9} {'mWh/orb':>9} {'DOD%':>7} {'MinSOC%':>8}  Pass"
    print(hdr); print("-" * len(hdr))

    worst = None
    for tag, stem in ORBITS:
        lighting = EXPORTS / f"{stem}_Lighting_Times_Epoch.csv"
        period, ecl_min = lighting_durations(lighting)
        for att in ATTITUDES:
            sv = EXPORTS / f"{stem}_SolarIncidenceAngles_{att}_epoch.csv"
            geo, frac = compute(sv, lighting)
            harvest_mw = DERATED_MW * geo * frac
            harvest_mwh = harvest_mw * period / 60
            dod = (LOAD_MW * ecl_min / 60) / (BATTERY_WH * 1000) * 100
            soc = 100 - dod
            ok = harvest_mwh > LOAD_MW * period / 60 and soc >= 20
            print(f"{tag:6} {att:9} {period:7.1f} {frac*100:7.1f}% {geo:6.3f} "
                  f"{harvest_mw:8.0f}  {harvest_mwh:8.0f}  {dod:6.2f}% {soc:7.1f}%  "
                  f"{'YES' if ok else 'NO'}")
            if worst is None or harvest_mw < worst[2]:
                worst = (tag, att, harvest_mw)

    print(f"\nDesign driver: {worst[0]} {worst[1]} — {worst[2]:.0f} mW orbit-average")
    print(f"Sustainable continuous load before the worst case fails: "
          f"{worst[2]:.0f} mW")


if __name__ == "__main__":
    sys.exit(main())
