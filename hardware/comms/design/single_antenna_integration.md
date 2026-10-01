# Single-antenna interface

[Design guide](README.md) · [Open work](../TODO.md)

**Documented design:** J9 is the only antenna connector; 437 MHz TX / 435 MHz RX,
half duplex. Earlier placement/routing logs are superseded by the
[recorded RF review](../verification/rf_review_435mhz.md).

J9 / ANT → C102 DC block → U11 common port; RF1 → TX_OUT; RF2 → RX_IN.
D15 provides shunt bidirectional antenna protection. C94/C55 are the branch filter
end capacitors. D15 replacement qualification remains open.

| Function | Selected part / connection |
|---|---|
| U11 switch | pSemi PE4259, 4259-63, SC-70-6 |
| U12 supply | TLV75530PDBVR, 3.0 V from +5V; EN tied to input |
| U13 buffer | SN74LVC1G17DBVR at +3V0; accepts the 3.3 V controller signal |
| Control | `TX_ACTIVE`, J6.14 / Pico GP10; GP22 remains spare |
| Defaults | R35/R36 pull-downs; low selects RX, high selects TX at valid supply |
| Supply capacitors | C103/C104: 1 µF 0603, selected 25 V parts; effective capacitance still needs qualification |

## Switching behavior

Stop TX drive → select path → wait for settling → enable TX only when supply
and system permissions allow. The existing **10 µs bench guard interval is a
starting point**, not a proven worst-case bound; the part's control-rate limit is
25 kHz. Do not assume a valid RX path during power-off or rail ramping.

## Acceptance still needed

Measure common-port tuning, path loss, inactive-port leakage, switching transients,
receiver exposure, and D15 voltage/mismatch margin. Verify J9's through-hole launch
and mechanical fit. Neither earlier DRC results nor package acceptance proves
RF performance or hot-switching suitability.

- [Switch component audit](../verification/components/rf_switch_pinmap.md)
- [Antenna protection audit](../verification/components/antenna_esd_pinmap.md)
- [Capacitor selection evidence](../bom/evidence/remaining_field_completion.md)
- [Prototype qualification worksheet](../bringup/rf_prototype_checklist.md)
