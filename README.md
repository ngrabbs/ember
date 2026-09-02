# EMBER

**E**mission **M**onitoring for **B**urn **E**vent **R**ecognition — a CubeSat-class
wildfire detection instrument and its supporting ground segment, built as the
senior capstone project for the Mississippi State University ECE department.

---

## The mission

Wildfire in the southeastern United States is frequent, dispersed, and rural.
Mississippi recorded more than 2,500 wildfires across 51,000 acres in FY2024 —
roughly twenty acres apiece, which is small enough to fall through the gap in the
satellite coverage a state forestry agency can actually reach. Geostationary
instruments refresh every five minutes but at 2 km resolution, which reduces a
twenty-acre fire to a sub-pixel inference. Polar-orbiting instruments resolve
375 m but pass only a few times a day. Commercial constellations close that gap
and sell it under national-scale service contracts.

EMBER detects fire by **chemistry rather than heat**. Burning vegetation releases
neutral potassium, which emits a narrow doublet at 766.5 and 769.9 nm during the
flaming phase of combustion. Three narrowband channels image the same scene — one
centred on that emission, two either side as continuum references — and the excess
of the on-line channel over the interpolated continuum isolates the potassium
signature. Silicon detectors see those wavelengths uncooled, which removes the
cryogenic chain that governs the size, power, and cost of a thermal fire payload.

Imagery exceeds the downlink by orders of magnitude, so screening happens onboard:
the payload evaluates each observation, keeps a compact detection report — position,
time, confidence — and discards the frames. A half-duplex UHF link returns those
reports and accepts commands within the same pass.

**What EMBER does not claim.** A single satellite revisits less often than VIIRS.
There is no temperature retrieval, it is blind through thick cloud, industrial
flares are a known false-positive source, and the minimum detectable fire is
hectare-scale. The argument is not that it outperforms a constellation — it is
that it reaches useful resolution on hardware a public agency can own, task, and
inspect.

---

## Subsystems

| Subsystem | Responsibility |
|---|---|
| Electrical Power System | Solar input, Li-ion storage, MPPT charge control, regulated rail distribution |
| Command and Data Handling | Mode control, command authority, telemetry aggregation, subsystem supervision |
| Payload | Three-channel narrowband instrument and onboard detection processing |
| Communications | UHF flight radio and the ground station that receives it — one link, measured end to end |
| Command, Telemetry and Debug Interface | Operator-facing command path, telemetry decode, and bench debug access |

Boards interconnect over the Pumpkin **CubeSat Kit Bus (CSKB)** H1/H2 stack
headers. [`system/interfaces/cskb_pinmap.md`](system/interfaces/cskb_pinmap.md) is the single source of truth for pin
assignment across every board.

---

## The payload instrument

The narrowband instrument is developed in its own repository, where the optics,
capture software, calibration pipeline, and flight-test results live:

**[`koenig_wildfire`](https://github.com/ngrabbs/koenig_wildfire)** — three IMX296
global-shutter monochrome cameras behind narrowband filters, a capture daemon and
operator web interface on a Raspberry Pi, and the ground-side analysis chain
(flat-field → registration → K-index).

This repository covers the spacecraft that carries it: power, command and data
handling, the radio link, and system integration.

---

## Repository layout

| Path | Contents |
|---|---|
| `hardware/` | Per-board design documentation, bring-up procedures, fabrication releases, datasheets |
| `firmware/` | Embedded software — housekeeping unit (FreeRTOS on RP2040), comms, payload, shared |
| `rf/` | Filter, matching, and gain-stage design; simulations and measured results |
| `analysis/` | Orbit and access modelling, link budget, power budget, trade studies |
| `system/` | Board-to-board interfaces, bus pin maps, protocols, integration planning |
| `test/` | Validation procedures and recorded results |
| `docs/` | Architecture, research references, and supporting documentation |

KiCad projects are tracked, under `hardware/<board>/kicad/` — the KiCad file
formats are plain text, so schematics and layout diff and review like any other
source. Altium projects are **not** tracked: the formats are binary and the
project trees dwarf the design. For Altium boards this repository carries the
written design record, fabrication outputs, and measured results only. See
`hardware/conventions/` for the design rules every board is built to.

---

## Building the housekeeping firmware

```bash
git submodule update --init --recursive     # FreeRTOS kernel
cd firmware/ihu && mkdir -p build && cd build
cmake .. && make -j
# Result: build/src/ihu.uf2
```

Requires the Pico SDK (`PICO_SDK_PATH`) and `arm-none-eabi-gcc`. Full bring-up
notes are in [`firmware/ihu/README.md`](firmware/ihu/README.md).

---

## Status

Under active development. Fall semester covers design and proof of concept;
hardware build and integration follow in spring.

Open work is tracked in [`TODO.md`](TODO.md) — the current front on each
subsystem, plus anything not owned by a checklist inside the design docs.

---

## License

See `LICENSE`.
