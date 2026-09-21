# L16 choke review

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


Reviewed 2026-09-09. No component value, MPN or footprint change applied.

The original manufacturer document `../../design/C18221300.pdf`, DDY rev A dated 2022-09-27, PDF page 5 (printed page 4 of 6), explicitly lists WI0805QD1R0MST-HF: 1 µH at 1 MHz, Q typical 10 at the listed test frequency, SRF typical 550 MHz, DCR 0.12 ohm max in a column also marked ±30%, typical Isat 1200 mA and Irms 1000 mA. Thus the earlier generic 200–400 MHz SRF assertion does not establish that this exact choke is capacitive at 435 MHz. The document does not establish production-minimum SRF or measured choke impedance at 435 MHz. Its low-frequency Q figure must not be extrapolated to UHF.

A documented 220 nH candidate is Coilcraft **0805HP-221XJRC**, 5% tolerance. The primary product table gives 930 MHz typical SRF, Q typical 75 at 250 MHz, 0.426 ohm maximum DCR and 0.50 A reference Irms for a 15 °C rise. The ideal reactance at 435 MHz is about 601 ohms; this is a calculation, not measured impedance. At a hypothetical 100 mA DC design current the DCR drop is at most 42.6 mV using the 25 °C figure. Typical SRF is not a guaranteed minimum, and this candidate does not meet the old plan's stated >1.5 GHz SRF target. Resolve that requirement using actual impedance/isolation and stability evidence before acceptance.

Primary sources (accessed 2026-09-09):
- https://www.coilcraft.com/en-us/products/rf/ceramic-core-chip-inductors/0805-%282012%29/0805hp/0805hp-221/
- https://www.coilcraft.com/getmedia/c30565bc-9cf5-4393-9380-6f782e4b4cd8/0805hp.pdf — document 1362, revised 04/11/22.

The installed L16 footprint has two 0.875 × 1.2 mm pads, with 2.125 mm center spacing, verified through native KiCad. It must not be treated as a validated drop-in land pattern for either part merely because both are called 0805. The Coilcraft drawing includes a recommended land pattern with 1.02, 1.12 and 1.98 mm dimensions; perform the complete drawing-view/pad audit and scratch render before assigning a replacement footprint. The existing DDY land pattern also needs comparison against the installed pads.

Acceptance remains open: choose exact part against the RF isolation requirement, validate its land pattern and ordering fields, apply coordinated schematic/PCB changes, then characterize gain, stability and insertion loss. No claim of flight or production qualification is made.

## Subsequent prototype implementation

The Coilcraft 0805HP-221XJRC candidate has now been applied for prototype testing, with an audited custom land pattern and matching schematic/PCB ordering fields. See `l16_footprint_acceptance.md`. This supersedes the earlier no-change status; the >1.5 GHz target and RF bench qualification remain open.
