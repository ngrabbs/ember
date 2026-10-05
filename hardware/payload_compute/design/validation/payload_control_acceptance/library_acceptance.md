# Stage3 exact package acceptance

2026-10-05. Physical lead mapping accepted for bounded prototype capture;
electrical startup, dynamic thresholds, PCB layout and assembly remain qualification work.

All manufacturer pin diagrams are top views, pin1 upper left. Front PCB coordinates
use positive Y down: walk down the left row, then up the right. No bottom-view mirroring.

| Exact MPN | Lead/function/symbol type | Footprint pad coordinates mm |
| --- | --- | --- |
| TPS3700DDCR | 1 OUTA/open_collector; 2 GND/power_in; 3 INA+/input; 4 INB-/input; 5 VDD/power_in; 6 OUTB/open_collector | 1(-1.35,-.95),2(-1.35,0),3(-1.35,.95),4(1.35,.95),5(1.35,0),6(1.35,-.95) |
| TPS3431SDRBR | 1 VDD/power_in;2 CWD/input;3 EN/input;4 GND/power_in;5 SET1/input;6 WDI/input;7 WDO_N/open_collector;8 ENOUT/open_collector;9 EP_GND/passive | 1–4 x=-1.4,y=-.975,-.325,.325,.975;5–8 x=1.4,y=.975,.325,-.325,-.975;9 centered0,0 |
| SN74LVC1G14DBVR | 1 NC/no_connect;2 A/input;3 GND/power_in;4 Y/output;5 VCC/power_in | 1(-1.3,-.95),2(-1.3,0),3(-1.3,.95),4(1.3,.95),5(1.3,-.95) |
| SN74LVC1G32DBVR | 1 A/input;2 B/input;3 GND/power_in;4 Y/output;5 VCC/power_in | Same DBV five-pad geometry |

TPS3700: TI SBVS187G p4 and DDC0006A drawing4214841/E 08/2024
(appended to current TPS3700-Q1 datasheet; identical DDC0006A package).
Six unique symbol leads/pads; no EP. DDC lands1.1x.6 mm,R.05, row spacing2.7mm.
TPS3431: TI SNVSB66A p3 and DRB0008A drawing4218875/A 01/2018 pp28–30.
Eight leads plus electrically grounded thermal pad, assigned logical symbol/pad9.
Eight lands .6x.31mm,R.05,pitch.65,row spacing2.8mm.
EP copper/mask central1.5x1.75mm plus four same-number9 tails .23x.825mm
at x=+/-.325,y=+/-1.2875mm. Five copper shapes all represent one physical EP.
No holes. One unnumbered paste-only aperture1.34x1.555mm covers central EP;
this simplified prototype stencil intentionally differs from TI's complete84% example.
Stencil release, vias and solder bonding require later assembly review.
All copper SMD F.Cu/F.Mask; signal lands also F.Paste. No mechanical pads or 3D model.

Symbols: EMBER_Payload:TPS3700DDC, EMBER_Payload:TPS3431SDRB;
stock74xGxx:74LVC1G14 and74LVC1G32 unnamed logic pins reconciled above.
Footprints: EMBER_Payload:TI_DDC0006A_SOT23_THIN_6,
TI_DRB0008A_VSON_8_EP_Prototype, TI_DBV0005A_SOT23_5.
The DBV five-pad footprint reuses the accepted mode-fixture geometry.
TI SCES218AA p3 and SCES219W p3 confirm1G14/1G32 exact DBVR maps.

Committed library, schematic pin and placed pad queryback: library-evidence.json.
Disposable symbols U1/U2/U3/U4 and front footprints at(100/110/120/130,100)
rotation0 were rendered and visually inspected before real use.
accepted-symbols.png and accepted-packages-detail.png show accepted views.
Pad-number overlays are inspection annotations; pad identities come from saved queryback.
Reused373/17/74/11 acceptance is linked in ../payload_mode_acceptance/library_acceptance.md
and ../../latch_library_acceptance.md. All existing maps queried again before use.

Sources: https://www.ti.com/lit/ds/symlink/tps3700.pdf,
https://www.ti.com/lit/ds/symlink/tps3700-q1.pdf,
https://www.ti.com/lit/ds/symlink/tps3431.pdf,
https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf,
https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf.
