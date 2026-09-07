// ---------------------------------------------------------------------------
// refclk_gen - reference clock for the AD9910, divided from the board clock
//
// EMBER experimental S-band payload, M1.
//
// The DDS breakout's own 40 MHz oscillator runs correctly but its output does
// not reach the AD9910's REF_CLK pin - traced as far as the W1 jumper and no
// further. Rather than keep chasing two centimetres of someone else's board,
// the FPGA supplies the reference instead.
//
// This is not purely a workaround. Deriving the DDS reference from the same
// 125 MHz that clocks the symbol engine makes the carrier and the symbol rate
// COHERENT - they cannot drift relative to one another, because they share an
// oscillator. For a modem that is a real advantage: no frequency offset
// accumulates between the carrier and the symbol timing.
//
//   125 MHz / 4 = 31.25 MHz reference
//   31.25 MHz x 32 (CFR3 N) = 1000 MHz SYSCLK, inside VCO5's 920-1030 MHz band
//
// Other exact options, should the wiring prefer a slower edge rate:
//   /5 = 25.0000 MHz, N = 40
//   /3 = 41.6667 MHz, N = 24   (odd divide; this module requires an even one)
//
// The AD9910 accepts 3.2 MHz to 60 MHz on REF_CLK with the PLL enabled, so all
// three are comfortably in range.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module refclk_gen #(
    parameter int unsigned DIVIDE = 4     // must be even, so the duty is 50%
) (
    input  wire  clk,
    input  wire  rst,
    output logic refclk
);
    localparam int unsigned HALF = DIVIDE / 2;
    localparam int unsigned CW   = (HALF <= 1) ? 1 : $clog2(HALF);

    logic [CW-1:0] count;

    always_ff @(posedge clk) begin
        if (rst) begin
            count  <= '0;
            refclk <= 1'b0;
        end else if (count == CW'(HALF-1)) begin
            count  <= '0;
            refclk <= ~refclk;
        end else begin
            count <= count + 1'b1;
        end
    end

`ifndef SYNTHESIS
    initial begin
        if (DIVIDE < 2)
            $fatal(1, "refclk_gen: DIVIDE must be at least 2");
        if (DIVIDE % 2 != 0)
            $fatal(1, "refclk_gen: DIVIDE must be even - an odd divide cannot give a 50%% duty cycle from a single edge, and the AD9910 reference wants a symmetric clock");
    end
`endif
endmodule

`default_nettype wire
