# Constraints

**Empty on purpose.**

No `.pcf` is committed until the IceZero board in hand has been physically
identified. Copying a pin-constraint file from another iCE40 board, or from a
different revision of this one, is the fastest way to drive a pin into
something that will not tolerate it.

Fill in the board-facts table in
[`../../fpga_link_processor_logic_interface_first_bringup.md`](../../fpga_link_processor_logic_interface_first_bringup.md)
first — assembly revision, FPGA top marking, density, package, oscillator
marking and frequency, selected PMOD connector, selected pins, and I/O bank
voltage — then create `icezero_<verified-revision>.pcf` and record which
pinout document revision it came from.

Until then `make synth` still works: it runs synthesis for a resource estimate
and needs no pin assignment. Place-and-route and bitstream generation are what
wait on this file.
