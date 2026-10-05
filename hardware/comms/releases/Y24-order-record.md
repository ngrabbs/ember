# Y24 purchased prototype order

Updated October 5, 2026 from the paid-order check on October 4 and the user's
October 5 vendor message. This record supplements, and does not alter, the
[October 4 export archive](review_20261004_1100/README.md).

## Identity and payment

- JLCPCB batch: `W2026100500220571`.
- PCB: `Y24-9381059A`; assembly: `SMT026100461688-9381059A`.
- Quantity: five PCBs, two top-side assembled; Pico and headers hand soldered.
- The user paid for this order. The portal showed Paid and PCB/assembly Reviewing
  when checked October 4; later review completion has not been verified.
- Recorded paid amounts: PCB $60.30, assembly $229.52, shipping $40.06,
  duties/tax $109.05; total $438.93. These supersede the earlier draft quote.
- Old active transceiver cart entries and Quotes entries were absent when checked
  after payment; no draft deletion was necessary.

## Exact manufactured-data baseline

Archive: `review_20261004_1100/transceiver-preview-gerbers.zip`, with BOM/CPL
in that directory's `assembly/`. The original manifest covers 45 artifacts.
On October 5, all 45 artifact sizes and SHA-256 hashes were rechecked successfully.
The eight schematic sheets, project file and current PCB all exactly matched
`review_20261004_1100/evidence/source-hashes.json`.

PCB SHA-256:
`e969c80d28f62171bb6eb9b52046d4ef295c5c81170a37aa8faf685d421b0742`.

The H1/H2 model is the unmodified ESQ-126-39-G-D STEP file under
`../kicad/lib/3dmodels/`, including its attribution/license record. The native
CPL remains in KiCad orientation. The uploaded portal draft received clockwise
90-degree corrections for U1/U4/U5/U10/U11/Y2 and 180-degree corrections for
U7/U8/U9/U12/U13/U14/Q3/Q4/Y1. Do not assume these corrections carry over to a
new upload. All 144 placements were selected in the reviewed draft.

## Open vendor review

On October 5 JLCPCB stated it cannot meet J9's requested finished-hole diameter
of 0.84 ±0.05 mm and offered its standard +0.13/−0.08 mm tolerance instead.
At 0.84 mm nominal this permits 0.76–0.97 mm finished holes, outside the
manufacturer drawing's 0.79–0.89 mm range.

J9 is a soldered through-hole Molex 734151471 / LCSC C588477 connector, not
press-fit. No blanket tolerance waiver or cancellation has been sent by the
assistant. Recommended follow-up is assembly-engineering confirmation of insertion
and soldering with the offered tolerance before accepting it. This note does not
assert that the factory has placed a hold or accepted that condition.

Vendor CAM/impedance acceptance and final placement approval remain unverified.
The order requested production-file and placement confirmation with automatic
placement confirmation disabled. Preserve the U15 package/paste and polarity
review requests described in the original archive.

## Validation scope

The archived review reports native ERC zero errors and DRC zero errors / zero
unconnected, with the documented warnings/exclusions. The R39 terminal swap is
explicitly proven electrically equivalent; exact pin parity is not claimed.
The October 5 reconciliation performed integrity checks, not a new electrical
review or a board modification. Bench power, CAN, thermal and RF qualification
remain to be performed on the prototypes.
