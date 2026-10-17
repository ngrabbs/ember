# Stored-image detector second pass — 2026-10-17

This is a development comparison on the same 107 selected triplets: 76 visually
labeled FIRE and 31 NO_FIRE. No images were added, relabeled or dropped during
this pass. The 30 previously excluded uncertain triplets remain excluded.
All outcomes, including UNKNOWNs, are retained. These images were also used for
configuration selection; there is no independent holdout or operational accuracy
claim.

## Changes and experiment sequence

1. The original conservative Pi run found 33/76 fire triplets, missed 10 and
   returned UNKNOWN for 33. Negatives produced 30 NO_FIRE and one UNKNOWN.
   Most unavailable results came from registration, especially dim frames.
2. Stretch each image's 1st–99th percentile range into a separate matching copy
   before CLAHE/ORB. Leave the measured intensities untouched. Compare 2000 and
   4000 features while retaining all existing registration quality gates.
3. Explore a small grid of K/excess/area thresholds on the Mac. The initial
   4000-feature profile with K=0.5, excess=5, area=16, guard=2 produced 68 fire
   detections, six misses, two UNKNOWNs and no negative false alarms there.
4. Run that profile on the Pi. It produced 69 fire detections, five misses,
   two UNKNOWNs and **four negative false alarms**. Cross-platform feature fits
   differ; the Mac's zero-false-alarm count did not reproduce on the target.
5. Sweep reference-neighborhood guard radii 2/3/4, absolute excess 3/5/7.5 and
   areas 8/16 at fixed K=0.5 on both hosts. Retain all 18 configurations and use
   the Pi results to select a second-pass development profile. Favor zero
   observed negative false alarms on both hosts, then more Pi fire detections.

The full local initial exploration (three matching configurations × twelve
threshold combinations) is summarized in `exploration.json`. Its scratch
harness wrapped the original aligner; the subsequent reports use the implemented
`normalized_orb_homography` mode. `initial-profile.json` preserves the first
candidate even after the shipping development profile changes. The initial
Mac/Pi evaluations and complete guard sweeps retain the unfavorable outcomes.

No detector interface or spectral formula changed. Pipeline version is 0.2.0;
algorithm remains `spectral_guarded_v1`, with its existing configurable radius.
The CAN daemon's version is separate. The new mode records transform matrices
and actual percentile intervals. Inputs/calibration/config/code hashes and
Python/NumPy/OpenCV versions identify each run.

## Selected profile

The highest Pi detection count among settings with no observed negative false
alarms on either host uses **K=0.5, excess=7.5, area=16, guard=2**. These are the
original conservative detector settings. Matching normalization and the larger
feature cap provide the improvement; widening the guard or lowering thresholds
did not improve this selection criterion. This is not a claim that zero false
alarms is a validated operating point.

| Host/profile | Fire detected | Fire missed | Fire UNKNOWN | Negative false alarm | Negative correct | Negative UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|
| Previous Pi conservative | 33 | 10 | 33 | 0 | 30 | 1 |
| Initial Pi candidate | 69 | 5 | 2 | 4 | 27 | 0 |
| Selected Pi profile | 64 | 10 | 2 | 0 | 31 | 0 |
| Selected Mac profile | 62 | 12 | 2 | 0 | 31 | 0 |

The two Pi UNKNOWNs are `20261014_162837_756` (localized registration fit) and
`20261014_174904_481` (missing exposure). The Mac instead rejects
`20261014_163139_693` for a weak registration fit. Do not infer that these two platforms make
identical decisions because the total UNKNOWN counts match.

## Reproduce the guard sweep

From the repository root, with the selected fixture files and calibration:

```sh
python3 firmware/payload/tune_detector.py \
  --manifest /path/to/fixtures/manifest.json \
  --config system/payload/evidence/stored-detector-pass2-20261017/initial-profile.json \
  --calibration /path/to/correction_20261003.npz \
  --k 0.5 --excess 3 5 7.5 --area 8 16 --guard 2 3 4 \
  --output /tmp/ember-pass2-sweep.json
```

Run `detect.py` with `firmware/payload/config/stored-images-pass2.json` for
per-fixture results using the selected profile; omit `--fixture` to evaluate
all 107. Use a new output path. Raw images and calibration remain external to
Git. The Pi's development installation is `~/ember-detector-dev-20261017`, with
its own `.venv`, `fixtures/manifest.json` and `correction_20261003.npz`.

## Interpretation and remaining work

A FIRE decision is a scene-level classification. Visual inspection of initial and selected-profile
candidate overlays found some background-edge regions alongside real flame.
Zero false alarms on the 31 negative frames does not prove that every region
inside a positive frame is fire. Spatially annotated flames and a wider range of
negative scenes are needed to measure localization and false alarms properly.
Larger reference neighborhoods suppress some edge artifacts but also reduce
sensitivity to small or weak flames. In the selected Pi example
`pi-recovered-fire-example.json`, the large region at `[741, 430, 68, 68]`
corresponds to visible flame, while the 20-pixel region at `[298, 639, 10, 9]`
marks a background plate corner. The scene-level detection is correct, but
that smaller region is a localization false positive.
`pi-negative-example.json` records a negative that the initial candidate
incorrectly flagged; the selected thresholds reject it.

The new matching contrast improves alignment availability; it does not recover
lost sensor information or establish JPEG linearity, optical calibration
compatibility or gain. A failed fit and missing exposure still return UNKNOWN.
Do not copy alignment transforms between captures or weaken quality gates just
to force those cases into a binary result. The matcher must remain separate
from the measured intensities used in the spectral calculation.

The live CAN fire-check remains outside this offline evaluation. A bounded
worker and coordinated fixture/UNKNOWN result protocol are still needed before
command integration. No camera capture, CAN command or RF transmission was used
for the detector experiments.

## Final verification and timing

The selected profile was rerun independently through `detect.py` on both hosts;
its 107 decisions reproduce the corresponding sweep confusion counts. The
`*-selected-evaluation.json` files retain every fixture result. Module and
configuration hashes match the checked-in implementation/profile.

Pi processing median/p95/maximum were **1976/2092/2113 ms**.
The previous conservative Pi median was 1044 ms: improved registration costs
about twice as much processing time. These times cover loading, preparation
and inference, excluding interpreter startup and output/map writes. They are
observations, not deadline guarantees. Keep image work off the CAN receive loop.

The ground suite ran 84 tests: 81 passed and three skipped. All ten detector
tests passed separately on the Pi. They include dim translated texture,
featureless/unrelated inputs, matching-only normalization and malformed settings.
At the post-evaluation check both payload services were active; can0 was
ERROR-ACTIVE at 500 kbit/s with zero RX/TX errors and zero bus-off events.
