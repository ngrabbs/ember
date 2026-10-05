#!/usr/bin/env python3
"""Worst-case DC voltage budget for REF3425 + LM2903B proposal.

Budget limits are design requirements, not measurements or full hardware
qualification. In particular, the reference's assembly/aging reserve and the
buck's full-temperature output envelope require validation.
"""
from itertools import product
import json

REFERENCE_FRACTION = 0.002  # Allocated total, see precision_monitor.md.
RESISTOR_FRACTION = 0.003  # 0.1% initial + <=10 ppm/C over 165 C, rounded up.
OFFSET_V = 0.004  # LM2903B SOIC maximum over -40..125 C, Vs=5..36 V.
BIAS_A = 50e-9  # Magnitude bounded symmetrically for conservative screening.
SENSE_ERROR_V = 0.010  # Allocated module-referred sensing error, not IC spec.


def trip_range(top, bottom):
    values = [
        (reference + offset) * (1 + rt / rb) + bias * rt + sense_error
        for reference, offset, rt, rb, bias, sense_error in product(
            (2.5 * (1 - REFERENCE_FRACTION), 2.5 * (1 + REFERENCE_FRACTION)),
            (-OFFSET_V, OFFSET_V),
            (top * (1 - RESISTOR_FRACTION), top * (1 + RESISTOR_FRACTION)),
            (bottom * (1 - RESISTOR_FRACTION), bottom * (1 + RESISTOR_FRACTION)),
            (-BIAS_A, BIAS_A),
            (-SENSE_ERROR_V, SENSE_ERROR_V),
        )
    ]
    return [min(values), max(values)]


def main():
    uv = trip_range(9310, 10000)
    ov = trip_range(10700, 10000)
    steady = [4.91, 5.09]  # Required at the module, across qualified conditions.
    dynamic = [steady[0] - 0.020, steady[1] + 0.020]
    margins = {
        "UV_fault_above_module_min": uv[0] - 4.75,
        "OV_fault_below_module_max": 5.25 - ov[1],
        "healthy_dynamic_above_highest_UV": dynamic[0] - uv[1],
        "healthy_dynamic_below_lowest_OV": ov[0] - dynamic[1],
        "startup_steady_above_highest_UV": steady[0] - uv[1],
    }
    assert all(v > 0 for v in margins.values()), margins
    feedback = {
        "nominal_V": 0.8 * (1 + 10000 / 1910),
        "old_leakage_error_magnitude_V": 100e-9 * 100000,
        "new_leakage_error_magnitude_V": 100e-9 * 10000,
        "new_divider_current_A": (0.8 * (1 + 10000 / 1910)) / (10000 + 1910),
    }
    print(json.dumps({
        "status": "PASS for allocated DC budget; hardware qualification pending",
        "UV_fault_V": uv, "OV_fault_V": ov,
        "required_module_steady_V": steady,
        "required_module_dynamic_V": dynamic,
        "margins_V": margins,
        "main_feedback": feedback,
        "corners_per_threshold": 64,
    }, indent=2))


if __name__ == "__main__":
    main()
