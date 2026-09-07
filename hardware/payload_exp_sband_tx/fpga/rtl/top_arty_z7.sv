// ---------------------------------------------------------------------------
// top_arty_z7 - M0 bench top level for the Digilent Arty Z7-20
//
// EMBER experimental S-band payload. Wraps the architecture-independent symbol
// engine with the board's switches, buttons, LEDs and a Pmod, so the symbol
// stream can be put on a scope and the loopback error count read from LEDs.
//
// Bench interface
// ---------------
//   sw[1:0]   pattern:  00 zero · 01 one · 10 alternating · 11 PRBS-7
//   btn[0]    reset (also a power-on reset holds for ~2 us after configuration)
//   btn[1]    press to advance the symbol rate, 1k -> 10k -> 100k -> 1M -> 1k
//   btn[2]    hold to deassert tx_enable - exercises the disable/enable path
//   btn[3]    clear the sticky error latch
//
//   led[1:0]  current rate_sel
//   led[2]    prbs_locked
//   led[3]    sticky: at least one bit error since the latch was cleared
//
//   Pmod JA pin 1  tx_symbol    <- put the scope probe here
//   Pmod JA pin 2  symbol_tick  <- trigger on this; one clock wide, marks
//                                  the first clock of every symbol
//   Pmod JA pin 3  tx_oe_n
//   Pmod JA pin 4  tx_loopback  <- jumper from pin 1 to close the loop
//
// Loopback sampling
// -----------------
// The returned symbol is delayed by the output register, two pad crossings, a
// jumper wire and a two-flop synchroniser - roughly three clocks. Sampling the
// loopback on symbol_tick itself would therefore latch the PREVIOUS symbol and
// produce a checker that never locks. The checker is instead enabled by
// symbol_tick delayed by SAMPLE_DELAY clocks, which lands the sample safely
// inside the symbol: 8 clocks is well past the round trip and well short of the
// 125 clocks in the fastest symbol.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

// Declaration initialisers on flip-flops are how a Xilinx device is given a
// defined state at configuration; they are deliberate here, not stray
// initial-block style. The rest of the RTL is held to a clean -Wall.
/* verilator lint_off PROCASSINIT */

