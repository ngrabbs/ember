# RX Chain Bring-Up Test Plan

## Stage 1: Si5351A CLK1 (RX LO)

Completed as part of TX Stage 1. See `si5351a_bringup_log.md`.

- [x] CLK1 outputs 145.900 MHz at expected power level
- [x] Enable/disable control working

## Stage 2: SA612 Mixer

_To be filled in when mixer circuit is assembled._

- [ ] Verify LO injection from Si5351A CLK1
- [ ] Inject known 145.9 MHz + offset signal, verify baseband output
- [ ] Measure conversion gain/loss

## Stage 3: Baseband Filter and Amplifier

_To be filled in after mixer validation._

## Stage 4: ADC Capture and Demodulation

_To be filled in after analog chain validation._
