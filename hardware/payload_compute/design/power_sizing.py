"""Reproduce preliminary payload power sizing; no hardware qualification implied.

Run with Python 3. Only the standard library is required. Values and limitations
are documented in power_component_sizing.md. Output goes to stdout as JSON.
"""

import itertools
import json
import math


def divider_window(top, bottom, threshold_min, threshold_max,
                   tolerance=0.001, leakage=0.1e-6):
    # At the sense node: Vin = Vthreshold*(1+Rt/Rb) + Ileak*Rt.
    values = [v * (1 + rt / rb) + leak * rt
              for rt, rb, v, leak in itertools.product(
                  [top * (1 - tolerance), top * (1 + tolerance)],
                  [bottom * (1 - tolerance), bottom * (1 + tolerance)],
                  [threshold_min, threshold_max], [-leakage, leakage])]
    return {"min_V": min(values), "max_V": max(values)}


def inductor(vin, vout, inductance, frequency, current):
    ripple = vout * (vin - vout) / (vin * inductance * frequency)
    return {"ripple_A_pp": ripple, "peak_A": current + ripple / 2,
            "rms_A": math.sqrt(current ** 2 + ripple ** 2 / 12)}


def calculate():
    thresholds = {}
    for name, top, bottom in [
        ("usb_uv", 56_200, 20_000), ("usb_ov", 250_000, 20_000),
        ("battery_uv", 374_000, 100_000),
        ("battery_ov", 665_000, 100_000),
    ]:
        thresholds[name] = {
            "top_ohm": top, "bottom_ohm": bottom,
            "rising": divider_window(top, bottom, 1.183, 1.223),
            "falling": divider_window(top, bottom, 1.076, 1.116),
        }
    lab = 15 + 3 * 3.3 * 0.25 + 2.5 + 1.5 + 0.35 + 0.25
    flight = lab - 2.5 - 1.5
    f_guard = 345_000 * 0.9  # Extra spread-spectrum guard, not a new TI limit.
    main = inductor(15.75, 5, 4.7e-6, f_guard, 6)
    main["minimum_effective_C_for_3A_step_0p2V_uF"] = 3 * 3 / (f_guard * 0.2) * 1e6
    main["minimum_rms_rating_at_80percent_A"] = main["rms_A"] / 0.8
    main["minimum_Isat_rating_from_9p6A_limit_at_80percent_A"] = 9.6 / 0.8
    return {
        "status": "preliminary calculations, not measured performance",
        "efuse_thresholds_0p1percent_resistors": thresholds,
        "power": {"lab_output_W": lab, "flight_output_W": flight,
                  "lab_6V_85percent_20percent_margin_A": lab * 1.2 / 0.85 / 6,
                  "flight_6V_85percent_A": flight / 0.85 / 6,
                  "lab_7W_mode_6V_85percent_20percent_margin_A":
                      (lab - 8) * 1.2 / 0.85 / 6},
        "usb_limit_screen_not_guaranteed": {
            "resistor_ohm": 1300,
            "nominal_A": 3334 / 1300,
            "assumed_min_A": 3334 / (1300 * 1.01) * 0.85,
            "assumed_max_A": 3334 / (1300 * 0.99) * 1.15},
        "usb_limit_advertised_10percent_accuracy_screen": {
            "resistor_ohm": 1300, "resistor_tolerance": 0.001,
            "nominal_A": 3334 / 1300,
            "min_A": 3334 / (1300 * 1.001) * 0.9,
            "max_A": 3334 / (1300 * 0.999) * 1.1,
            "lab_20percent_margin_at_14p25V_85percent_A": lab * 1.2 / (14.25 * 0.85)},
        "battery_750ohm_limit": {
            "min_A_with_0p1percent_R_screen": 3.960 / 1.001,
            "max_A_with_0p1percent_R_screen": 4.840 / 0.999},
        "main_5V_inductor": main,
        "aux_3p3V_inductor": inductor(15.75, 3.3, 6.8e-6, 500_000, 2),
        "aon_3p3V_inductor": inductor(15.75, 3.3, 33e-6, 400_000, 0.5),
        "nominal_feedback_V": {"main_10k_1p91k": 0.8 * (1 + 10 / 1.91),
                                  "aux_31p2k_10k": 0.8 * (1 + 31.2 / 10),
                                  "aon_100k_43p2k": 1 * (1 + 100 / 43.2)},
        "aon_frequency": {"ideal_400kHz_RT_kohm": 18286 / (400 ** 1.021),
                          "40p2kohm_nominal_kHz": (18286 / 40.2) ** (1 / 1.021)},
        "efuse_4p7nF_nominal_slew": {
            "V_per_ms": 2000 / 4700,
            "15V_ramp_ms": 15 / (2000 / 4700),
            "6V_ramp_ms": 6 / (2000 / 4700)},
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2))
