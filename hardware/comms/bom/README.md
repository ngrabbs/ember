# Comms BOM and sourcing

[Comms home](../README.md) · [Open work](../TODO.md) · [Purchased Y24 order](../releases/Y24-order-record.md)

## Ordering and assembly

Use `LCSC Part #` for exact JLCPCB C-numbers in the schematic, PCB, and BOM
export. Verify live JLCPCB stock for the build quantity plus the selected
assembly service's allowance.

Keep ordering codes for J6/J7/J8 (DNP) and hand-soldered parts in the full BOM.
Exclude DNP parts, hand-soldered parts, bare test pads (`N/A`), and mounting
holes from the assembly upload. Account for the Pico and CAN termination
shunts separately. Install the shunts only at a bus end.

Regenerate the native netlist before exporting a new manufacturing BOM and
check the filtered BOM and placement files against the vendor preview. Use the
[Y24 assembly BOM](../releases/review_20261004_1100/assembly/BOM.csv) for the
exact purchased prototype baseline.

## Part selections

| References | Selected part | Decision |
|---|---|---|
| L12/L13/L19–L24 | Murata LQW15AN10NG00D · C90642 | Replaced the Coilcraft 10 nH part. Use the Murata model for filter work and verify measured response. |
| U12 | TI TLV73330PDBVR · C882826 | Replaced TLV75530PDBVR. |
| D12/D13 | Lite-On LTST-C190KGKT · C125094 | Top-view green LED in the existing 0603 footprint. |
| U9 / U10 | Mini-Circuits PSA4-5043+ · C5240848 / ADE-1+ · C2942210 | Retained the exact amplifier and mixer. Recheck both when sourcing. |
| L16 | Coilcraft 0805HP-221XGRC · C40877572 | Retained 220 nH with the prototype self-resonance exception. Isolation and stability still need bench checks. |
| D15 | Nexperia PESD5V0F1BLD,315 · C478204 | Selected in the existing SOD882D footprint. |
| J9 | Molex 734151471 · C588477 | Soldered through-hole MMCX. See the Y24 order record for the finished-hole tolerance and vendor review. |
| 9.1 pF RF capacitors | YAGEO CC0402BRNPO9BN9R1 · C526972 | Exact part identified. Qualify alternate tuning values against RF models and bench measurements. |
| Y2 / U5 | SI5351A-B-GTR · C504891 / MCP6022T-I/SN · C57639 | Tape-and-reel ordering variants retain the device and package. |

## Regulator capacitors

C103/C104 use Samsung CL10B105KA8NNNC (C29936), 1 µF, 25 V, X7R, 0603.
Typical DC-bias, tolerance, and temperature screening estimated about 0.61 µF
at C103 (5 V) and 0.69 µF at C104 (3 V). Verify effective capacitance and
regulator stability on the bench.
