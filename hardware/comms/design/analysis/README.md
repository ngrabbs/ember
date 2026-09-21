# RF analysis

[Design guide](../README.md) · [Qualification worksheet](../../bringup/rf_prototype_checklist.md)

**Screening models, not measured acceptance.** Keep the saved inputs, assumptions,
and source scripts with reported results. New disposable runs go in ignored `output/`.
The scripts require Python with NumPy; numerical work was not rerun during cleanup.

| Study | Inputs / implementation | Record |
|---|---|---|
| Ideal filters | `rf_filter_ideal.py` | [Earlier RF review](../../verification/rf_review_435mhz.md) |
| Routed-line filters | `rf_filter_screen.py`, `rf_filter_before.json`, `rf_filter_after.json` | [Review evidence](../../verification/evidence/rf_review_validation.json) |
| Manufacturer inductor model | `rf_filter_vendor.py`, `rf_vendor_scenarios.json` | [Model follow-up](rf_vendor_model_followup.md), [results](rf_vendor_model_validation.json) |
| Paired end-cap sensitivity | `rf_end_cap_sensitivity.py`, `rf_filter_after.json` | [Results](rf_end_cap_sensitivity.json) |
| U9 loaded-network dependencies | [Circuit screen](u9_circuit_screen.md) | [Stability samples](u9_stability_screen.json) |
| U9/mixer headroom | [Headroom study](u9_mixer_headroom.md) | [Calculations](u9_mixer_headroom.json) |
| U9 package and pad candidate | [Implementation preparation](u9_implementation_preparation.md) | [Pad calculation](u9_pad_nominal.json) |
| Antenna diode voltage | [Replacement candidates](../../bom/replacement_candidates.md) | [Calculations](rf_diode_voltage_limits.json) |

Example run from this directory:

```bash
python3 rf_filter_vendor.py rf_filter_after.json output/vendor
python3 rf_end_cap_sensitivity.py output/end-cap
```

Do not discard input snapshots as generated clutter: they define the geometry
used by these studies. Historical stock counts and component candidates need
revalidation before procurement or implementation.
