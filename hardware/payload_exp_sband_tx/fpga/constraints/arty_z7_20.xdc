# ---------------------------------------------------------------------------
# EMBER experimental S-band payload - M0 bench constraints
# Digilent Arty Z7-20  (XC7Z020-1CLG400C)
#
# Pin assignments taken verbatim from Digilent's official master XDC:
#   https://github.com/Digilent/digilent-xdc  ->  Arty-Z7-20-Master.xdc
# Do not hand-transcribe pin names; re-derive from that file if the board
# revision changes.
# ---------------------------------------------------------------------------

## 125 MHz board clock (Sch=SYSCLK)
set_property -dict { PACKAGE_PIN H16  IOSTANDARD LVCMOS33 } [get_ports { clk }]
create_clock -add -name sys_clk_pin -period 8.000 -waveform {0 4} [get_ports { clk }]

## Switches - pattern_sel
set_property -dict { PACKAGE_PIN M20  IOSTANDARD LVCMOS33 } [get_ports { sw[0] }]
set_property -dict { PACKAGE_PIN M19  IOSTANDARD LVCMOS33 } [get_ports { sw[1] }]

## Buttons - 0 reset, 1 advance rate, 2 hold to disable, 3 clear error latch
set_property -dict { PACKAGE_PIN D19  IOSTANDARD LVCMOS33 } [get_ports { btn[0] }]
set_property -dict { PACKAGE_PIN D20  IOSTANDARD LVCMOS33 } [get_ports { btn[1] }]
set_property -dict { PACKAGE_PIN L20  IOSTANDARD LVCMOS33 } [get_ports { btn[2] }]
set_property -dict { PACKAGE_PIN L19  IOSTANDARD LVCMOS33 } [get_ports { btn[3] }]

## LEDs - [1:0] rate_sel, [2] prbs_locked, [3] sticky error or lock loss
set_property -dict { PACKAGE_PIN R14  IOSTANDARD LVCMOS33 } [get_ports { led[0] }]
set_property -dict { PACKAGE_PIN P14  IOSTANDARD LVCMOS33 } [get_ports { led[1] }]
set_property -dict { PACKAGE_PIN N16  IOSTANDARD LVCMOS33 } [get_ports { led[2] }]
set_property -dict { PACKAGE_PIN M14  IOSTANDARD LVCMOS33 } [get_ports { led[3] }]

## Pmod JA - the bench interface
##   pin 1  tx_symbol    scope probe
##   pin 2  symbol_tick  scope trigger, one clock wide
##   pin 3  tx_oe_n
##   pin 4  tx_loopback  jumper from pin 1 to close the loop
set_property -dict { PACKAGE_PIN Y18  IOSTANDARD LVCMOS33 } [get_ports { ja_tx_symbol }]
set_property -dict { PACKAGE_PIN Y19  IOSTANDARD LVCMOS33 } [get_ports { ja_symbol_tick }]
set_property -dict { PACKAGE_PIN Y16  IOSTANDARD LVCMOS33 } [get_ports { ja_tx_oe_n }]
set_property -dict { PACKAGE_PIN Y17  IOSTANDARD LVCMOS33 } [get_ports { ja_loopback }]

# ---------------------------------------------------------------------------
# Timing exceptions
#
# Buttons and switches are mechanical and are synchronised in the RTL. The
# loopback returns through a jumper wire and a two-flop synchroniser, and the
# checker samples it mid-symbol rather than at the clock edge, so its pad-to-pad
# delay carries no timing requirement. The scope outputs have no receiver to
# meet. Constraining any of these would only invent failures.
# ---------------------------------------------------------------------------
set_false_path -from [get_ports { btn[*] }]
set_false_path -from [get_ports { sw[*] }]
set_false_path -from [get_ports { ja_loopback }]
set_false_path -to   [get_ports { led[*] }]
set_false_path -to   [get_ports { ja_tx_symbol ja_symbol_tick ja_tx_oe_n }]

## Drive strength and slew on the scope outputs - keep edges clean into a probe
set_property SLEW SLOW [get_ports { ja_tx_symbol ja_symbol_tick ja_tx_oe_n }]
set_property DRIVE 8   [get_ports { ja_tx_symbol ja_symbol_tick ja_tx_oe_n }]

## PL-only design: no PS is instantiated, so tell Vivado the unused PS is fine.
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
