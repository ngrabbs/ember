# UCC33020RAQR approved construction checkpoint

2026-10-24, basis `4dcbfa579a6f4a95480a4b0501ea8fa6242b3072`. The [user-approved rules](../../../design/rev_b_bms_ucc33020_library_rules.md) were executed through Konnect. **Development physical map passes; the custom review marker remains.** No UCC circuit was placed in the integrated EPS and no real PCB synchronization occurred. Assembly, thermal, EMC and electrical startup/fault qualification remain open.

## Constructed identities and preserved sources

- Symbol: `Ember_Charger_BMS_Review:UCC33020RAQR_REVIEW`, one unit, all12 separate physical leads with datasheet-derived electrical types. EN/FLT is bidirectional, VINP/grounds power_in, SEL input, VCC power_out. No pin types were weakened for ERC.
- Footprint: `Ember_Charger_BMS_Review:TI_RAQ0012C_VSON12_5x4mm_CombLand_REVIEW`, exact approved decomposition. No central EP, mechanical contact, drill or3D model.
- New independent fixture: `fixture/ucc33020_check.kicad_pro/.kicad_sch/.kicad_pcb` and portable `sym-lib-table`/`fp-lib-table`. The main project's existing portable tables did not change.

`baseline.json` freezes **477 tracked files byte-for-byte**, including main EPS native sources, historical study/package fixtures and LT3014/UART/BMS evidence. The intentionally changed review-symbol library is excluded from that count. Separately, `library_before.txt` and the verifier prove its entire original byte prefix and every prior parsed symbol remain exact; exactly one new UCC symbol is appended. Its existing instances and historical embedded libraries are untouched. The exact protected-path guard permits only **seven paths**: the modified review-symbol library, one new footprint, and the five new fixture sources/tables. It compares against the recorded commit and works after commit; it is not a broad future-path allowance.

Preflight rechecked Konnect0.11.1/KiCad10.0.0, current config and registered libraries. There is no configured KiCadLib nickname; the226-library inventory includes official and portable project libraries. Fresh UCC33020 symbol and RAQ footprint searches returned zero. No global/vendor library was edited. Generic defaults were subordinate to the approved geometry/policy.

## Source and physical evidence

