# PCB pad connectivity reconciliation

Live Konnect pad queries: {'ipc': 107}. Comparison uses previously verified native schematic export (176 nets), with no electrical edits since that export.

86 UUID-based component candidates; 150 existing nets touch those candidates. 7 existing nets split across multiple current schematic nets. These require routing changes; identity relinking alone is insufficient.

## Existing nets requiring review

- /I2C_SCL: I2C_SCL → Y2.4, J7.14; I2C_SDA → R2.2
- /I2C_SDA: I2C_SDA → Y2.5, J7.15; I2C_SCL → R1.2
- GND: GND → Y2.8, R23.2, R27.2, C2.1, C58.2, J9.2, J9.2, J9.2, J9.2, R34.2, L23.2, U10.1, U10.1, U10.1, U10.1, U10.1, U10.1, U10.1, U10.1, U10.1, U10.4, U10.4, U10.4, U10.5, U10.5, C74.1, C79.1, H4.29, H4.30, H4.31, H4.32, Y1.2, C65.2, R30.2, R24.2, L24.2, C96.2, C1.1, C71.1, D12.1, C3.1, C88.1, C66.2, J6.3, J6.8, J6.13, J6.18, J8.9, J8.10, J8.11, J8.12, J8.13, J8.16, J8.20, C76.1, U9.2, C59.2, C61.1, C80.1, L19.2, D13.1, C5.2, C78.1, C68.1, U8.2, C63.2, C72.1, C4.1, U7.3, R22.2, J7.3, J7.8, J7.13, J7.18, C70.1, C100.2, C62.1, C77.1, R29.2, L21.2; TRIPLER_OUT → Q3.3
- /TRIPLER_OUT: Net-(Q3-B) → Q3.1; TRIPLER_OUT → L17.2, TP13.1, C93.1
- Net-(Q1-B): GND → Q3.2; Net-(Q3-B) → R27.1, C73.1
- Net-(U4-RF): Net-(U10-RF) → U10.3; Net-(U9-OUT_DC) → L16.2; Net-(U9-IN) → U9.3
- /BPSK_145: BPSK_DATA → TP12.1; /TX Chain/RF_TX_BPSK_145 → U7.4, C73.2

## Unmatched PCB footprints

C31 (10p), C30 (10p), TP1 (TestPoint), C24 (10p), TP2 (TestPoint), J5 (Conn_Coaxial_Small), C19 (10p), C21 (6.8p), L12 (68n), C22 (10p), C29 (10p), L10 (82n), C23 (33p), L9 (82n), L13 (68n), C20 (6.8p), U1 (MCP6022), C32 (10p), L2 (15n), L6 (15n), L11 (82n)

## Pads absent from native export

[]
