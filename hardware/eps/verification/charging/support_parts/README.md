# Charger support-part selection

2026-10-24. These records verify development part identities and interface
choices; the integrated circuit has its own electrical and rendered acceptance.

## BOOST capacitor

Select **GRM188R72A223KAC4D** for the LTC4162 SW-to-BOOST 22 nF capacitor.
Murata's [GRM188R72A223KAC4-01A reference sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM188R72A223KAC4-01A.pdf),
specifications dated June 17, 2026, p.2, verifies 22 nF, 100 V DC, X7R,
±10%, 0603/1608M. Body dimensions are 1.6 × 0.8 × 0.8 mm, each ±0.1 mm.
The suffix D means a 180 mm reel with W8P4 paper tape and 4000 parts per reel.
The source page was rendered and actually inspected; [the render](boost_source_p2.png)
and [source hashes/metadata](boost_source.json) preserve the evidence.

The datasheet identifies the component; it does not establish its effective
capacitance, actual BOOST waveform, assembly qualification or procurement.
Reuse the stock nonpolarized capacitor symbol and verified 0603 lands.
The capacitor's 100 V rating does not increase the IC's BOOST-to-SW rating.

## Thermistor harness partition

Use a separate **two-contact JST GH** interface for the charger NTC. A later
seven-contact retained-domain BMS connector can carry three cell-sense nodes
and two independent two-wire BMS sensors. The nine-contact requirement is
therefore preserved across two differently sized connectors; it never froze
a single mixed-domain connector. The main power connection remains XT30.

This avoids placing system-ground charger return in the same connector as
raw BMS VSS and cell voltages. It does not replace pack-side sense-wire fault
protection, insulation, strain relief, correct assembly or mating-order review.
There must be no raw cell/Kelvin feed around the hardware RBF boundary.

The charger development pair is **BM02B-GHS-TBT(LF)(SN)** header and
**GHR-02V-S** housing with **SSHL-002T-P0.2** crimp contacts. Assign pin 1
to the charger NTC sense node and pin 2 to quiet system GND. The sensor itself
is an insulated, pack-mounted Semitec 103AT-2 candidate, electrically separate
from both BMS sensors. No permanent dummy resistor is permitted.

The official [JST US catalog](https://www.jst.com/wp-content/uploads/2025/06/eGH.pdf)
pp.2–3 was downloaded, rendered and actually inspected: positive lock,
1.25 mm pitch, 50 V rating, 1 A reference at AWG 26; applicable AWG 30–26
and insulation diameter 0.76–1.0 mm. The assembly figure gives approximately
7.3 mm mated height; a 16 mm board standoff alone does not establish wire
bend, latch/tool access or actual mechanical fit.

The stock footprint search returned
`Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical`. Its two signal
lands and two mechanical retention lands require a physical-map/disposable
acceptance before actual placement. The queried 0.6 × 1.7 mm signal lands
are longer than the catalog's 0.6 × 1.35 mm reference lands; do not describe
stock geometry as an exact manufacturer pattern. The two MP regions are
mechanical retention, with no signal assignment in the two-pin symbol.

Temperature qualification remains open. The retrieved US catalog specifies
−25 to +85 °C; the [current global catalog](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf)
reports a wider range. Resolve the applicable approval drawing/version before
claiming a connector passes the −40 to +85 °C electronics screen. Neither
catalog establishes vacuum, radiation, launch or flight acceptance.

## Precision resistors

Vishay [TNPW e3 document 28758](https://www.vishay.com/docs/28758/tnpw_e3.pdf),
revision April 10, 2026, pp.1–2/4, changes the earlier catalog power figures.
For newly placed TNPW0603 parts use **0.110 W P70, General mode**, with a
125 °C film limit and thermal derating. The 0.210 W table maximum requires
Advanced mode and a 175 °C film limit; it is not the chosen precision operating
condition. This does not migrate unrelated historical schematic parts.

The suffix codes B/E/EA mean ±0.1%, ±25 ppm/K and 5000-piece reel. Values
63K4, 10K0 and 4K70 are consistent with the proposed RT, bias and pull-up
parts. The three source pages were rendered and actually inspected;
[hashes and metadata](tnpw_source.json) accompany the source-page renders.
A 4.7 kΩ pull-up across 3.3 V dissipates about 2.32 mW. That remains below
the General-mode straight-line 85 °C allowance of about 80 mW, before
actual board/self-heating and long-term precision review.