Authority is TI [SLUSFK4A Rev A May2025](https://www.ti.com/lit/ds/symlink/ucc33020.pdf), actual p4 top-view pin/functions and RAQ0012C drawing4230399/A01/2024, pp34–36. Source hashes/images and the previously inspected typical application/electrical limits remain frozen in [candidate evidence](../ucc33020_candidate/README.md). `physical_map.csv` has one row for every one of the12 physical contacts: pin1 upper left,1–6 down the left,7–12 up the right. The underside outline is not mistaken for the front footprint.

**Raw multiplicities are intentional:** 42 objects =14 F.Cu/F.Mask +14 blank F.Paste-only +14 blank F.Mask-only. Copper numbers1–12 appear once, with a second3 and9 for the respective comb spine. Twelve symbol leads describe **eight continuous copper regions**, six isolated contacts plus two three-contact ground combs. The paste and expanded mask unions also have eight regions. All28 non-electrical aperture objects are unnumbered. No duplicate was hidden by dictionary conversion.

Each tooth is0.60×0.30 mm with nominalR0.05; each spine0.30×1.60 mm. Expanded mask shapes add0.07 mm on every side withR0.12; their union includes the base numbered pads' F.Mask opening. The saved scratch board's default0.05 mm copper-pad mask margin is smaller than the explicit0.07 mm apertures. Separate mask-only objects do not introduce extra electrical pin numbers. The copper gap is4.2 mm; the mask gap is4.06 mm under this geometry. This alone does not establish system creepage, clearances or EMC.

The approved rectangle union lacks TI's internal concaveR0.05 fillets. The frozen proposal calculation at1 µm raster gives0.004248 mm² total symmetric-difference area across both combs, all differing samples within0.043 mm per coordinate of the sharp corners (0.052 mm conservative raster bound). Saved geometry is checked against those same approved rectangles/radii. This is a documented construction deviation; the footprint is **not claimed to have an exact TI copper/stencil outline**. Fab uses5×4 mm nominal body/chamfer, silk lies beyond maximum-bodyY, courtyard±3.10×±2.40 mm with0.05 mm stroke. No copper was added below the isolation gap.

## Saved and live instance verification

`symbol_query.json`, `footprint_query.json`, `instance_fields.json` and `instance_pins.json` are actual Konnect readbacks. The verifier additionally reads saved native library/embedded symbol definitions and every raw saved pad because live pad queries do not expose dimensions/radii/drills. It checks the complete12-pin map, all42 raw object counts/counters, positions, sizes, shapes, layers, radii, no-drill condition, union-region counts and complete metadata.

The exact new PCB was confirmed as the sole managed open board before mutation. An initial manually placed disposable footprint had no schematic identity; the sync dry run returned a non-mutating identity conflict. Only that new disposable instance was deleted through Konnect, then a fresh dry run/apply created the schematic-owned instance. It was moved to50/50 mm, saved via IPC and all42 pads read back in `live_after_save.json`. Primary3/4/5/6 resolve to GND; secondary9/10/11/12 to GND_BMS_RAW, including both duplicate spines. Aperture-only pads carry no net. No real EPS board was opened or synchronized.

The schematic grounds are actual downward symbols, wired with exposed pin stubs and six explicit T-junction dots; the two returns stay distinct. Four genuine unwired functional pins remain. The fixture is a package check, not an operating converter.

## Electrical and rendered gates are separate

Direct CLI `fixture.xml` proves one physical part,12 unique physical endpoints and six nets: two four-pin ground sets plus four unwired singletons. `erc.json` has **8 expected fixture errors,0 warnings**:4 unconnected pins,3 undriven power nets and1 undriven SEL input. No NC or source flags hide them. CLI logs retain host Fontconfig warnings separately; they are not ERC warnings or evidence of a circuit fault.

Actual opened/inspected views: `symbol.png` full B page; `symbol_detail.png`; `board_copper_detail.png` whole placed part with silk/courtyard; `board_fab_detail.png`; `board_paste_detail.png`; `board_mask_detail.png`; `board_mask_copper_detail.png`; `board_numbered_fab_detail.png`. Raw complete board SVGs and one-page `fixture.pdf` are retained. Pad1 key, row direction, both continuous ground combs, distinct-domain gap, eight paste/mask regions and expanded apertures agree with the physical contract. The numbered-fab view adds **query-derived numeric annotations** to the actual saved-board fab/courtyard export; those labels are not new native fab artwork. Default placed U1 text remains in the central gap; final layout text positioning and assembly visibility still require review.

The actual approved presentation alternative is a **bright-green review callout** reading `CUSTOM — REVIEW REQUIRED` and `[ Construction authorized: UCC33020RAQR review candidate ]`, plus a fixture-level isolation-divider annotation. The library body is not green. Exposed authoring cannot add library divider graphics or custom metadata defaults; complete MFG P/N/manufacturer/package/description/review fields were added to the saved instance through supported annotations. Future instances must explicitly preserve those fields and the review callout. No full S08/S11 library-default or field-styling pass is claimed.

The saved PCB editor was closed without a save/discard prompt. CUA close observation timed out; `board_closed.json` confirms requested_open=false and zero open boards. Post-close AS_UNHANDLED is expected. Project meta3 normalization is captured in final hashes. Locks/PRL/editor history/backups are not byte-frozen artifacts.

Run `verify_package.py` with the bundled Python runtime; `native_source_sha256.json` binds the seven final native paths to the export/readback checkpoint. `evidence_sha256.json` records final evidence bytes, excluding volatile editor files. Keep older verifiers historical; their guards intentionally reject later authorized library additions. No flight/assembly acceptance, real isolated-supply circuit selection or complete BMS gauging claim follows from this package gate.
