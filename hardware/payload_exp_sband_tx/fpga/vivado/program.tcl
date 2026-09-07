# ---------------------------------------------------------------------------
# Program the Arty Z7-20 over USB-JTAG.
#
# Needs hw_server running (start it in the background first):
#   hw_server &
#   vivado -mode batch -source vivado/program.tcl
# ---------------------------------------------------------------------------

set here [file dirname [file normalize [info script]]]
set root [file dirname $here]
set bit  $root/build/vivado/top_arty_z7.bit

if {![file exists $bit]} {
    puts "ERROR: no bitstream at $bit - run vivado/build.tcl first"
    exit 1
}

open_hw_manager
connect_hw_server
open_hw_target

# A Zynq JTAG chain enumerates the ARM debug access port (arm_dap_0) as well as
# the PL. arm_dap_0 comes first and is not programmable, so select the FPGA by
# name rather than by position.
puts "=== devices on the chain: [get_hw_devices] ==="
set dev ""
foreach d [get_hw_devices] {
    if {[string match "xc7z*" $d]} { set dev $d; break }
}
if {$dev eq ""} {
    puts "ERROR: no xc7z* device on the JTAG chain - found [get_hw_devices]"
    exit 1
}

puts "=== programming $dev with $bit ==="
current_hw_device $dev
refresh_hw_device -update_hw_probes false $dev
set_property PROGRAM.FILE $bit $dev
program_hw_devices $dev
refresh_hw_device $dev

puts "=== done ==="
close_hw_target
disconnect_hw_server
exit 0
