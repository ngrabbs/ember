# Inhibit and Deployment Architecture

## Purpose

Define the stack's **power inhibit** and **deployment detect** strategy
so that the RBF pin, separation switches, post-ejection timer, and
RF/deployable enable logic are all consistent across the EPS and IHU
boards. This is a design-notes stub — the schematic implementation
will land in [`hardware/eps/design/altium_eps_schematic_guide.md`](../../hardware/eps/design/altium_eps_schematic_guide.md) once the
policy below is locked.

## TL;DR breadcrumb (read this first if you forgot where we left off)

> Locked 2026-04-15 during a design-discussion pass. Decisions below
> are for **v0.1 proto board only**. Flight version will replace the
> jumpers with real mechanical parts and invert the sensed polarity.

On the v0.1 proto board, everything that will eventually be a
mechanical safety interlock is just **a 1×2 pin header jumper**. All
three of them follow the same intuitive convention: **jumper
installed = safe/inhibited, jumper pulled = armed/running.** That is:

| Jumper | Installed (on the bench) | Pulled (for flight-mode testing) |
|---|---|---|
| `JP1` WDT Disable (IHU board) | Watchdog disabled | Watchdog enabled |
| `JP_RBF` RBF (EPS board) | Main bus killed | Main bus live |
| `JP_INH1` Deployment Inhibit #1 (EPS board) | TX + burn-wire inhibited | TX + burn-wire armed |
| `JP_INH2` Deployment Inhibit #2 (EPS board) | TX + burn-wire inhibited | TX + burn-wire armed |

Four separate jumpers, all "installed = safe." The two inhibit
jumpers are wired **in series** so either one alone keeps the
satellite inhibited — fail-safe.

**Important polarity note for future-you:** on the real flight
version, `JP_INH1` and `JP_INH2` get replaced by 2× normally-closed
separation microswitches. The P-POD rails hold those switches
mechanically **open** while stowed, and ejection lets them **close**.
So the real-switch convention is **open = inhibited, closed = armed**
— the *electrical inverse* of the proto jumper (where installed =
closed = inhibited). The net name and the "inhibited vs armed"
*meaning* stay the same; only the drive polarity flips. When we swap
the jumper for real switches, expect a small rewire: instead of the
jumper shorting the inhibit net to the "inhibited" rail, the
switches will sit in series with a pull-up and short the net to GND
when closed. Same `DEPLOY_DETECT` net, inverted sense.

Same thing for `JP_RBF`: the flight version is a physical pull-pin
that opens a contact (not a closeable header), but the convention
"installed = safe, pulled = armed" is preserved from proto to flight
without a polarity flip, since the pull-pin and the jumper both
*open the circuit when removed*.

The IHU `JP1` jumper is unchanged from its original spec — it is a
WDT-disable jumper, **not** an RBF. The earlier "(RBF)" label was
misleading and has been removed (see task, Section C of the IHU
schematic doc). Reserve the term "RBF" for the EPS `JP_RBF` pin
only.

**What still needs to happen before flight** (not v0.1 proto):

1. Pick a deployer (P-POD / NLAS / ISIPOD). Drives switch-face
   choice and RBF access-window location.
2. Pick real separation-switch parts (Omron D2F candidate) and get
   mechanical team to place them.
3. Replace `JP_INH1` / `JP_INH2` with the real switch pair, flip the
   drive polarity as noted above.
4. Replace `JP_RBF` with a real pull-pin mechanism in the chassis.
5. Confirm with launch provider / faculty advisor whether the
   second hardware inhibit (`JP_INH2` → second switch pair) counts
   toward CDS §3.2's "three independent inhibits" requirement or
   whether a third firmware arm is also needed.

## Background — why this is its own doc

The existing IHU `JP1` labeled "Disable Watchdog (RBF)" is **not** a
CDS-compliant Remove-Before-Flight pin. It is a bench/flight mode
jumper for the STWD100 watchdog — useful during bring-up, but it does
not cut bus power and is not what a range-safety reviewer means by
"RBF." We need a real RBF pin *and* separation switches, both living
on the EPS, and we need to stop overloading the term "RBF" for the
WDT jumper.

