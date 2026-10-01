# TX qualification plan

[Bring-up guide](README.md) · [TX design](../design/tx_chain.md)

**Planned checks, not completed results.** Use the [prototype worksheet](rf_prototype_checklist.md)
for instrument limits, calibration, configuration, and acceptance budgets.

| Stage | Check |
|---|---|
| Power | Current-limited supply, correct rails and amplifier bias, no unexpected heating |
| Clock/control | Si5351A communication; CLK0 near 145.67 MHz; TX disabled at reset |
| Modulation/tripler | XOR swing and BPSK behavior; tripler fundamental and unwanted products |
| Filters/amplifier | Passive loss/matching, U8 gain, bias isolation and stability |
| Shared antenna | Correct switch state, settling, path loss, and inactive RX exposure |
| Full TX | Calibrated antenna power, occupied bandwidth and spurs against agreed limits |

Record actual output and maximum allowed mismatch before approving D15.
The selected design retains ADL5602; older simulation power estimates and
compression ratings are not guaranteed antenna-output limits.

Save raw measurements with the board revision and settings. Recheck native
connectivity and design rules after hardware changes. Historical clock/tripler
bench methods are available under [history](history/README.md).
