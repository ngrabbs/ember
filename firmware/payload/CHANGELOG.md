# Payload changelog

[Current bench builds](../README.md#current-bench-builds) · [Payload guide](README.md)

| Date | Version | Change |
|---|---|---|
| 2026-11-15 | 0.8.0 | Adds selectable JPEG and RAW detector profiles, offline tuning, and profile reporting. |
| 2026-11-14 | 0.7.1 · `deeac88` | Publishes a new payload identity for the FULL telemetry release. |
| 2026-11-06 | 0.7.0 · `3e4d0b4` | Saves capture GPS evidence with fire-check results. |
| 2026-11-05 | 0.6.0–0.6.1 · `2ffff3b`, `c37fd71` | Consolidates fire-check settings, reads camera originals in place, and allows a 10-second fire-check budget. |
| 2026-11-01 | 0.5.0 · `2e0bac0` | Reports failed registration quality gates as explicit UNKNOWN results. |
| 2026-11-01 | 0.3.0–0.4.1 · `f4d3b19` through `2bc2915` | Adds opt-in camera triplets in 0.3.0, live spectral detection in 0.4.0, and saved-image evidence tied to the exact reply in 0.4.1. The 0.4.0 adapter reports UNKNOWN as error 11. |
| 2026-10-17 | 0.2.0 · `c35262e`, `0800b07` | Adds commanded fire checks with a static NO_FIRE stub. Adds offline stored-image detectors under the same version. |
| 2026-10-17 | 0.1.0 · `17d4f68` | Adds the boot-ready Pi CAN A responder with identity and status requests. |
