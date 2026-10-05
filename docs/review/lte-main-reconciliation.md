# LTE/main reconciliation — October 5, 2026

[Review](README.md) · [Operator guides](../user/README.md)

Combines main `4e9775f` with the published LTE branch `80ed598` (including
telemetry-guide PR #8 and documentation PR #14). Main's EPS Rev B, payload,
paid transceiver and SDRB/UHF checkpoints are retained.

The IHU CAN source is retained byte-for-byte from main, including the opt-in
native EPS timer. The LTE branch's manual-only source does not replace it.
Both archived UHF byte-preservation attributes and LTE patch whitespace rules
are retained. Imported srsRAN template comment spacing and the archived modem
diagnostic retain their original bytes with explicit whitespace attributes. The operator guides now describe native cadence and the separate
telemetry-only UHF instance, with optional services still disabled at boot.

The original documentation audit and verification record remain dated evidence.
The portable inventory is refreshed for this combined checkout. Historical UHF
service snapshots retain their exact manifest-hashed bytes; their relative links
are checked against the maintained original runbook directory. Four transceiver
references to an unpublished local preview point to the release index instead.

## Combined verification

- Ground discovery: 45 tests on macOS and Linux, 44 passed and one explicitly
  skipped kernel virtual-CAN test (no interface supplied). Includes sanitizer-backed
  native timer, CAN framing, queue policy, actual host C endpoint and Walter FSM.
  [Linux transcript](evidence/lte-main-20261005/ground-linux.txt).
- UHF software/process supervision: all 23 unit tests passed on Linux using
  `python3 -m unittest test_binary_injector test_can_forward test_packet_radio
  test_repeater_probe test_stream_decoder test_supervisor -v` from `ground/uhf`.
  [Transcript](evidence/lte-main-20261005/uhf-linux.txt). The standalone GNU Radio
  flowgraph script `test_native_mix.py` was not rerun: GNU Radio is unavailable
  in these test runtimes. Unit tests do not open UHD devices.
- Both CAN Feather Release roles built with warnings-as-errors in the existing
  Linux development container; [SDK/compiler and UF2 hashes](evidence/lte-main-20261005/can-build.txt).
  These build hashes do not replace installed-image identities.
- All eight LTC4162 driver tests passed.
- Mixer core passed C++17 warnings-as-errors and address/undefined sanitizers.
- Four offline archived verifiers passed: native-autotelem, handheld-proof,
  both-uhf-antennas and supervision. These recheck saved evidence, not current RF.
- Documentation audit: zero missing local file links and zero unmatched fences;
  heading anchors and external URLs are outside this check. The two relative
  links in the manifest-hashed supervision snapshot resolve in their original
  `ground/uhf` context; its bytes were not changed.
- `git diff --check` passed. No protected KiCad source differs from pre-merge main.

Linux GCC exposed a signed-size comparison in Walter packet validation and two
misleading single-line loop layouts in test fixtures. Cast the packet length to
`size_t` and brace the loops; the existing behavioral tests then passed without
relaxing compiler warnings.
No live RF session, installed service change, firmware flash or CAD design edit
is part of this integration.
