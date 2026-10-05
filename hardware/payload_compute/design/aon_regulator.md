# AON regulator prototype

> 2026-10-05: this accepted core is now captured in the separate
> [real prototype stage](../kicad/payload_compute_rev_next/README.md).
> The standalone evidence below remains the original study record.

2026-10-04. Standalone schematic implemented and exported through Konnect;
physical-map and connectivity checks pass. This is a prototype study, not
carrier integration or a fabrication release.

Use LMR36506R3RPER, fixed 3.3 V auto/PFM. Its nine-lead map and chosen prototype
lands are recorded in [package acceptance](aon_library_acceptance.md).
The [schematic and renders](validation/payload_aon_acceptance/README.md)
contain the actual circuit and closed-file readback evidence.

RT connects to internal VCC for nominal 1 MHz operation. This follows TI's
fixed-3.3-V typical application BOM, rather than the earlier adjustable-frequency
concept. VCC has a 1 µF bypass and no external load. BOOT has 100 nF to SW;
the output uses 15 µH and two nominal 22 µF capacitors. VOUT/BIAS senses the
3.3 V output. EN connects to the protected bootstrap input so the supervisor
can start independently of main-source admission. PGOOD is intentionally
unused; the separate TPS3808 supervisor establishes AON reset.

The input allocation is 10 µF / 50 V plus 100 nF / 50 V, with at least
4.7 µF effective bulk capacitance at the maximum qualified input. Output
capacitors are nominal 22 µF / 10 V each. The initial inductor allocation is
Isat ≥1.2 A and Irms ≥0.6 A. These are selection constraints, not accepted
passive MPNs; confirm bias derating, tolerances, DCR, temperature rise and
closed-loop current-limit behavior before selection.

The [AON DC budget](aon_supply_budget.py) remains 3.2505–3.3825 V, using TI's
−1.5%/+2.5% system-table allocation under its stated conditions. The G33 reset
supervisor has 57.7 mV static release margin. This does not cover dropout,
ripple, distribution loss, load steps or startup. Confirm the regulator starts
and supports the reduced USB bootstrap allocation before relying on it to
negotiate full power or release logic reset.

The external VDC boundary must already provide limited, protected,
reverse-isolated bootstrap power. This fixture contains no fuse, TVS, diode
OR, USB controller or flight isolation. PWR_FLAG symbols are ERC declarations,
not physical protection. Both prototype PCB fixtures contain only a package
placement, without converter routing or a production board outline.

Verification: seven exported nets, all nine IC pins accounted for, zero ERC
errors/warnings, zero disconnected pins/wires, shorts, orphans or symbol
overlaps. Exported SVG inspected after correcting the ground declaration's
field placement. Saved through Konnect's closed-file path with KiCad closed;
live PCB IPC save is not applicable. Reproduce with
`python3 design/validation/check_aon_study.py` from this hardware directory.

Remaining qualification: exact passives, bootstrap isolation/protection,
startup/dropout and full-temperature load regulation, PCB hot-loop placement,
thermal behavior and a common stencil for the RPE and RPW packages. RPE uses
a modified prototype land pattern and TI's 0.125 mm stencil example; the eFuse
example uses 0.100 mm. Those assembly choices must be reconciled.

Source: [TI LMR36506 datasheet](https://www.ti.com/lit/ds/symlink/lmr36506.pdf),
SNVSBB6C January 2026, pin table, frequency-selection table, typical application
table 8-3 and package drawings 4227033/B.
