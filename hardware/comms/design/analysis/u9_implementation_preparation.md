# U9 implementation preparation

Konnect library search found no TQP3M9036 or TQP3M family symbol. It found the existing Package_DFN_QFN:Qorvo_DFN-8-1EP_2x2mm_P0.5mm footprint, with eight leads plus ground paddle, 0.5 mm pitch. The library references Qorvo document da000896. This is a reuse candidate, not an accepted footprint yet.

## Proposed physical mapping, pending drawing comparison

| Lead | Datasheet function | Existing library pad XY, mm (component view) |
|---|---|---|
| 1 | NC | -0.89, -0.75 |
| 2 | RF input | -0.89, -0.25 |
| 3 | NC | -0.89, 0.25 |
| 4 | NC | -0.89, 0.75 |
| 5 | NC | 0.89, 0.75 |
| 6 | Shutdown | 0.89, 0.25 |
| 7 | RF output / DC bias | 0.89, -0.25 |
| 8 | NC | 0.89, -0.75 |
| Exposed paddle | RF/DC ground | 0, 0 (library pad 9) |

Library signal-pad size is 0.48 × 0.25 mm; ground paddle is 0.6 × 1.2 mm. The manufacturer's exposed paddle is not numbered in the available functional diagram; pad 9 is a proposed library mapping. No symbol was created or installed. Physical drawing comparison and disposable-instance render/readback remain BLOCKED by unavailable manufacturer drawing images. Pin function evidence: Qorvo TQP3M9036 datasheet, November 27, 2018, page 1, https://www.mouser.com/datasheet/3/1081/1/TQP3M9036_Data_Sheet.pdf

## Attenuation option ready for sourcing verification

Use a nominal 37.4 Ω series / 150 Ω shunt / 150 Ω shunt pi network as the 6 dB candidate. Ideal 50 Ω ABCD calculation gives 6.013 dB insertion loss and 67.0 dB return loss. Exact candidates: UNI-ROYAL 0402WGF374JTCE, C25108; UNI-ROYAL 0402WGF1500TCE, C25082. Konnect's catalogue reports 17,076 and 230,547 pieces respectively; these are NOT live stock confirmation. Do not assign them to the production BOM until JLCPCB live stock, RF parasitics and power checks are completed. No parts ordered.

The choke remains coupled to the replacement design; do not finalize L16 solely to close a missing-code count. Main schematic/PCB are unchanged.
