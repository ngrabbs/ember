# Rev B protection integration checkpoint

Development schematic integration based on converter checkpoint `b5b1c03`; target `hardware/eps/rev_b/eps_rev_b.kicad_pro`. Both protection sheets were rebuilt through Konnect as unique B children from the current authoritative `recovery_protection` root and attached `recovery_rail_final.kicad_sch`. The rejected unlinked `recovery_rail.kicad_sch` was not used. No PCB synchronization or historical study modification was performed.

## Electrical verification

Run `python3 hardware/eps/verification/rev_b/protection_integration/verify_protection_integration.py` from the repository root. `verified.json` records the result: 160 physical parts, 91 root nets, 68 functional nets; all 41 mapped protection endpoint sets (37 functional and four intentional NC sets) match. All previous 77 physical UUIDs and metadata are preserved, with the 56 previous endpoint sets preserved under the authorized three signal scope migrations. Eighteen historical source files and 69 prior evidence files remain unchanged.

Fresh full-hierarchy CLI ERC reports **16 errors, zero warnings**: the existing unconnected MCU pins remain visible. This is a graph/metadata integration pass, not an electrically complete EPS or production release.

`reference_crosswalk.csv` records 312 old-to-new instance rows, including cumulative omitted-instance dispositions. The protection rebuild retains 161 native instances and omits only duplicate flags #FLG172/#FLG173/#FLG202 and their isolated return symbol #PWR171. Seven legitimate protection flags remain, including the filtered REC5_BIAS flag. Existing SYS/ground/+3V3 fixtures are not duplicated.

The approved global interfaces are SRC_FAULT = R608.2/U100.3/U600.11, REC5_FAULT = R619.2/U100.14/U601.11, and REC5_RESET = R623.1/U100.13. Protector fault pullups remain single. All three actual nets are CONTROL. All 68 functional nets have intended class membership. Three unsupported-to-delete native patterns `/Controller/REC5_FAULT`, `/Controller/REC5_RESET`, `/Controller/SRC_FAULT` are explicitly proven unmatched; 71 patterns total have no unexpected current membership.

VIN_CHG is not joined to SYS_PWR_PERMITTED. 5V0_RECOVERY_REG feeds the rail barrier, and +5V exists only downstream of that barrier. `protection_endpoint_crosswalk.csv`, `prior_endpoint_crosswalk.csv`, `fields_readback.json`, XML exports and `rebuild_readback.json` provide the exact checks and physical pin/package readbacks. Blank-number paste apertures are distinguished from electrical pads in package checks.

## Actual rendered-sheet inspection

Seven full-page PNGs, the seven-page PDF and eleven detail PNGs show the saved native sheets. Full pages and details were opened and inspected; root independently inspected all pages/details and the refreshed source page/source_bias detail. The final SRC_BIAS power anchor was moved off the wire corner onto a dedicated stub; the associated legitimate flag received its own stub. Final exports and source views were refreshed after this presentation correction, with unchanged physical connectivity.

The two added sheets have 107 and 138 orthogonal 1.27 mm-grid wire segments, zero joined four-way junctions, and no pin anchors at wire branches. There is one source and five rail unconnected crossings, explicitly enumerated in `verified.json`; these have no junction dots or wire endpoints at their crossings.

## Open boundaries and qualification

SOLAR_PERMITTED is an external interlocked-solar development fixture; the physical RBF circuit and charger PowerPath are absent. VIN_CHG ends at the future charger interface. SYS_PWR_PERMITTED remains a separate external permitted-source fixture feeding both converters. Their 102.6 uF nominal shared input capacitance and simultaneous startup are not qualified by this integration.

Low-VCC LTC4364 feedback accuracy, hot MOSFET SOA, source-energy bounds, minimum effective inductance/capacitance, TVS/snubber/resistor/shunt pulse ratings, thermal behavior and physical fit remain open. SMBJ60A full-current clamp does not guarantee the 80 V MOSFET rating. The bounded transient fixtures do not establish general solar fault acceptance. Startup load admission, settling, reset qualification and cooldown requirements remain as documented in the protection design analysis. The 330 ohm rail bleeder contributes about 15 mA/76 mW and consumes load budget. Autonomous 3V3 overvoltage containment and independent CAN branch isolation remain absent. No bench, thermal, PCB or fabrication acceptance is claimed.

Policy/API limits remain explicit: S03 four-way-junction ERC severity cannot be persisted as Error through exposed tools; S11 custom-field presentation cannot be controlled; S04 root/standalone pagination metadata has API limits; S08 earlier reused custom-symbol review-marker coverage remains unresolved. Metadata queryback does not satisfy visible-field acceptance. Native settings were not hand patched.

`evidence_sha256.json` hashes the saved evidence files, excluding itself. Historical and prior-checkpoint manifests are independently verified by the script.
