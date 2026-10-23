#!/usr/bin/env python3
"""Offline LTC4162 divider checks; no hardware access or register writes.

Nominal 103AT data: Semitec AT catalog pp.12-13 (manufacturer PDF).
Tolerance envelope is an engineering sensitivity, not a replacement for a
manufacturer guaranteed R/T tolerance table or ADC error specification.
"""
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPAN = 18191 * 1.2
RT = [(-50, 329500), (-40, 188500), (-30, 111300), (-20, 67770),
      (-10, 42470), (0, 27280), (10, 17960), (20, 12090), (25, 10000),
      (30, 8313), (40, 5827), (50, 4160), (60, 3020), (70, 2228),
      (80, 1668), (85, 1451), (90, 1266), (100, 973.1), (110, 757.6)]


def resistance(t):
    """Interpolate log R against reciprocal kelvin; no extrapolation."""
    for (ta, ra), (tb, rb) in zip(RT, RT[1:]):
        if ta <= t <= tb:
            f = (1 / (t + 273.15) - 1 / (ta + 273.15)) / (
                1 / (tb + 273.15) - 1 / (ta + 273.15))
            return math.exp(math.log(ra) + f * math.log(rb / ra))
    raise ValueError(t)


def code(r, bias=10000):
    return SPAN * r / (r + bias)


def decode_r(c, bias=10000):
    if not 0 < c < SPAN:
        raise ValueError("Open/short/out-of-domain code must not become temperature")
    return bias * c / (SPAN - c)


def trip_temperature(c, r25_scale=1, beta_scale=1, bias_scale=1,
                     adc_gain=1, adc_offset_ratio=0):
    actual_ratio = (c / SPAN - adc_offset_ratio) / adc_gain
    target = decode_r(actual_ratio * SPAN, 10000 * bias_scale)
    lo, hi = RT[0][0], RT[-1][0]
    for _ in range(70):
        t = (lo + hi) / 2
        r = resistance(t) * r25_scale * math.exp(
            3435 * (beta_scale - 1) * (1 / (t + 273.15) - 1 / 298.15))
        if r > target:
            lo = t
        else:
            hi = t
    return (lo + hi) / 2


def main():
    # Independent checks against ADI Table 6, not just inverse round-trips.
    adi = [(16117, 28215), (14113, 18290), (7970, 5751),
           (7112, 4832), (6325, 4080), (4970, 2948)]
    max_error = max(abs(decode_r(c) / r - 1) for c, r in adi)
    assert max_error < .001
    assert code(0) == 0 and abs(code(10000) - 10914.6) < 1e-6
    assert code(1e15) > 21829
    assert code(resistance(0)) > code(resistance(25)) > code(resistance(60))
    for invalid in [0, -1, SPAN, 32767]:
        try:
            decode_r(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(invalid)
    # 0.1% initial bias plus 25 ppm/K across electronics screening range.
    drift = 65 * 25e-6
    bias_bounds = [(1 - .001) * (1 - drift), (1 + .001) * (1 + drift)]
    corners = list(itertools.product([.99, 1.01], [.99, 1.01], bias_bounds))
    adc_corners = list(itertools.product([.99, 1.01], [-.001, .001]))
    proposed = []
    for t in [5, 10, 35, 37, 39, 40]:
        c = round(code(resistance(t)))
        ts = [trip_temperature(c, *v) for v in corners]
        with_adc = [trip_temperature(c, *v, *a)
                    for v in corners for a in adc_corners]
        proposed.append(dict(nominal_celsius=t, code=c,
                             sensitivity_trip_min_c=min(ts),
                             sensitivity_trip_max_c=max(ts),
                             with_assumed_adc_min_c=min(with_adc),
                             with_assumed_adc_max_c=max(with_adc)))
    default = []
    for c, _ in adi:
        ts = [trip_temperature(c, *v) for v in corners]
        default.append(dict(code=c, nominal_trip_c=trip_temperature(c),
                            sensitivity_trip_min_c=min(ts),
                            sensitivity_trip_max_c=max(ts)))
    rows = [dict(celsius=t, ohms=r, voltage=1.2*r/(r+10000),
                 adc_code=code(r)) for t, r in RT]
    result = dict(
        status="DEVELOPMENT_ANALYSIS_ONLY",
        sensor_candidate="Semitec 103AT-2; three separate devices",
        bias_candidate="TNPW060310K0BEEA; 10k 0.1% 25ppm/K",
        span_counts=SPAN, adi_table6_max_relative_resistance_error=max_error,
        nominal_table=rows, default_thresholds=default,
        provisional_5_to_40_celsius_profile=proposed,
        corners=len(corners),
        combined_adc_corners=len(corners) * len(adc_corners),
        adc_assumption="LTC4162 Rev A p5 ratio offset +/-0.001 and span +/-1%; "
                       "these rows lack full-temperature dot. Applying them at "
                       "other temperatures is sensitivity only, not a guarantee.",
        max_excitation_sensor_power_w=1.2**2/(4*10000),
        unqualified=["ADC gain/offset and excitation error", "R/T interpolation error",
                     "Guaranteed tolerance over temperature", "Mounting gradient and lag",
                     "Vacuum materials and self heating", "Cell charge limits",
                     "BMS coefficients, thresholds and actual fault response"])
    (HERE / "thermistor_results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["status", "corners",
          "adi_table6_max_relative_resistance_error", "default_thresholds",
          "provisional_5_to_40_celsius_profile"]}, indent=2))


if __name__ == "__main__":
    main()
