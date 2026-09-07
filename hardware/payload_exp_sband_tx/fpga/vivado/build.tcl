# ---------------------------------------------------------------------------
# EMBER experimental S-band payload - M0 bitstream for the Arty Z7-20
#
# Non-project mode: no .xpr, nothing to get out of step with the repository.
# The RTL and the XDC on disk are the design.
#
#   vivado -mode batch -source vivado/build.tcl
#
# Run from the fpga/ directory, or let the script find it - paths are derived
# from this file's own location, so it works the same on a workstation and
# inside the m75q container.
# ---------------------------------------------------------------------------

set here [file dirname [file normalize [info script]]]
set root [file dirname $here]
set out  $root/build/vivado
file mkdir $out

set part xc7z020clg400-1     ;# Arty Z7-20, XC7Z020-1CLG400C
set top  top_arty_z7

puts "=== EMBER M0 ==="
puts "    root : $root"
puts "    part : $part"
puts "    top  : $top"

# Synthesisable sources only - the testbenches live in sim/ and never come here.
set srcs [lsort [glob $root/rtl/*.sv]]
foreach f $srcs { puts "    rtl  : [file tail $f]" }
read_verilog -sv $srcs
read_xdc $root/constraints/arty_z7_20.xdc

synth_design -top $top -part $part -verilog_define SYNTHESIS
write_checkpoint -force $out/post_synth.dcp
report_utilization -file $out/post_synth_utilization.rpt

opt_design
place_design
phys_opt_design
route_design

write_checkpoint -force $out/post_route.dcp
report_timing_summary -warn_on_violation -file $out/timing_summary.rpt
report_utilization              -file $out/utilization.rpt
report_drc                      -file $out/drc.rpt

write_bitstream -force $out/$top.bit

# Fail the build loudly rather than shipping a bitstream that misses timing.
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
set whs [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -hold]]
puts "=== timing: WNS $wns ns, WHS $whs ns ==="
if {$wns < 0 || $whs < 0} {
    puts "ERROR: timing not met - see $out/timing_summary.rpt"
    exit 1
}
puts "=== bitstream: $out/$top.bit ==="
exit 0
