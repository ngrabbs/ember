# Rev B high-power resistor metadata correction

2026-10-24. The BMS integration review found an existing field error in five source/recovery protection resistors. The `K` TCR code in their exact Vishay CRCW-HP order codes means **100 ppm/K**, whereas their stored fields said 25 ppm/K. Correct those five TCR fields through Konnect, retaining reference, UUID, value, MPN, footprint and electrical connectivity. This is an explicit exception to the integration checkpoint's otherwise preserved pre-existing metadata.

| Reference | Existing exact MPN | Function from charger-stage exported graph |
|---|---|---|
| R601 | CRCW1206100RFKEAHP | Source controller bias feed, SRC_FILTERED to D600 anode |
| R610 | CRCW1206100RFKEAHP | Source reset/discharge transistor path to SRC_COMMON |
| R612 | CRCW12061R00FKEAHP | Source input RC snubber resistance |
| R614 | CRCW1206100RFKEAHP | Recovery controller bias feed, REC5_PIN to REC5_BIAS |
| R621 | CRCW1206100RFKEAHP | Recovery reset/discharge transistor path to REC5_COMMON |

R625 already records 100 ppm/K and needs no correction. The new 300 Ω precharge part CRCW1206300RFKEAHP must also record 100 ppm/K. The [Vishay CRCW-HP e3 datasheet](https://www.vishay.com/docs/20043/crcwhpe3.pdf), document 20043, ordering-code table, is the primary authority. The prior CAN-branch study had already encountered this distinction; the five native metadata errors survived that earlier candidate correction.

At a 65 K excursion and 1% initial tolerance, a conservative additive screen is ±1.65%, giving 98.35–101.65 Ω or 0.9835–1.0165 Ω. The former 25 ppm/K field would imply ±1.1625%. These five parts are not the precision OV/UV divider resistors, so this field correction does not change the programmed trip ratios. It widens the bias/reset RC and snubber-resistance screening envelope. Earlier nominal model runs are still nominal evidence; their unchanged resistor numbers cannot be reclassified as full tolerance/temperature coverage.

Regenerate the complete exported graph and verify exact equality before/after this field-only correction. Record the five allowed property changes and preservation of all other pre-existing properties/UUIDs in the current integration verifier. Keep earlier committed fixtures and their hashes frozen. Pulse/repetition, assembled thermal resistance and hot protection performance remain separate open gates; the 0.75 W P70 rating alone does not close them.