module top_arty_z7 #(
    parameter int unsigned CLOCK_HZ     = 125_000_000,
    parameter int unsigned SAMPLE_DELAY = 8,
    parameter int unsigned DEBOUNCE_W   = 20        // ~8.4 ms at 125 MHz
) (
    input  wire       clk,          // H16, 125 MHz
    input  wire [3:0] btn,
    input  wire [1:0] sw,
    output wire [3:0] led,
    output wire       ja_tx_symbol,   // JA pin 1
    output wire       ja_symbol_tick, // JA pin 2
    output wire       ja_tx_oe_n,     // JA pin 3
    input  wire       ja_loopback     // JA pin 4
);

    // -----------------------------------------------------------------------
    // Reset: power-on pulse, plus btn[0]
    // -----------------------------------------------------------------------
    logic [7:0] por_count = '0;
    logic       por       = 1'b1;
    logic [1:0] btn0_sync = '0;

    always_ff @(posedge clk) begin
        btn0_sync <= {btn0_sync[0], btn[0]};
        if (por_count != 8'hFF) begin
            por_count <= por_count + 1'b1;
            por       <= 1'b1;
        end else begin
            por <= 1'b0;
        end
    end

    logic rst;
    assign rst = por | btn0_sync[1];

    // -----------------------------------------------------------------------
    // Debounced buttons
    // -----------------------------------------------------------------------
    // One debouncer serves each button; each use needs only the level or only
    // the edge, so the other output of that instance is legitimately unused.
    /* verilator lint_off UNUSEDSIGNAL */
    logic btn1_level, btn1_rise;
    logic btn2_level, btn2_rise;
    logic btn3_level, btn3_rise;
    /* verilator lint_on UNUSEDSIGNAL */

    btn_debounce #(.CNT_W(DEBOUNCE_W)) u_b1 (
        .clk(clk), .rst(rst), .raw(btn[1]), .level(btn1_level), .rise(btn1_rise));
    btn_debounce #(.CNT_W(DEBOUNCE_W)) u_b2 (
        .clk(clk), .rst(rst), .raw(btn[2]), .level(btn2_level), .rise(btn2_rise));
    btn_debounce #(.CNT_W(DEBOUNCE_W)) u_b3 (
        .clk(clk), .rst(rst), .raw(btn[3]), .level(btn3_level), .rise(btn3_rise));

    // -----------------------------------------------------------------------
    // Controls
    // -----------------------------------------------------------------------
    logic [1:0] rate_sel;
    logic [1:0] sw_sync_a, sw_sync_b;

    always_ff @(posedge clk) begin
        sw_sync_a <= sw;
        sw_sync_b <= sw_sync_a;
        if (rst)           rate_sel <= 2'b00;
        else if (btn1_rise) rate_sel <= rate_sel + 1'b1;
    end

    logic tx_enable;
    assign tx_enable = ~btn2_level;      // held down = disabled

    // -----------------------------------------------------------------------
    // Symbol engine
    // -----------------------------------------------------------------------
    logic tx_symbol, tx_oe_n, symbol_tick;

    tx_pattern_source #(
        .CLOCK_HZ (CLOCK_HZ),
        .RATE_0   (1_000),
        .RATE_1   (10_000),
        .RATE_2   (100_000),
        .RATE_3   (1_000_000)
    ) u_tx (
        .clk         (clk),
        .rst         (rst),
        .tx_enable   (tx_enable),
        .pattern_sel (sw_sync_b),
        .rate_sel    (rate_sel),
        .tx_symbol   (tx_symbol),
        .tx_oe_n     (tx_oe_n),
        .symbol_tick (symbol_tick)
    );

    assign ja_tx_symbol   = tx_symbol;
    assign ja_symbol_tick = symbol_tick;
    assign ja_tx_oe_n     = tx_oe_n;

    // -----------------------------------------------------------------------
    // Loopback: synchronise the return, and sample it mid-symbol
    // -----------------------------------------------------------------------
    logic [1:0] lb_sync = '0;
    always_ff @(posedge clk) lb_sync <= {lb_sync[0], ja_loopback};

    logic [SAMPLE_DELAY-1:0] tick_pipe = '0;
    always_ff @(posedge clk) tick_pipe <= {tick_pipe[SAMPLE_DELAY-2:0], symbol_tick};

    logic sample_en;
    assign sample_en = tick_pipe[SAMPLE_DELAY-1];

    logic        locked;
    logic [31:0] error_count;
    logic [15:0] loss_count;

    // bit_count is the number the M0 gate is actually stated in - "1,000,000
    // symbols with zero errors". Four LEDs cannot show a 48-bit counter, so it
    // is left unread here and is the first thing the UART readout must expose.
    /* verilator lint_off UNUSEDSIGNAL */
    logic [47:0] bit_count;
    /* verilator lint_on UNUSEDSIGNAL */

    prbs7_check u_chk (
        .clk         (clk),
        .rst         (rst),
        .en          (sample_en),
        .rx_bit      (lb_sync[1]),
        .locked      (locked),
        .bit_count   (bit_count),
        .error_count (error_count),
        .loss_count  (loss_count)
    );

    // -----------------------------------------------------------------------
    // Status
    // -----------------------------------------------------------------------
    logic err_sticky;
    always_ff @(posedge clk) begin
        if (rst || btn3_rise)
            err_sticky <= 1'b0;
        else if (error_count != 32'd0 || loss_count != 16'd0)
            err_sticky <= 1'b1;
    end

    assign led = {err_sticky, locked, rate_sel};

`ifndef SYNTHESIS
    initial begin
        if (SAMPLE_DELAY < 4)
            $fatal(1, "top_arty_z7: SAMPLE_DELAY must clear the loopback round trip");
    end
`endif

endmodule


// ---------------------------------------------------------------------------
// btn_debounce - synchronise a mechanical input and require it to hold
// ---------------------------------------------------------------------------
module btn_debounce #(
    parameter int unsigned CNT_W = 20
) (
    input  wire  clk,
    input  wire  rst,
    input  wire  raw,
    output logic level,
    output logic rise
);
    logic [1:0]       sync  = '0;
    logic [CNT_W-1:0] count = '0;

    always_ff @(posedge clk) begin
        sync <= {sync[0], raw};
        rise <= 1'b0;

        if (rst) begin
            count <= '0;
            level <= 1'b0;
        end else if (sync[1] != level) begin
            if (count == {CNT_W{1'b1}}) begin
                count <= '0;
                level <= sync[1];
                rise  <= sync[1];          // pulse on press only
            end else begin
                count <= count + 1'b1;
            end
        end else begin
            count <= '0;
        end
    end
endmodule
/* verilator lint_on PROCASSINIT */

`default_nettype wire
