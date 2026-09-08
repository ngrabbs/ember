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

## Pmod JB - UART console, 115200 8N1
##   pin 1  jb_uart_tx  FPGA output -> the cable's RX
##   pin 2  jb_uart_rx  FPGA input  <- the cable's TX
## Connect GND, TX and RX only. NEVER the cable's VCC: this board has its own
## supply, and a 5 V VCC wire on a self-powered board is what destroyed the
## IceZero this payload started on.
set_property -dict { PACKAGE_PIN W14  IOSTANDARD LVCMOS33 } [get_ports { jb_uart_tx }]
set_property -dict { PACKAGE_PIN Y14  IOSTANDARD LVCMOS33 } [get_ports { jb_uart_rx }]

## AD9910 DDS - Pmod JB pins 3,4,7,8,9,10 and JA pins 7,8,9,10
## GROUND IS THE ONLY OTHER CONNECTION between the two boards. The DDS has its
## own 5 V barrel jack; do not bridge 5 V or 3.3 V in either direction.
set_property -dict { PACKAGE_PIN T11  IOSTANDARD LVCMOS33 } [get_ports { dds_cs_n }]
set_property -dict { PACKAGE_PIN T10  IOSTANDARD LVCMOS33 } [get_ports { dds_sclk }]
set_property -dict { PACKAGE_PIN V16  IOSTANDARD LVCMOS33 } [get_ports { dds_sdio }]
set_property -dict { PACKAGE_PIN W16  IOSTANDARD LVCMOS33 } [get_ports { dds_sdo }]
set_property -dict { PACKAGE_PIN V12  IOSTANDARD LVCMOS33 } [get_ports { dds_io_update }]
set_property -dict { PACKAGE_PIN W13  IOSTANDARD LVCMOS33 } [get_ports { dds_master_reset }]
set_property -dict { PACKAGE_PIN U18  IOSTANDARD LVCMOS33 } [get_ports { dds_pf0 }]
set_property -dict { PACKAGE_PIN U19  IOSTANDARD LVCMOS33 } [get_ports { dds_pf1 }]
set_property -dict { PACKAGE_PIN W18  IOSTANDARD LVCMOS33 } [get_ports { dds_pf2 }]
set_property -dict { PACKAGE_PIN W19  IOSTANDARD LVCMOS33 } [get_ports { dds_pll_lock }]

## AD9910 reference clock - ChipKit header ck_io0. JA and JB are fully used.
## 125 MHz / 10 = 12.5 MHz. This replaces the breakout's own 40 MHz oscillator,
## whose output does not reach the AD9910's REF_CLK pin, and has the side
## benefit of making the DDS carrier coherent with the symbol clock.
set_property -dict { PACKAGE_PIN T14  IOSTANDARD LVCMOS33 } [get_ports { dds_refclk }]
set_property SLEW FAST [get_ports { dds_refclk }]
set_property DRIVE 12  [get_ports { dds_refclk }]

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
set_false_path -from [get_ports { jb_uart_rx }]
set_false_path -from [get_ports { dds_sdo dds_pll_lock }]
set_false_path -to   [get_ports { dds_cs_n dds_sclk dds_sdio dds_io_update \
                                  dds_master_reset dds_pf0 dds_pf1 dds_pf2 }]
create_generated_clock -name dds_refclk -source [get_ports clk] -divide_by 10 \
                       [get_ports dds_refclk]
set_false_path -to   [get_ports { jb_uart_tx }]
set_false_path -to   [get_ports { led[*] }]
set_false_path -to   [get_ports { ja_tx_symbol ja_symbol_tick ja_tx_oe_n }]

## Drive strength and slew on the scope outputs - keep edges clean into a probe
set_property SLEW SLOW [get_ports { ja_tx_symbol ja_symbol_tick ja_tx_oe_n }]
set_property DRIVE 8   [get_ports { ja_tx_symbol ja_symbol_tick ja_tx_oe_n }]

## PL-only design: no PS is instantiated, so tell Vivado the unused PS is fine.
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
