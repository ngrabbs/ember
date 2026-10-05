# TPS26600PWPR bootstrap package acceptance

2026-10-05. Accepted for schematic capture and prototype lead mapping; thermal layout/stencil/assembly qualification remains pending.

TI exact MPN TPS26600PWPR, HTSSOP PWP0016A, SLVSDG2G Rev G. [Datasheet](https://www.ti.com/lit/ds/symlink/tps2660.pdf), pin functions pp.4–5; appended package outline/layout PDF pp.52–54, drawing4214868/A02/2017. Pin figure explicitly TOP VIEW: key at upper-left,1→8 down left and9→16 up right, counterclockwise around top. Bottom exposed-pad outline is translated into component-side land view; electrical EP17 is explicitly numbered by package drawing.

Symbol `Power_Management:TPS26600PWP`. Footprint `EMBER_Payload:TI_PWP0016A_HTSSOP-16_EP3.4x5_Mask3.3x3.3_Prototype`. Default stock footprint mask2.66x2.46 does not match current appended land example3.3x3.3, so it was not used.

|Lead|Function / symbol type|Pad / X,Y mm|View evidence|
|---|---|---|---|
|1|IN / power_in|1 / -2.900,-2.275|TI top view p.4; component-side land p.53|
|2|IN / passive|2 / -2.900,-1.625|TI top view p.4; component-side land p.53|
|3|UVLO / input|3 / -2.900,-0.975|TI top view p.4; component-side land p.53|
|4|NC / no_connect|4 / -2.900,-0.325|TI top view p.4; component-side land p.53|
|5|OVP / input|5 / -2.900,0.325|TI top view p.4; component-side land p.53|
|6|MODE / input|6 / -2.900,0.975|TI top view p.4; component-side land p.53|
|7|~{SHDN} / input|7 / -2.900,1.625|TI top view p.4; component-side land p.53|
|8|RTN / passive|8 / -2.900,2.275|TI top view p.4; component-side land p.53|
|9|GND / power_in|9 / 2.900,2.275|TI top view p.4; component-side land p.53|
|10|IMON / output|10 / 2.900,1.625|TI top view p.4; component-side land p.53|
|11|ILIM / passive|11 / 2.900,0.975|TI top view p.4; component-side land p.53|
|12|dVdT / passive|12 / 2.900,0.325|TI top view p.4; component-side land p.53|
|13|NC / no_connect|13 / 2.900,-0.325|TI top view p.4; component-side land p.53|
|14|~{FLT} / open_collector|14 / 2.900,-0.975|TI top view p.4; component-side land p.53|
|15|OUT / power_out|15 / 2.900,-1.625|TI top view p.4; component-side land p.53|
|16|OUT / passive|16 / 2.900,-2.275|TI top view p.4; component-side land p.53|
|17|RTN / passive|17 / 0.000,0.000|TI top view p.4; component-side land p.53|

16 perimeter leads+1 electrical EP =17 symbol pins =17 numbered copper pads. Pins1/2 IN,15/16 OUT and8/17 RTN are coincident in the stock symbol but separate physical leads/pads. Five unnamed mask/paste features are nonelectrical, giving22 total footprint pad objects: mask3.3x3.3 andfour1.45x1.45 rounded paste windows. CopperEP3.4x5; perimeterlands1.5x0.45 at±2.9mm,0.65pitch. No holes or duplicate numbered pads. Prototype paste area roughly77%; this departs from TI100% example and requires assembly review. Thermal vias are deferred to layout and must connect RTN only.

Acceptance: source figures viewed; every pin/pad queried; disposable U1 symbol and updated U2 footprint placed/read back, top-view key/numbering/body/courtyard/silk/paste visually inspected in `symbol.png` and `footprint-detail.png`. U1 PCB is initial graphics experiment, U2 is final accepted geometry. No real PCB placements. The symbol intentionally hides stacked lead numbers; exported node membership must include all17 logical pins. RTN and EP17 must never be tied to systemGND.
