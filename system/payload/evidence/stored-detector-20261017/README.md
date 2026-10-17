# Stored-image detector development evidence — 2026-10-17

Corpus: 107 operator-selected triplets (76 visually labeled FIRE, 31 NO_FIRE).
The 30 uncertain captures remain excluded. These are development comparisons on
the same corpus used for threshold exploration, not independent validation.

| Profile | FIRE detected | FIRE missed | FIRE unknown | Negative false positive | Negative correct | Negative unknown |
|---|---:|---:|---:|---:|---:|---:|
| Basic spectral | 40 | 0 | 36 | 17 | 13 | 1 |
| Guarded, same thresholds | 37 | 3 | 36 | 3 | 27 | 1 |
| Guarded, conservative comparison | 32 | 8 | 36 | 0 | 30 | 1 |

Every evaluation JSON retains all 107 outcomes, including UNKNOWNs. Preparation
failed for 37 cases: weak/absent/poorly distributed registration features and
one retained case with missing exposure metadata. No implicit registration
fallback or inferred exposure is used. Full parameter sweeps retain the false
positive/miss tradeoffs rather than only the most favorable settings.

The conservative profile was selected on this same development corpus. Its zero
observed false positives do not establish a false-positive rate or acceptable
fire sensitivity. Dark/ambiguous scenes were excluded, input linearity/gain and
optical calibration compatibility remain unverified, and no held-out scene set
exists. Most remaining fire UNKNOWNs require better registration information.

Reference-host runs record implementation/config/manifest/calibration hashes and
NumPy/OpenCV versions in the evaluation summaries. Individual run records and
optional maps remain local, alongside the selected original files. Original image
bytes and the 16-MB reference calibration are not committed to this repository.

The live CAN responder remains unchanged: no image analysis was enabled by these
offline runs, and no CAN command or RF transmission was used for evaluation.

## Pi 4 run

The full conservative run on the target Pi produced 33 FIRE detections,
10 misses and 33 UNKNOWNs among the 76 labeled fire triplets. The 31 negative
triplets produced 30 NO_FIRE, one UNKNOWN and no FIRE. The archived
`pi-conservative-evaluation.json` retains all cases and hashes. ORB/RANSAC
outcomes vary with platform/build; the reference-host table is not substituted
for target results.

Per-case processing median was 1054 ms, p95 1294 ms and maximum 4510 ms.
These include fixture loading/preparation/inference but exclude initial Python
imports and output/map writes. The Pi was concurrently installing dependencies
and experiencing SD-card I/O contention, so these are observed development
measurements, not qualified deadline bounds. In particular the maximum exceeds
the existing three-second bench exchange timeout. Command integration needs a
bounded worker and coordinated admission/result timing, rather than putting
this synchronous pipeline in the current CAN handler. Six detector tests also
passed on the Pi using its isolated virtual environment.

A separate Pi example including imports and map/report writes took 1943 ms from
Python entry and peaked at 143780 KiB RSS (about 140 MiB). The numerical result
and resource measurements are recorded in `pi-example-result.json` and
`pi-resource-usage.json`. These are single-run observations, not upper bounds.
The live responder stayed active; CAN RX/TX error counters remained zero at the
post-evaluation check.

The repeat at detector checkpoint `2be15b4` retained exactly the same 107 decisions.
Its implementation hash matches the detector modules at that commit. Subsequent
integer-type configuration validation changes do not change these profiles or
the numerical detector; their tests are run separately. Its per-case median/p95/maximum were
1044/1287/1347 ms; the earlier 4510-ms observation is retained above.
