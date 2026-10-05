# Communications Git checkpoint — October 5, 2026

Scope: existing local SocketCAN adapter, UHF framing/decoder/injection and
supervision tools, automatic IHU bench telemetry, relevant tests, dedicated
communications runbooks and October 3 evidence. No payload files or pending
shared documentation edits are included. This reconciliation did not change
radio behavior, flash firmware, operate hardware, or start installed services.

## Current verification

Tests were rerun from a clean materialization of the staged Git index:

- Ground/firmware unittest discovery: 45 tests, 44 passed, one Linux virtual-CAN
  test skipped because no explicitly supplied virtual interface is available.
  Includes the C automatic-telemetry policy test with address/UB sanitizers.
- Portable UHF tests: all 16 passed, using isolated Python 3.14 / NumPy 2.5.3.
- C++ headroom core: compiled with warnings-as-errors and address/UB sanitizers;
  transparency, phase, amplitude bounds and nonfinite-input checks passed.
- Archived native automatic telemetry, handheld proof and both-UHF-antennas
  verification scripts: each exited 0 against the staged evidence snapshot.
  These are offline consistency checks, not new hardware tests. The latter
  retains its failed tone-forwarding gate; handheld observations are distinct.

The first broad UHF discovery attempt on macOS failed because NumPy was absent,
GNU Radio is unavailable, and Linux supervisor preexec/process-death semantics
are unsupported. NumPy was installed into a local disposable virtual environment;
portable suites then passed. Linux supervisor, kernel CAN filtering and GNU Radio
integration were not requalified here. No new Pico target build was performed;
prior build/flash evidence is retained as historical evidence, not a current build.

## Evidence completeness and boundaries

The repository's generic ignore rules hide `.log` and `.raw` files. This
checkpoint explicitly includes 108 small archived communications evidence files
needed by the saved verification scripts; Python caches and build outputs remain
excluded. Script recomputation was performed on a disposable snapshot so the
original archived result files remain unchanged.

The branch is based on the existing LTE/CAN bench work and should be reviewed
against `feature/lte-m-bench`. It does not imply that those prerequisite commits
have been merged to main. Shared firmware/ground README edits remain assigned
to documentation work; dedicated new SDRB/UHF runbooks are included here.
