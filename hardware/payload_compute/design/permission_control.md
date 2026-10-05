# IHU receiver and source permission design

2026-10-04. Bounded disposable circuit implemented and checked. NAND physical
pin-map acceptance is complete; carrier integration and physical timing remain
open. See [circuit evidence](validation/payload_permission_acceptance/README.md).

## Receiver

Use SN74LVC1G11DBVR as a non-inverting receiver, with two unused inputs
held at AON 3.3 V. PAYLOAD_EN enters through a proposed 100 Ω series
resistor; a 10 kΩ pulldown sits on the receiver side. Both resistor values
have a provisional 1% tolerance. The accepted contract is 3.3 V push-pull,
default low, with VOH ≥3.0 V and VOL ≤0.4 V at the payload connector.
This reduces the previous 1 kΩ series proposal to preserve edge rate.
No signal pull-up to payload AON is used.

LVC input requirements are VIH ≥2.0 V / VIL ≤0.8 V across VCC=3.0–3.6 V.
Using ±5 µA input leakage, resistor corners give received high ≥2.9692 V,
low ≤0.3966 V, and missing-drive voltage ≤50.5 mV. Input current is under
0.35 mA for a 3.3825 V asserted source in this resistor-only model. Allocate
an additional ground-offset budget before accepting these margins.

Inputs accept up to 5.5 V in specified operation; Ioff at VCC=0 limits
power-off leakage to ±10 µA. Neither statement defines the receiver output
during arbitrary ramps, negative transients, ESD events or a failed supply.
External default-low pull resistors and the reset interlock remain required.
Do not add a large RC filter to this ordinary CMOS receiver. The datasheet
requires input transition rate no slower than 10 ns/V at 3.3 V ±0.3 V.
A provisional 30 pF total receiver-side capacitance gives a 3.0 ns resistor
RC time constant. In an exponential-edge approximation, the RC contribution
at the 2.0 V high boundary is under 3.1 ns/V; driver slew and interconnect
response are additional. Scope the actual connector and IC-pin waveforms;
this RC calculation is not a measured edge guarantee. A noisy or slow IHU
output would require a separately qualified Schmitt receiver instead.

## Logic implementation

Retain the bench sampler's MODE_LOCKED and BENCH_LATCHED. Independent
upstream source-control circuitry provides LAB_SOURCE_SELECTED,
STACK_SOURCE_SELECTED and each branch's SOURCE_OK. SELECTED must describe
actual hardware admission, not an unverified MCU intention. Protection/path
switching, AON bootstrap and branch qualification are outside this block.

Proposed gate equations (NAND inputs tied high when unused):

```
U1 IHU_EN_RX = IHU_INPUT_PIN
U2 STACK_MODE = !BENCH_LATCHED
U3 LAB_DENY = !(BENCH_LATCHED & LAB_SOURCE_SELECTED & LAB_SOURCE_OK)
U4 STACK_BASE = STACK_MODE & STACK_SOURCE_SELECTED & STACK_SOURCE_OK
U5 STACK_DENY = !(STACK_BASE & IHU_EN_RX)
U6 BRANCH_PERMISSION = !(LAB_DENY & STACK_DENY)
U8 SELECTS_EXCLUSIVE = !(LAB_SOURCE_SELECTED & STACK_SOURCE_SELECTED)
U9 MODE_READY = MODE_LOCKED & AON_RESET_N & SELECTS_EXCLUSIVE
U7 MODE_PERMISSION = BRANCH_PERMISSION & MODE_READY
```

AND gates: SN74LVC1G11DBVR. NAND gates: proposed SN74LVC1G10DBVR.
U1–U9, the receiver resistors, input/output bias resistors and nine 100 nF
bypass capacitors are wired in the disposable schematic. The exported netlist
implements these equations. +3V3 in this study means the always-on domain.

R1 is 100 Ω / 1%; R2 is the receiver-side 10 kΩ / 1% pulldown.
R3–R8 bias BENCH_LATCHED, LAB_SOURCE_SELECTED, LAB_SOURCE_OK,
STACK_SOURCE_SELECTED, STACK_SOURCE_OK and MODE_LOCKED low; R10 biases
MODE_PERMISSION low. These are 10 kΩ loads on their eventual drivers.
R9 is intentionally omitted: AON_RESET_N is open drain with the separate
supervisor block's 10 kΩ pull-up. Another 10 kΩ pulldown would form a divider
and prevent a valid high. Reset fanout, leakage, edge rate and pull-up loading
still need checking with the complete connected carrier.

Both selections high denies permission in either mode. Neither selected
also denies permission through the branch gates. A valid bench selection
ignores IHU requests; a stack selection requires IHU high. In stack mode,
IHU low removes permission through hardware, independently of STM32 code.
The existing run latch clears on permission loss and still needs a fresh
qualified arm edge after recovery. These gates must not replace that latch.

Keep source admission separate from main-buck enable and module POWER_EN.
Gating input protection with downstream 5 V readiness would prevent startup.
Removing MODE_PERMISSION is an operating interlock; it is not proof that
source switches disconnect raw battery or that carrier rail energy decays.
All default-low/power-off behavior must be validated with the actual switches.

## Timing and pending validation

At -40 to 125°C and the respective datasheet load conditions, NAND delay
is at most 6.4 ns, AND delay 6.2 ns. The proposed IHU path includes the
receiver AND, two NAND gates and final AND: allocated gate delay 25.2 ns.
The existing run-latch study then adds its own downstream delays. Input
receiver edge crossing, board loading and rail energy are not included;
no system hard-kill time is established. Stable-input truth tables do not
prove hazard-free behavior when mode/source signals change concurrently.
Source changes must disable the main request and go through discharge/new
qualification, with no promised seamless hot swap.

Checks:

- `python3 design/permission_control_study.py`: 512 intent combinations,
  IHU loss/recovery through an ideal run latch, and eight receiver corners.
- `python3 design/validation/check_permission_study.py`: 20 exported nets,
  Boolean evaluation of the saved gate topology for 512 combinations, and
  six physical NAND leads joined to symbol and placed footprint pads.

Wire, pin, short, orphan and overlap checks report zero findings. Final render
was inspected, including label spacing and page boundaries. Direct ERC reports
one error (U9 pin 3 lacks the external supervisor driver) and two isolated-label
warnings (IHU_PAYLOAD_EN and AON_RESET_N). Those are declared study boundaries;
the study is not globally ERC-clean. Pulldowns can satisfy ERC's input-drive
heuristic, so other external drivers remain required despite no corresponding
ERC error. Power flags explicitly assume external AON power and ground.

The previous UI/IPC block cleared after the user closed KiCad. Konnect's
closed-board placement then succeeded; placed pads were read back and the
package render inspected against TI's DBV top view and land drawing.
All protected source changes used Konnect. Each closed-file mutation was
saved by the tool and verified through queries/exports; live `save_project`
is unavailable while KiCad is closed and no live changes were pending.

The disposable PCB contains only the package-validation footprint, not a
routed version of this circuit. Source admission/protection, switch behavior,
connector ESD, power-ramp timing and integration with the supervisor, mode
sampler and run latch remain open before carrier or fabrication acceptance.

## Sources

- [TI SN74LVC1G11](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf), SCES487I, input conditions and full-temperature switching table.
- [TI SN74LVC1G10](https://www.ti.com/lit/ds/symlink/sn74lvc1g10.pdf), SCES486E, top-view DBV pin map p1, input/leakage specifications pp3–4, switching table p5.
- [Accepted user interface and bench sampler](bench_mode.md).
