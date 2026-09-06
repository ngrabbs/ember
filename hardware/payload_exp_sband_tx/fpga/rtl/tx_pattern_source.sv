// ---------------------------------------------------------------------------
// tx_pattern_source - symbol timing, pattern selection, registered TX output
//
// EMBER experimental S-band payload, milestone M0.
//
// The reusable symbol engine for the experimental transmitter. It divides the
// board clock down to a symbol rate, selects one of four test patterns, and
// presents the result on a registered output.
//
// M0 proves this block. Under the selected architecture (see the payload trade
// study) its symbol stream later drives the BPSK symbol mapper and NCO ahead of
// the DAC; under the deferred phase-modulator architecture the same stream
// drives an external buffer directly. It is unchanged either way, which is why
// it is worth building first.
//
// Timing contract
// ---------------
//   symbol_tick is asserted for exactly one clock cycle, in the same cycle in
//   which a new symbol first appears on tx_symbol. Both are registered off the
//   same clock edge, so on a scope or logic analyser symbol_tick marks the
//   first clock of every symbol and can be used directly as a trigger.
//
//   tx_symbol is assigned only inside always_ff. There is no combinational
//   path from pattern_sel, rate_sel or the pattern state to the pin, so the
//   output cannot glitch while several internal bits settle.
//
//   pattern_sel and rate_sel are sampled at symbol boundaries only. Changing
//   them mid-symbol takes effect at the next boundary rather than immediately,
//   so a control change cannot shorten or corrupt a symbol in flight.
//
// Enable behaviour
// ----------------
//   tx_enable low holds the divider at zero, freezes the pattern state, forces
//   tx_symbol to IDLE_SYMBOL and drives tx_oe_n high. Re-enabling therefore
//   restarts at a clean symbol boundary with the pattern state where it was
//   left, which makes disable/enable cycles repeatable.
//
//   tx_oe_n is the external buffer's active-low output enable. It is separate
//   from the symbol value on purpose: permission to drive the interface and
//   the data being driven are different things. The buffer must also have a
//   resistor-defined disabled state, because no register in this FPGA has a
//   defined value before configuration completes.
// ---------------------------------------------------------------------------

