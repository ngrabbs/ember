# Transmit chain

[Design guide](README.md) · [Antenna interface](single_antenna_integration.md)

**Baseline: low-power 437 MHz BPSK, retaining ADL5602.**

Si5351A CLK0 (~145.67 MHz) → 74LVC1G86 XOR modulation → Q3 tripler →
TX preselector → U8 ADL5602 → TX output filter → U11 switch → J9.

Both UHF filters use the documented series end capacitors, coupled resonators,
and tuning values in the [RF review](../verification/rf_review_435mhz.md#filter-and-matching-findings).
The present 9.1 pF shunt values are baseline; 8.2/7.5 pF are measurement candidates.

- Q3/Q4 use the manufacturer-specific Hottech 2SC3356 mapping in the
  [component audit](../verification/components/rf_pinmap_audit.md).
- U8's RF output is also its bias node. Preserve its DC-block/bias arrangement;
  use the [package audit](../verification/components/u8_adl5602_pinmap.md).
- Do not treat the amplifier's compression capability or old simulated antenna
  power as a clean-output guarantee. Measure actual output with filter/switch losses.
- Verify XOR swing at the operating frequency, modulation shaping, tripler spurs,
  amplifier bias/thermal behavior, and complete TX spectrum.

Begin with the [TX test plan](../bringup/tx_test_plan.md); track remaining work in
[TODO](../TODO.md). Older BFR92A/Rev-A examples are historical, not replacement
instructions for this board.
