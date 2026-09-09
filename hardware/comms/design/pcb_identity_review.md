# PCB identity conflict review

Read-only saved PCB identity metadata compared with schematic export. Matching reference or value alone does not establish electrical identity.

| Reference | PCB value | Schematic value | PCB path | Schematic path |
|---|---|---|---|---|
| C1 | 15p | 15p | /f2f0ab83-e758-4a41-9b73-ed4cf38f51a5 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/f2f0ab83-e758-4a41-9b73-ed4cf38f51a5 |
| C2 | 100n | 15p | /954d221b-dd04-41cd-b8c0-376bf8ca96ea | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/d3774bc3-685a-4761-bb36-76313ae8072b |
| C3 | 100n | 100n | /f589ca97-b9d0-4175-90dc-a6fb7416d239 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/bff41946-7205-44c9-b2f0-f4046e680604 |
| C4 | 15p | 10u | /d3774bc3-685a-4761-bb36-76313ae8072b | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/32f1bf85-a147-4371-93f1-ecf9a0dc8b46 |
| C5 | 100n | 100n | /bff41946-7205-44c9-b2f0-f4046e680604 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/471a2369-08b7-4fb8-8951-cd78ec0b0890 |
| C6 | 10u | 100n | /32f1bf85-a147-4371-93f1-ecf9a0dc8b46 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/954d221b-dd04-41cd-b8c0-376bf8ca96ea |
| C7 | 100n | 100n | /471a2369-08b7-4fb8-8951-cd78ec0b0890 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/f589ca97-b9d0-4175-90dc-a6fb7416d239 |
| R1 | 0R | 4.7k | /1da3f6d9-30bb-4e40-b6e3-5dbc71726394 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/19c8f017-bd19-476c-a8df-355e796bf98f |
| R2 | 0R | 4.7k | /54106ccf-25b0-4223-8b04-7afecd31f9f6 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/56b16d7e-a84d-4a2e-94ff-9607b2ce3d45 |
| R3 | 4.7k | 0R | /19c8f017-bd19-476c-a8df-355e796bf98f | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/1da3f6d9-30bb-4e40-b6e3-5dbc71726394 |
| R4 | 4.7k | 0R | /56b16d7e-a84d-4a2e-94ff-9607b2ce3d45 | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/54106ccf-25b0-4223-8b04-7afecd31f9f6 |
| Y1 | Crystal_GND2 | Crystal_GND2 | /af4d137f-ad72-41aa-8006-15d04bbf8f6f | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/af4d137f-ad72-41aa-8006-15d04bbf8f6f |
| Y2 | Si5351A-B-GT | Si5351A-B-GT | /711bdd67-cdde-4c92-9503-90ff2e98379d | /f9c62eb1-d7c0-4e60-a61d-f835f0c0a42e/711bdd67-cdde-4c92-9503-90ff2e98379d |
| L12 | 68n | 10n | /6f42ed88-0fc9-4093-a8be-f0ee685cfad3 | /8e04e994-8636-422b-bbcc-3acfa2e99d78/8da06ec2-869c-44ec-886c-dc19c3f472a3 |
| L13 | 68n | 10n | /8e60f7b2-14f6-4cea-a081-7d6d01b593f9 | /8e04e994-8636-422b-bbcc-3acfa2e99d78/ce2c1be5-f623-4c09-b71e-0f119673e888 |

## Proposed links by preserved symbol UUID

86 unique symbol UUID matches; 21 board footprints have no unique match. These are candidates pending pad/net validation, not permission to delete unmatched items.