`default_nettype none

module tx_pattern_source #(
    parameter int unsigned CLOCK_HZ    = 100_000_000,
    // Four selectable symbol rates. Each must divide CLOCK_HZ exactly; the
    // elaboration check below refuses anything else rather than silently
    // producing a rate that is a fraction of a percent off.
    parameter int unsigned RATE_0      = 1_000,
    parameter int unsigned RATE_1      = 10_000,
    parameter int unsigned RATE_2      = 100_000,
    parameter int unsigned RATE_3      = 1_000_000,
    parameter logic [6:0]  PRBS_SEED   = 7'h7f,
    parameter logic        IDLE_SYMBOL = 1'b0
) (
    input  logic       clk,
    input  logic       rst,          // synchronous, active high
    input  logic       tx_enable,    // logical permission to transmit
    input  logic [1:0] pattern_sel,  // 00 zero, 01 one, 10 alternating, 11 PRBS-7
    input  logic [1:0] rate_sel,     // selects RATE_0 .. RATE_3
    output logic       tx_symbol,    // registered binary symbol
    output logic       tx_oe_n,      // active-low external buffer enable
    output logic       symbol_tick   // one cycle, marks the first clock of a symbol
);

    // -----------------------------------------------------------------------
    // Symbol-rate divisors
    // -----------------------------------------------------------------------
    localparam int unsigned DIV_0 = CLOCK_HZ / RATE_0;
    localparam int unsigned DIV_1 = CLOCK_HZ / RATE_1;
    localparam int unsigned DIV_2 = CLOCK_HZ / RATE_2;
    localparam int unsigned DIV_3 = CLOCK_HZ / RATE_3;

    localparam int unsigned DIV_MAX_01 = (DIV_0 > DIV_1) ? DIV_0 : DIV_1;
    localparam int unsigned DIV_MAX_23 = (DIV_2 > DIV_3) ? DIV_2 : DIV_3;
    localparam int unsigned DIV_MAX    = (DIV_MAX_01 > DIV_MAX_23) ? DIV_MAX_01 : DIV_MAX_23;
    localparam int unsigned CW         = (DIV_MAX <= 2) ? 1 : $clog2(DIV_MAX);

    // Control registers, sampled at symbol boundaries. Declared here because
    // the divisor decode below reads rate_q.
    logic [1:0]    pattern_q;
    logic [1:0]    rate_q;

    // Terminal counts rather than divisors. The counter runs 0 .. DIV-1, so
    // DIV-1 always fits in CW bits whereas DIV itself does not when DIV is an
    // exact power of two.
    localparam int unsigned LAST_0 = DIV_0 - 1;
    localparam int unsigned LAST_1 = DIV_1 - 1;
    localparam int unsigned LAST_2 = DIV_2 - 1;
    localparam int unsigned LAST_3 = DIV_3 - 1;

    logic [CW-1:0] div_count;
    logic [CW-1:0] div_last;

    always_comb begin
        case (rate_q)
            2'b00:   div_last = LAST_0[CW-1:0];
            2'b01:   div_last = LAST_1[CW-1:0];
            2'b10:   div_last = LAST_2[CW-1:0];
            default: div_last = LAST_3[CW-1:0];
        endcase
    end

    // A >= comparison rather than == so that selecting a shorter divisor while
    // the counter is already past it cannot stall the divider for a full wrap
    // of the counter.
    logic tick_now;
    assign tick_now = tx_enable && (div_count >= div_last);

    // -----------------------------------------------------------------------
    // Pattern sources
    // -----------------------------------------------------------------------
    logic       alternating;
    logic       prbs_bit;
    logic       selected_symbol;

    prbs7_gen #(
        .SEED (PRBS_SEED)
    ) u_prbs7_gen (
        .clk     (clk),
        .rst     (rst),
        .en      (tick_now),
        .bit_o   (prbs_bit),
        .state_o (/* unused */)
    );

    // Both pattern sources present their CURRENT value here and advance on the
    // same edge that registers it, so the symbol transmitted is the one that
    // was pending before the shift. prbs7_gen and prbs7_golden.py share that
    // "output before the shift" convention.
    always_comb begin
        case (pattern_q)
            2'b00:   selected_symbol = 1'b0;
            2'b01:   selected_symbol = 1'b1;
            2'b10:   selected_symbol = alternating;
            default: selected_symbol = prbs_bit;
        endcase
    end

    // -----------------------------------------------------------------------
    // Symbol timing and the registered output
    // -----------------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (rst) begin
            div_count   <= '0;
            alternating <= 1'b0;
            pattern_q   <= 2'b00;
            rate_q      <= 2'b00;
            tx_symbol   <= IDLE_SYMBOL;
            tx_oe_n     <= 1'b1;
            symbol_tick <= 1'b0;
        end else begin
            tx_oe_n     <= ~tx_enable;
            symbol_tick <= tick_now;

            if (!tx_enable) begin
                // Hold at a clean boundary with the pattern state frozen, and
                // accept control changes freely: configuring while disabled and
                // then enabling starts the first symbol at the requested
                // pattern and rate.
                div_count <= '0;
                tx_symbol <= IDLE_SYMBOL;
                pattern_q <= pattern_sel;
                rate_q    <= rate_sel;
            end else if (tick_now) begin
                div_count   <= '0;
                tx_symbol   <= selected_symbol;
                alternating <= ~alternating;
                // While transmitting, controls are sampled only here, at a
                // symbol boundary, so a change cannot corrupt a symbol in
                // flight.
                pattern_q   <= pattern_sel;
                rate_q      <= rate_sel;
            end else begin
                div_count <= div_count + 1'b1;
            end
        end
    end

`ifndef SYNTHESIS
    initial begin
        if (RATE_0 == 0 || CLOCK_HZ % RATE_0 != 0)
            $fatal(1, "tx_pattern_source: RATE_0 (%0d) must divide CLOCK_HZ (%0d) exactly", RATE_0, CLOCK_HZ);
        if (RATE_1 == 0 || CLOCK_HZ % RATE_1 != 0)
            $fatal(1, "tx_pattern_source: RATE_1 (%0d) must divide CLOCK_HZ (%0d) exactly", RATE_1, CLOCK_HZ);
        if (RATE_2 == 0 || CLOCK_HZ % RATE_2 != 0)
            $fatal(1, "tx_pattern_source: RATE_2 (%0d) must divide CLOCK_HZ (%0d) exactly", RATE_2, CLOCK_HZ);
        if (RATE_3 == 0 || CLOCK_HZ % RATE_3 != 0)
            $fatal(1, "tx_pattern_source: RATE_3 (%0d) must divide CLOCK_HZ (%0d) exactly", RATE_3, CLOCK_HZ);
    end
`endif

endmodule

`default_nettype wire
