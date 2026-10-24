# Charger PowerPath MOSFET package review

2026-10-24. **Not yet accepted for circuit use.** Exact candidate CSD18543Q3A
uses the stock `Transistor_FET:CSD18543Q3A` symbol. The recorded Konnect queries
show its five logical pin numbers and the installed
`Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET` footprint. No library was edited.

[TI SLPS633](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf), pp.1 and 8–10,
was rendered and actually inspected. The package's physical terminals 5–8 and
thermal region 9 all belong to drain and intentionally map to stock logical
pin 5. This is five physical drain regions, not five independent electrical
nets. Source terminals 1/2/3 remain separate stock symbol pins; gate is 4.

The stock land is not the exact recommended pattern: source/gate centers are
X=−1.44 rather than −1.55 mm, and tangential width is 0.50 rather than 0.30 mm.
Its paste apertures also differ. The footprint-info API describes the custom
central drain pad's basic size but does not expose its union primitives; those
fields alone cannot prove the complete drain geometry.

The [construction proposal](../../../design/rev_b_charger_powerpath_footprint_rules.md)
therefore specifies the manufacturer copper union and stencil apertures using
supported overlapping rectangular pads, while preserving the stock logical
symbol. Approval, creation, full geometry readback and disposable symbol/board
verification remain required. No new footprint or real circuit placement has
been performed. This record does not qualify the electrical PowerPath design,
thermal performance, assembly process or procurement.
