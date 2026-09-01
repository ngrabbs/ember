# K-Line Wildfire Detection

The physics of the detection method — why potassium, why these wavelengths,
what the narrowband channels measure, and how the index is formed — is
maintained in the payload instrument repository:

**[`koenig_wildfire/docs/k_line_primer.md`](https://github.com/ngrabbs/koenig_wildfire/blob/main/docs/k_line_primer.md)**

That document is the single source of truth. It is kept alongside the
instrument it describes so the optics, the filter set, and the explanation
change together.

## Why this file is a pointer and not a copy

An earlier copy of the primer lived here and described a **superseded filter
plan** — 762 / 766 / 770 nm, with two on-line channels and 762 nm as the
off-line reference. That scheme has been abandoned.

762 nm sits inside the **O₂ A-band** (roughly 759–771 nm), where reflected
sunlight is attenuated by atmospheric oxygen by an amount that varies with
path length, altitude, and viewing angle. A reference channel is supposed to
report what the continuum is doing; one whose own transmission moves with the
atmosphere injects a term that has nothing to do with fire.

The current plan is **750 / 770 / 780 nm** — one on-line channel on the
potassium doublet, two references placed outside the A-band on either side of
it. The measurement is the fractional excess of the on-line channel over the
continuum interpolated from the two references.

Keeping only one copy avoids a second document drifting back toward the old
numbers.