| Current PCB ref | Schematic ref | PCB value | Schematic value |
|---|---|---|---|
| Y2 | Y2 | Si5351A-B-GT | Si5351A-B-GT |
| Q1 | Q3 | NPN | 2SC3356 |
| L1 | L17 | 220n | 15n |
| R15 | R23 | 330 | 330 |
| R5 | R27 | 47k | 47k |
| C34 | C99 | 100n | 100n |
| C4 | C2 | 15p | 15p |
| L5 | L15 | 220n | 220n |
| C43 | C58 | 47u | 47u |
| D2 | D14 | D_Schottky | D_Schottky |
| TP5 | TP13 | TestPoint | TestPoint |
| J4 | J9 | Conn_Coaxial_Small | Conn_Coaxial_Small |
| TP7 | TP15 | TestPoint | TestPoint |
| C3 | C7 | 100n | 100n |
| R7 | R34 | 51 | 51 |
| L3 | L23 | 15n | 10n |
| U4 | U10 | ADE-1+ | ADE-1+ |
| L14 | L16 | 1u | 1u |
| C52 | C74 | 10u | 10u |
| C27 | C79 | 10u | 10u |
| R4 | R2 | 4.7k | 4.7k |
| H2 | H4 | Conn_02x26_Odd_Even | Conn_02x26_Odd_Even |
| D7 | D11 | LED | LED |
| D6 | D10 | LED | LED |
| Y1 | Y1 | Crystal_GND2 | Crystal_GND2 |
| C25 | C65 | 10p | 10p |
| R1 | R3 | 0R | 0R |
| R9 | R30 | 10k | 10k |
| R16 | R24 | 330 | 330 |
| C33 | C83 | 100n | 1n |
| R2 | R4 | 0R | 0R |
| L4 | L24 | 15n | 10n |
| H1 | H3 | Conn_02x26_Odd_Even | Conn_02x26_Odd_Even |
| C12 | C96 | 6.8p | 9.1p |
| C1 | C1 | 15p | 15p |
| C17 | C71 | 100n | 100n |
| D3 | D12 | Green | Green |
| R6 | R25 | 100R | 100R |
| C5 | C3 | 100n | 100n |
| C44 | C88 | 100n | 100n |
| R10 | R28 | 10k | 10k |
| C15 | C66 | 100n | 100n |
| J1 | J6 | Conn_01x20 | Conn_01x20 |
| C39 | C57 | 2.2n | 2.2n |
| R11 | R20 | 22k | 22k |
| J3 | J8 | Conn_01x20 | Conn_01x20 |
| C9 | C84 | 10p | 3.9p |
| C18 | C76 | 10u | 10u |
| U3 | U9 | PSA4-5043+ | PSA4-5043+ |
| C49 | C59 | 47u | 47u |
| TP3 | TP11 | TestPoint | TestPoint |
| TP8 | TP16 | TestPoint | TestPoint |
| C42 | C61 | 100n | 100n |
| TP4 | TP12 | TestPoint | TestPoint |
| C16 | C80 | 100n | 100n |
| L7 | L19 | 15n | 10n |
| D4 | D13 | Green | Green |
| C10 | C93 | 10p | 3.9p |
| R8 | R32 | 100k | 100k |
| D5 | D9 | LED | LED |
| C7 | C5 | 100n | 100n |
| R3 | R1 | 4.7k | 4.7k |
| C53 | C78 | 100n | 100n |
| C50 | C68 | 10u | 10u |
| U6 | U8 | ADL5602ARKZ-R7 | ADL5602ARKZ-R7 |
| C40 | C63 | 2.2n | 2.2n |
| R17 | R26 | 1k | 1k |
| C41 | C72 | 10u | 10u |
| C6 | C4 | 10u | 10u |
| C2 | C6 | 100n | 100n |
| U2 | U7 | 74LVC1G86 | 74LVC1G86 |
| D1 | D8 | D_Schottky | D_Schottky |
| R14 | R22 | 330 | 330 |
| J2 | J7 | Conn_01x20 | Conn_01x20 |
| TP6 | TP14 | TestPoint | TestPoint |
| C51 | C70 | 100n | 100n |
| C11 | C101 | 10p | 3.9p |
| C13 | C100 | 6.8p | 9.1p |
| R18 | R31 | 1k | 1k |
| C48 | C62 | 100n | 100n |
| C35 | C77 | 100n | 100n |
| R12 | R21 | 22k | 22k |
| R13 | R29 | 10k | 10k |
| L8 | L21 | 15n | 10n |
| C14 | C73 | 100n | 100n |
| C38 | C69 | 100n | 100n |
