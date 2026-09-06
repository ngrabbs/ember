// ---------------------------------------------------------------------------
// prbs7_gen - PRBS-7 sequence generator
//
// EMBER experimental S-band payload, milestone M0.
//
// Convention, which must match sim/prbs7_golden.py exactly:
//
//     polynomial   x^7 + x^6 + 1
//     state        7 bits, state[6] is the MSB
//     seed         7'b111_1111 (0x7F)
//     output       state[6], taken BEFORE the shift
//     feedback     state[6] XOR state[5]
//     next state   {state[5:0], feedback}
//
// "Output before the shift" is the detail most often got wrong when a
// generator and a checker are written separately, so it is stated here, in the
// golden model, and in the bring-up document, and tb_prbs7.sv checks it
// against generated vectors rather than trusting it.
//
// The sequence has period 127 and visits every nonzero register state exactly
// once. The all-zeros state is a lock-up state and is unreachable from any
// nonzero seed, so SEED must be nonzero.
//
// A useful identity that falls out of this convention, and the one prbs7_check
// predicts with:
//
//     b[k+7] = b[k] XOR b[k+1]
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module prbs7_gen #(
    parameter logic [6:0] SEED = 7'h7f
) (
    input  logic       clk,
    input  logic       rst,      // synchronous, active high
    input  logic       en,       // advance one symbol when high
    output logic       bit_o,    // current output bit, valid before the shift
    output logic [6:0] state_o   // register state, for debug and simulation
);

    logic [6:0] state;

    // The output is a plain register bit, so it carries no combinational
    // decode and cannot glitch between clock edges.
    assign bit_o   = state[6];
    assign state_o = state;

    always_ff @(posedge clk) begin
        if (rst)
            state <= SEED;
        else if (en)
            state <= {state[5:0], state[6] ^ state[5]};
    end

`ifndef SYNTHESIS
    initial begin
        if (SEED == 7'b0)
            $fatal(1, "prbs7_gen: SEED must be nonzero; the all-zeros state is a lock-up state");
    end
`endif

endmodule

`default_nettype wire