## Regulatory / standards drivers

- **Cal Poly CubeSat Design Specification (CDS) Rev. 14**
  - §3.2 (electrical): RBF pin required; shall cut all power to the
    satellite except the charging circuit while installed.
  - §3.2: at least **three independent deployment inhibits** on the
    RF transmitter path. Typically realized as RBF + 2× separation
    switches in series.
  - §3.3 (operational): **30-minute** post-ejection wait before any
    RF transmission. **45-minute** wait before any deployable
    actuation (antennas, solar panels).
- **FCC Part 97** (amateur license, if we go that path): also
  requires the post-ejection silent period.
- **ITU coordination**: same requirement, different paperwork.

## Required functional blocks

1. **RBF pin (EPS)**
   - Physical pin on the +Z or -Z face (TBD — depends on P-POD access
     window location once we pick a deployer).
   - Series in the battery → main bus path. Pin inserted = bus dead,
     charge path still alive so the battery can top off during
     pre-launch integration. Pin pulled = bus live.
   - Implementation option A: mechanical — pin is literally a jumper
     that opens the batt→bus FET gate drive.
   - Implementation option B: electrical — RBF pin grounds a signal
     that holds the main load switch disabled.
   - **Decision needed:** A vs B. A is simpler and harder to defeat
     by firmware bugs; B gives us telemetry (EPS can see RBF state).

2. **Separation switches (EPS)**
   - **2× redundant** normally-closed microswitches in series.
     "Normally closed" here means: while the satellite is inside the
     P-POD, the rails push the plungers down and the switches are
     **held open**. When the satellite is ejected, springs close the
     switches.
   - Series wiring: both switches must close before the deployment
     detect net is asserted — this is the fail-safe direction. If
     either switch sticks open, the satellite stays in "still in
     P-POD" state and will not transmit or deploy. Safer to stay
     quiet than to transmit while still in the tube.
   - **Switch choice candidates:** Omron D2F-01L (sealed, 5M cycles,
     widely space-flown), Honeywell ZX series (bigger, more robust),
     or a custom gold-contact reed. Vacuum + vibe rating is the
     filter.
   - Mounting: on the -Z rail face (opposite the antenna) so P-POD
     rail contact is clean. Mechanical team owns the bracket; EPS
     owns the circuit.

3. **Deployment detect + debounce (EPS)**
   - Series switch pair → pull-up → RC debounce → Schmitt buffer
     (74LVC1G17) → `DEPLOY_DETECT` net to EPS MCU GPIO.
   - Debounce RC target: ~10 ms. Launch vibration will chatter the
     switches and we do not want to start the 30-min timer on a
     bounce.
   - `DEPLOY_DETECT` is also routed to the IHU via CSKB as
     `DEPLOY_DETECT_FC` (H1 TBD pin) so the IHU can log the
     transition for telemetry.

4. **Post-ejection timer (EPS firmware)**
   - On first rising edge of `DEPLOY_DETECT`, EPS MCU latches the
     transition into MRAM with a timestamp (monotonic uptime
     counter; no RTC).
   - Timer 1: **T+30 min** → assert `COMMS_TX_ENABLE` (gates the
     +5V rail to the comms board PA, or gates a digital enable to
     the comms MCU — TBD).
   - Timer 2: **T+45 min** → assert `BURN_ENABLE` (gates the burn
     wire load switch for antenna deployment).
   - Timers must survive reset: if EPS reboots mid-inhibit, it reads
     the latched transition time from MRAM and resumes counting
     from the original T0, not from the reboot. This is the
     non-trivial part — needs careful MRAM layout.
   - If the switches *reopen* after transition (e.g., mechanical
     glitch), **do not** cancel the timer. Once we commit to
     "deployed," we stay deployed. CDS is silent on this but every
     flown CubeSat I've seen locks the transition.

