# SDRB integration PR against main — October 5, 2026

This materializes the SDRB checkpoint `40981a1` on current main, together with the
minimum missing native CAN bench, packet validation and additive Yamcs-instance
prerequisites. LTE radio code/experiments and unrelated payload, transceiver and
shared documentation work are excluded. Historical LTE references link to their
preserved branch rather than silently importing that branch.

Validation from this isolated tree:

- Ground discovery: 32 tests, 31 passed, virtual-CAN filter test skipped because
  no explicitly supplied virtual bus was configured. Includes native C timer
  policy under address/undefined-behavior sanitizers and C/Python CAN vectors.
- Portable UHF and Linux ownership/supervision: 23/23 tests passed on the Pi.
- C++ mixer core: warnings-as-errors and address/UB sanitizers passed on the Mac.
- Fresh Release builds of both IHU/COMMS CAN Feather targets in the existing
  m75q `amsat-dev-x86` environment, SDK `ee68c78`, GCC14.2.1, completed successfully.
  No board was flashed. These new build hashes do not replace installed-image
  identities in historical evidence.
- Native automatic telemetry, HT/handheld, both-UHF-antennas and supervision
  archived checks pass offline. Failed antenna-tone/startup gates remain failures;
  this is evidence consistency checking, not a new RF experiment.

The initial test bundle lacked baseline USB firmware and a baseline EPS fixture.
Supplying those dependencies made ground discovery pass; the first transcript
is preserved. An archived copy of SERVICES.md had acquired a historical header
and corrected links after its hash was recorded. The exact original content was
recovered from the matching maintained runbook and restored without changing the
manifest. The later text remains separate as SERVICES.annotated.md. Its original
relative links reflect its historical location; use the maintained service guide
for current operation. After restoration supervision verification passed.

[result.json](result.json) records exact counts, source/tool/image identities,
corrections and limitations; transcripts are alongside it. Application source
matches the SDRB checkpoint. Changes to publication links and restoration of the
one archived runbook do not alter radio/firmware behavior. AMSAT's upstream
checkout was verified clean; no AMSAT PR or core/image changes are included.

Intermittent TX startup underrun/timing errors remain open. Current GNU Radio
runtime, virtual CAN kernel filtering and live RF were not requalified here;
prior dated hardware/runtime results remain distinct. Radio startup services
remain opt-in and disabled at boot.
