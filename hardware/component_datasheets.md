# Component and Module Datasheets

Third-party documents the design depends on. Each entry records the vendor's
own document number and revision, so the exact revision a design decision was
made against stays identifiable even if a download URL moves.

**Why document numbers, not just links.** Vendors reissue datasheets under the
same URL. A pin map derived from DG-10931-001 v1.1 is not necessarily valid
against v1.2. Cite the number and revision in design notes, not "the Jetson
design guide".

Documents held locally in this repository are marked in the *Local* column.
Anything not held locally is retrieved from the vendor.

---

## Payload compute — NVIDIA Jetson

All available through the [Jetson Download Center](https://developer.nvidia.com/embedded/downloads)
(search by document number). Registration may be required.

| Document | Number | Rev | Local |
|---|---|---|---|
| Jetson Orin Nano Series Data Sheet | DS-11105-001 | v1.1 | `payload_compute/design/` |
| Jetson Orin NX Series and Orin Nano Series Design Guide | DG-10931-001 | v1.1 | `payload_compute/design/` |
| Jetson Orin Nano Developer Kit Carrier Board Specification | SP-11324-001 | v1.3 | `payload_compute/design/` |
| Jetson Orin NX and Orin Nano Pin Function Names Guide | DA-11434-001 | v1.0 | `payload_compute/design/` |
| Jetson Nano System-on-Module Data Sheet | DS-09366-001 | v1.1 | — |

Derived work in this repository — this is where the analysis lives, and it
cites the documents above rather than reproducing them:

- [`payload_compute/design/payload_carrier_pinmap.md`](payload_compute/design/payload_carrier_pinmap.md) — carrier pin assignment
- [`payload_compute/design/jetson_module_compatibility_report.md`](payload_compute/design/jetson_module_compatibility_report.md) — Orin Nano vs Original Nano
- [`payload_compute/design/altium_payload_schematic_guide.md`](payload_compute/design/altium_payload_schematic_guide.md)
- [`payload_compute/design/altium_payload_layout_guide.md`](payload_compute/design/altium_payload_layout_guide.md)

## Electrical Power System

| Part | Vendor | Document | Local |
|---|---|---|---|
| LTC4162-L battery charger | Analog Devices | [LTC4162-L datasheet](https://www.analog.com/en/products/ltc4162-l.html) | `eps/components/LTC4162/` |
| DC2038A evaluation board | Analog Devices | DC2038A demo manual | `eps/components/LTC4162/` |
| TPSM5D1806 dual buck module | Texas Instruments | [TPSM5D1806](https://www.ti.com/product/TPSM5D1806) datasheet + `sluuc66b` user guide | `eps/components/TPSM5D1806/` |
| SM141K10TF solar module | Anysolar / IXYS | SM141K10TF data sheet, 2021-05 | `eps/components/SM141K10TF/` |
| INR18650 MJ1 cell | LG Chem | Cell specification | — |

## Communications

| Part | Vendor | Document | Local |
|---|---|---|---|
| ADE-1+ frequency mixer | Mini-Circuits | ADE-1+ datasheet ([LCSC C2942210](https://www.lcsc.com/product-detail/C2942210.html)) | `comms/design/` |
| WI0805QD1R0MST-HF 1 µH choke | DDY / Huizhou Deli | Rev A, 2022-09-27, Chinese original ([LCSC C18221300](https://www.lcsc.com/product-detail/C18221300.html)) | `comms/design/` |
| Si5351A clock generator | Skyworks | Si5351 datasheet + AN619 | — |
| PSA4-5043+ MMIC amplifier | Mini-Circuits | PSA4-5043+ datasheet | — |

[`comms/design/WI0805QD1R0MST-HF_datasheet_translated.md`](comms/design/WI0805QD1R0MST-HF_datasheet_translated.md) is our own English
translation of the DDY original, not a vendor document.

## Housekeeping and structure

| Item | Vendor | Document | Local |
|---|---|---|---|
| CubeSat Kit Motherboard (CSKB pin map) | Pumpkin | DS_CSK_MB_710-00484-E, Rev E, P/N 710-00484 | `../system/interfaces/` |
| ABM8G SMD crystal | Abracon | ABM8G series datasheet ([LCSC C596913](https://www.lcsc.com/product-detail/C596913.html)) | `payload_compute/design/` |
| MR25H40 SPI MRAM | Everspin | MR25H40 datasheet | — |
| RP2040 / Pico SDK | Raspberry Pi | [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) | — |

## Reference designs

| Project | Source |
|---|---|
| AMSAT RT-IHU | <https://gitlab.amsat.org/engineering/golf/rt-ihu> |
| AMSAT CubeSatSim | <https://github.com/alanbjohnston/CubeSatSim> |
