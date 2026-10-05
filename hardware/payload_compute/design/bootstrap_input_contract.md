# Bootstrap input and restart contract

2026-10-05. Requirements for the next captured bootstrap stage. Circuit and
package evidence belongs to the prototype project's stage record. These
requirements do not certify USB compliance or measured startup behavior.

## USB source boundary

The intended portable kit uses a qualified USB-C PD source and C-to-C cable,
with at least 500 mA available at initial 5 V attachment and the preferred
15 V / 3 A negotiated profile for full operation. The Type-C default-power
level for a USB2 sink is 500 mA in TI's Type-C documentation. No guarantee is
made for a legacy USB-A host limited to 100 mA before enumeration. The
power-only PD inlet is separate from Jetson's USB recovery/data connection.

Retain the 0.200 W regulated AON startup target; the previous 0.250 W ceiling
is a sensitivity case to qualify. CAN transceivers remain inactive during
reduced startup. The active 0.350 W AON allocation must not be assumed available
at the lowest bootstrap voltage and minimum current limit.

For TPS26600 with a 120 kΩ current-limit resistor, the datasheet's
steady overload allocation is 85–115 mA; short-circuit allocation is 80–120 mA.
The captured branch selects 118 kΩ ±1% so its upper resistance stays below
the recommended 120 kΩ maximum. Scaling the tabulated endpoints inversely
with resistance gives an inferred 85.6–118.1 mA overload and 80.6–123.3 mA
short range; this interpolation is not a separately guaranteed datasheet row
and needs bench verification.
Include resistor variation, quiescent current, programming-divider loads,
PD-controller consumption and transient behavior. Neither the nominal 100 mA
setting nor the maximum steady short limit is a universal peak current ceiling.
The internal fast-trip response has finite delay. The final exact settings and
corner results must be reproduced against the captured component values.

Budget the **whole receptacle's direct VBUS capacitance**, including the
PD controller, protection, bootstrap and future main path. An output slew
capacitor downstream of a switch does not limit charging of input capacitors
upstream of that switch. Do not copy the old admission fixture's 10 µF raw
input capacitor into the full USB inlet without checking this complete budget.
PD voltage changes/hard resets, source cable resistance and actual source
inrush behavior remain prototype tests.

## Three separate bootstrap feeds

Each USB, bench and stack feed has its own limiter and voltage qualification
before the common AON input. Main admissions are separate paths. AON power
must exist before the MCU chooses a source or negotiates/qualifies the full
operating profile. Bootstrap voltage thresholds must therefore allow initial
USB 5 V rather than inheriting the main USB path's roughly 13 V threshold.

TPS26600 supports native active OR with reverse blocking. Accept its exact
connection and reverse/leakage/dynamic limits before removing separate diodes.
Its RTN reference is **not system GND**; programming passives and thermal pad
return to their own branch's RTN, while the GND pin connects to system ground.
The thermal pad cannot be the sole RTN connection. Telemetry crossing from
this domain needs its own reverse-input and partial-power acceptance.

Reverse blocking has nonzero leakage. Check whether that leakage can energize
an absent source's sense circuitry or accumulate voltage on an unloaded rail.
A leakage allocation, bleed path or measurement is not a physical launch
inhibit. Flight isolation must cover both raw stack AON/main branches and
alternate feeds. Fuse/TVS coordination, capacitor fault ratings, wiring energy
and device failure behavior need the actual source/harness envelope; the IC's
60 V rating alone does not rate the whole board for 60 V.

## Complete AON loss and bench restart

The hardware source and run latches cannot retain fault/session history after
AON power disappears. USB hard reset or a brownout can therefore look like a
fresh bench attachment. A startup jumper alone cannot prevent repeated
automatic bench boot attempts after this event.

Reserve a persistent unclean-session marker in the supervisor's internal
flash journal or an equivalently validated mechanism. Set it before requesting
main power; clear it only after verified normal shutdown and rail discharge.
At boot, invalid/unclean records inhibit automatic payload startup, show the
power/fault indication and require an explicit fresh arm. In bench mode the
existing local button can provide that deliberate recovery action; in flight
IHU CAN arm supplies it. Exact journal endurance, interrupted-write behavior,
button semantics and tests belong to later supervisor firmware implementation.
No extra memory IC is implied by this requirement.

Clean initial attachment retains the accepted automatic bench boot/AP workflow.
Fault recovery must not produce an arm solely because voltage becomes valid
again. Prototype acceptance includes repeated PD resets/brownouts during SD
writes and power cycling after an unclean stop, not only steady power tests.

Sources: [TI Type-C guide](https://www.ti.com/lit/eb/slyy228/slyy228.pdf),
[TUSB320 current-mode table](https://www.ti.com/lit/ds/symlink/tusb320.pdf),
[TPS2660 datasheet](https://www.ti.com/lit/ds/symlink/tps2660.pdf), and
[STUSB4500 datasheet](https://www.st.com/resource/en/datasheet/stusb4500.pdf).
