# JLCPCB live-stock audit — 2026-09-09

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


**All 32 existing valid BOM ordering codes now have live-stock checks. 31 show stock; U9 is preorder-only.** This covers the 98 placements carrying those codes. Twenty other purchasable placements still require ordering-field completion or part qualification. The three DNP headers and six bare test pads require no purchase for the current assembly configuration.

## Confirmed blockers and low quantities

| References | Exact JLC part | Live stock | Disposition |
|---|---|---:|---|
| U9 | PSA4-5043+ / C5240848 | **0** | Preorder-only; does not meet in-stock requirement. Konnect's catalogue incorrectly suggested 1,129 available. Exact-name search returns only this entry. |
| D15 | Nexperia PESD5V0F1BRLDYL / C552549 | **0** | Preorder-only; evaluate an electrically and mechanically suitable in-stock ESD part. Similar TECH PUBLIC result is not an approved replacement. |
| L12/L13/L19/L20/L21/L22/L23/L24 | 0402HP-10NXGRW / C40976557 | **19** | Eight per board, at most two boards before assembly allowance. |
| H3/H4 | Samtec ESQ-126-39-G-D / C7466599 | **5** | Two per board, at most two boards before assembly allowance. Preserve stack geometry. |
| R20/R21 | AF0402FR-0722KL / C4230864 | 61 | Quantity risk for larger builds. |
| L17/L18 | 0402HP-15NXJRW / C39750903 | 137 | Check build quantity. |
| R27/R33 | AC0402JR-0747KL / C144710 | 191 | Check build quantity. |

These are available counts at observation time, not reservations. Build quantity remains unanswered; no sufficient-quantity approval has been issued.

## Resolved sourcing candidates

| Function | Exact candidate / JLC code | Live stock |
|---|---|---:|
| J9 antenna connector | Molex 734151471 / C588477 | 7,537 |
| L16 tolerance variant | Coilcraft 0805HP-221XGRC / C40877572 | 255 |
| Better-stocked 10 nH candidate | Murata LQW15AN10NG00D / C90642 | 38,198 |
| 7.5 pF tuning candidate | Murata GJM1555C1H7R5BB01D / C497526 | 3,781 |
| 8.2 pF tuning candidate | Murata GJM1555C1H8R2BB01D / C161336 | 28,783 |
| Y2 ordering candidate | SI5351A-B-GTR / C504891 | 36,086 |
| U5 ordering candidate | Microchip MCP6022T-I/SN / C57639 | 17,659 |
| U10 mixer | Mini-Circuits ADE-1+ / C2942210 | 189 |
| U11 RF switch | pSemi PE4259-63 / C470892 | 6,753 |
| U12 regulator | TI TLV75530PDBVR / C507268 | 1,183 |
| U13 Schmitt buffer | TI SN74LVC1G17DBVR / C7836 | 5,936 |
| R35/R36/R37 | 0402WGF1002TCE / C25744 | 29,056,266 |
| C103/C104 | Samsung CL10B105KA8NNNC / C29936 | 1,411,022 |
| C102 | FH 0402CG101J500NT / C1546 | 4,286,915 |
| C83 | FH 0402CG102J500NT / C53547 | 296,945 |
| C105/C106 | Existing Samsung CL05B104KO5NNNC / C1525 | 35,351,941 |

The Molex listing omits the hyphen in 73415-1471. Check the manufacturer drawing against the existing MMCX footprint before assigning the field. L16's G tolerance variant and the Murata filter inductors require the previously identified electrical review. In particular, do not use the Coilcraft RF model for the Murata part. Capacitor voltage/DC-bias and RF requirements remain part of candidate approval.

## What changed and what remains

Completed the signed-in live catalogue audit and corrected the cached availability assumptions. No purchases, reservations, schematic changes or PCB changes were made. The worksheet contains a live-stock column for all existing coded parts.

Next implementation work is to qualify in-stock replacements for U9 and D15, verify the connector drawing and the remaining candidate specifications, then populate exact ordering fields through KiCad tools and rerun affected checks. The RF tuning proposal remains a test candidate. Stock availability alone does not qualify RF performance.

Evidence: browser-rendered JLCPCB search results, observed 2026-09-09 approximately 19:07–19:15 UTC, plus the preceding same-day live inductor/choke detail checks. Raw stock quantities are saved in `jlcpcb_live_stock.json`; the complete placement audit is `jlcpcb_bom_audit.csv`.

Relevant pages: [U9](https://jlcpcb.com/partdetail/MiniCircuits-PSA4_5043/C5240848), [stack headers](https://jlcpcb.com/partdetail/Samtec-ESQ_126_39_GD/C7466599), [Murata inductor candidate](https://jlcpcb.com/partdetail/MurataElectronics-LQW15AN10NG00D/C90642).
