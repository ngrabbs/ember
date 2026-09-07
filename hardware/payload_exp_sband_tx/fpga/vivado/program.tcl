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

set dev [lindex [get_hw_devices] 0]
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
