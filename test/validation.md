# Testing and Validation Plan

Detailed RF validation procedures are tracked in:

- [`test/rf/tx_validation.md`](rf/tx_validation.md)
- [`test/rf/rx_validation.md`](rf/rx_validation.md)
- [`test/rf/spectral_analysis.md`](rf/spectral_analysis.md)

System-level integration artifacts are tracked in:

- [`system/integration/integration_plan.md`](../system/integration/integration_plan.md)
- [`system/integration/system_tests.md`](../system/integration/system_tests.md)

## Baseline Validation (Senior Design)

### Subsystem Bench Testing
- [ ] Power rail voltage/current draw validation
- [ ] Solar + battery charge curve testing
- [ ] Thermal dissipation and heat sink checks
- [ ] Battery overcharge and undervoltage protections

### Communications Board Testing (Primary Focus)
- [ ] Verify TX chain output and spectral cleanliness on SDR/spectrum analyzer
- [ ] Verify RX chain sensitivity and command decode under controlled input
- [ ] Confirm modulation timing, frame structure, and beacon cadence
- [ ] Confirm demodulated messages match onboard logs

### Integration Testing
- [ ] Full stack test (EPS + OBC + comms board + selected payload)
- [ ] Burn-in test: 24+ hour operation in enclosure
- [ ] Simulated eclipse/power-loss cycles
- [ ] Final launch configuration test (boot logic, safe mode)

### Environmental Testing (As Available)
- [ ] Thermal cycling chamber
- [ ] Vacuum chamber or bell jar test
- [ ] Vibration or shake test (DIY or lab partner)


## Debug and Telemetry Tooling
- [ ] Serial interface tools for log inspection
- [ ] RF sniffing tools (RTL-SDR, SDRplay)
- [ ] Log parser for CSV/JSON comparison vs ground truth
