#!/usr/bin/env python3
"""Analytical interlock candidate screening, not circuit acceptance."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rg_min = 220000 * (1 - .001) * (1 - 25e-6 * 65)
rg_max = 220000 * (1 + .001) * (1 + 25e-6 * 65)
rp_min = 10000 * (1 - .01) * (1 - 100e-6 * 65)
rp_max = 10000 * (1 + .01) * (1 + 100e-6 * 65)
ratio_min = rg_min / (rg_min + rp_max)
ratio_max = rg_max / (rg_max + rp_min)
result = {
    "status": "ANALYTICAL_CANDIDATE_ONLY; NO_NATIVE_BUILD_OR_DYNAMIC_ACCEPTANCE",
    "candidate": "SUD50P08-25L-E3; procurement/package acceptance open",
    "passive_network_ohm": {"Rgs": 220000, "Rpd": 10000},
    "resistance_corners_ohm": {"Rgs": [rg_min, rg_max], "Rpd": [rp_min, rp_max]},
    "unclamped_Vgs_magnitude_V": [
        {"common_source_V": v, "min_V": v * ratio_min, "max_V": v * ratio_max}
        for v in [4.5, 5, 8.4]
    ],
    "minimum_common_source_for_4p5V_guaranteed_drive_V": 4.5 / ratio_min,
    "ideal10V_clamp_sensitivity": [
        {"source_V": v, "Rpd_max_current_A": (v - 10) / rp_min,
         "Rpd_max_power_W": (v - 10) ** 2 / rp_min}
        for v in [32.164, 35, 60]
    ],
    "initial_Cgs_max_F": 100e-9 * 1.1 * 1.15,
    "Rgs_Cgs_tau_upper_initial_s": rg_max * 100e-9 * 1.1 * 1.15,
    "MOSFET_gate_charge_and_Miller_not_included_in_tau": True,
    "pair_conduction_sensitivities": [
        {"current_A": i, "pair_drop_at25C_V": i * .029 * 2,
         "pair_loss_at25C_W": i * i * .029 * 2,
         "pair_loss_at_assumed_2x_R_W": i * i * .029 * 4}
        for i in [2, 4, 6]
    ],
    "initially_uncharged_capacitor_energy_J": [
        {"capacitance_F": c, "voltage_V": v, "energy_J": .5 * c * v * v}
        for c in [102.6e-6, 150e-6, 1e-3] for v in [5, 8.4, 32.164]
    ],
    "limits": [
        "common-source voltage differs from cell voltage because all upstream drops matter",
        "4.5V drive resistance is a25C datasheet condition; doubled resistance is only a sensitivity",
        "10V clamp is an illustrative assumption, not a selected zener specification",
        "RC constant is not a guaranteed power-cutoff time or input-inrush bound",
        "capacitor energies are sizing cases, not actual selected total source banks or SOA proof",
        "four attempted SPICE runs did not converge and provide no accepted measurements",
    ],
}
(HERE / "analytical_results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ["status", "minimum_common_source_for_4p5V_guaranteed_drive_V", "Rgs_Cgs_tau_upper_initial_s"]}, indent=2))