5. **Three-inhibit chain on the TX path (comms)**
   - CDS wants three independent inhibits between battery and RF.
     Proposed chain:
     1. RBF pin (cuts bus → whole satellite dead)
     2. Deployment detect via separation switches (cuts
        `COMMS_TX_ENABLE` → no +5V to PA)
     3. Firmware-controlled `COMMS_PA_EN` GPIO on the comms MCU
        (software arm after the 30-min timer expires and a ground
        command is received, TBD)
   - Inhibit 3 is debatable — some teams count the comms MCU's own
     boot-up sequence as the third inhibit. Decision needed with
     faculty advisor / launch provider before locking.

## Decisions locked for v0.1 proto (2026-04-15)

- [x] **RBF implementation:** mechanical jumper only (`JP_RBF`,
      1×2 header on the EPS board). Simpler and impossible to
      defeat with a firmware bug. No telemetry of RBF state on
      v0.1 — we accept that tradeoff for the proto. Option B
      (electrical with telemetry) can come back in a flight spin
      if we want to see the RBF state in EPS housekeeping.
- [x] **Third TX inhibit:** second hardware latch, realized as a
      second jumper (`JP_INH2`) on v0.1. Not a firmware arm. This
      gives us two hardware inhibits in series on the proto, which
      maps cleanly to 2× series separation switches on flight.
      Whether CDS §3.2's "three independent inhibits" counts
      RBF + 2× switches as three, or wants an additional firmware
      arm on top, is still open (see below) but does not block
      the proto layout — jumpers are cheap to add.
- [x] **IHU `JP1` label:** drop "(RBF)" everywhere. Rename to
      "WDT Disable (Bench)." Reserve "RBF" for the EPS-side
      `JP_RBF` only. (Tracked as a separate edit pass on the IHU
      schematic doc.)

## Still open (does not block v0.1 proto)

- [ ] **Deployer selection** — P-POD (Cal Poly), NLAS (NanoRacks),
      ISIPOD (ISIS), something else? Drives switch-face choice,
      rail geometry, RBF access-window location, and mechanical
      bracket design. Deferred — we do not need a deployer picked
      to lay out the proto board, since the proto uses jumpers.
- [ ] **Real separation switch part** — Omron D2F-01L is the
      leading candidate, but the filter is vacuum rating + vibe
      survival + low-current contact resistance. Decide during
      flight spin, not v0.1 proto.
- [ ] **CDS three-inhibit interpretation** — is RBF + 2× series
      switches enough, or does the launch provider want a third
      firmware arm too? Confirm with faculty advisor / launch
      provider before flight spin.
- [ ] **CSKB pin for `DEPLOY_DETECT_FC`** — when we wire the EPS
      deployment detect net to the IHU for telemetry, which H1 pin
      does it land on? Open USER pin on H1 is probably cleanest.
      Add to [`system/interfaces/cskb_pinmap.md`](../../system/interfaces/cskb_pinmap.md) when chosen. Not
      needed for v0.1 proto if the IHU just polls EPS over I2C for
      deployment state instead.
- [ ] **MRAM layout for latched deployment state + T0 timestamp**
      — needs to coexist with the existing EPS uptime counter and
      any other non-volatile state. Firmware concern, not
      schematic-blocking.

## References

- Cal Poly CDS Rev. 14 (PDF; not in repo — fetch from
  cubesat.org/resources before locking policy).
- AMSAT RT-IHU deployment sequence notes (see the
  `primary_power.kicad_sch` in the RT-IHU repo for how they wire
  their separation switches — they use a single-switch approach,
  which is less conservative than CDS recommends).
- [`hardware/ihu/design/altium_ihu_schematic.md`](../../hardware/ihu/design/altium_ihu_schematic.md)
  Section C — current WDT-disable jumper (JP1), to be re-labeled.
- [`hardware/eps/design/altium_eps_schematic_guide.md`](../../hardware/eps/design/altium_eps_schematic_guide.md) — target location
  for the new RBF + separation switch + timer block once policy
  is locked.
