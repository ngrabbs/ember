// ---------------------------------------------------------------------------
// tb_tx_pattern_source - self-checking testbench for the M0 symbol engine
//
// EMBER experimental S-band payload, milestone M0.
//
// Covers the M0 acceptance items that concern symbol timing and the output:
//
//   C1  reset produces the documented idle state and a disabled interface
//   C2  nothing ticks and the interface stays disabled while tx_enable is low
//   C3  enabling asserts the external buffer enable
//   C4  each rate_sel gives exactly its divisor in clock cycles per symbol
//   C5  the constant patterns hold their levels for many symbols
//   C6  the alternating pattern toggles on every symbol, giving half the
//       symbol rate - the frequency you measure on a scope to confirm the rate
//   C7  tx_symbol changes ONLY on a cycle where symbol_tick is high, which is
//       the simulation form of "the output is registered and cannot glitch"
//   C8  PRBS-7 mode survives a loopback through prbs7_check with zero errors
//   C9  a disable/enable cycle returns to a clean symbol boundary and re-locks
//
// The divisors are shrunk here so a million-symbol run finishes in seconds.
// The RTL defaults (1 k to 1 M symbols/s from a 100 MHz clock) are what the
// hardware builds use; only the ratio matters to these checks.
//
//   make sim-tx         200,000 symbols
//   make sim-long     1,000,000 symbols - the M0 gate
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module tb_tx_pattern_source;

    // 100 MHz clock, divisors of 16, 8, 4, 2.
    localparam int unsigned CLOCK_HZ = 100_000_000;
    localparam int unsigned RATE_0   =   6_250_000;   // divisor 16
    localparam int unsigned RATE_1   =  12_500_000;   // divisor 8
    localparam int unsigned RATE_2   =  25_000_000;   // divisor 4
    localparam int unsigned RATE_3   =  50_000_000;   // divisor 2

    // A function rather than an unpacked array parameter: every simulator
    // elaborates this, and the expected divisors stay next to the rates above.
    function automatic int exp_div(input int r);
        case (r)
            0:       return CLOCK_HZ / RATE_0;
            1:       return CLOCK_HZ / RATE_1;
            2:       return CLOCK_HZ / RATE_2;
            default: return CLOCK_HZ / RATE_3;
        endcase
    endfunction

    localparam int PAT_ZERO = 2'b00;
    localparam int PAT_ONE  = 2'b01;
    localparam int PAT_ALT  = 2'b10;
    localparam int PAT_PRBS = 2'b11;

    // -----------------------------------------------------------------------
    // Clock and DUT
    // -----------------------------------------------------------------------
    logic clk = 1'b0;
    always #5 clk = ~clk;

    logic       rst         = 1'b1;
    logic       tx_enable   = 1'b0;
    logic [1:0] pattern_sel = PAT_ZERO;
    logic [1:0] rate_sel    = 2'b00;

    logic tx_symbol;
    logic tx_oe_n;
    logic symbol_tick;

    tx_pattern_source #(
        .CLOCK_HZ (CLOCK_HZ),
        .RATE_0   (RATE_0),
        .RATE_1   (RATE_1),
        .RATE_2   (RATE_2),
        .RATE_3   (RATE_3)
    ) u_dut (
        .clk         (clk),
        .rst         (rst),
        .tx_enable   (tx_enable),
        .pattern_sel (pattern_sel),
        .rate_sel    (rate_sel),
        .tx_symbol   (tx_symbol),
        .tx_oe_n     (tx_oe_n),
        .symbol_tick (symbol_tick)
    );

    // Loopback checker, fed one bit per symbol tick. This is the simulation
    // stand-in for the optional hardware loopback described in the bring-up
    // document.
    logic        chk_rst = 1'b1;
    logic        locked;
    logic [47:0] bit_count;
    logic [31:0] error_count;
    logic [15:0] loss_count;

    prbs7_check u_chk (
        .clk         (clk),
        .rst         (chk_rst),
        .en          (symbol_tick),
        .rx_bit      (tx_symbol),
        .locked      (locked),
        .bit_count   (bit_count),
        .error_count (error_count),
        .loss_count  (loss_count)
    );

    // -----------------------------------------------------------------------
    // Check plumbing
    // -----------------------------------------------------------------------
    int errors  = 0;
    int symbols = 200_000;

    task automatic check(input bit cond, input string msg);
        if (cond) $display("  ok    %s", msg);
        else begin
            errors++;
            $display("  FAIL  %s", msg);
        end
    endtask

    // -----------------------------------------------------------------------
    // C7 - continuous glitch monitor
    //
    // Sampled at the rising edge, so tx_symbol and symbol_tick here are the
    // values that were present during the cycle just ending. If tx_symbol
    // differs from the previous cycle, symbol_tick must have been high in this
    // one: both are registered off the same edge, so a change without a tick
    // means an unregistered or glitching path reached the output.
    // -----------------------------------------------------------------------
    logic tx_symbol_q  = 1'b0;
    logic monitor_on   = 1'b0;
    int   monitor_hits = 0;

    always @(posedge clk) begin
        if (monitor_on && !rst && (tx_symbol !== tx_symbol_q) && !symbol_tick) begin
            monitor_hits++;
            if (monitor_hits <= 5)
                $display("  FAIL  tx_symbol changed outside a symbol tick at %0t", $time);
        end
        tx_symbol_q <= tx_symbol;
    end

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    task automatic wait_tick();
        do @(negedge clk); while (!symbol_tick);
    endtask

    // Clock cycles from one symbol_tick to the next.
    task automatic measure_period(output int period);
        int n;
        wait_tick();
        n = 0;
        do begin
            @(negedge clk);
            n++;
        end while (!symbol_tick);
        period = n;
    endtask

    task automatic run_symbols(input int n);
        int k;
        for (k = 0; k < n; k++) wait_tick();
    endtask

    // Count symbols with tx_symbol at the wrong level.
    task automatic count_level_errors(input int n, input logic expect_level, output int bad);
        int k;
        bad = 0;
        for (k = 0; k < n; k++) begin
            wait_tick();
            if (tx_symbol !== expect_level) bad++;
        end
    endtask

    // -----------------------------------------------------------------------
    int  period, bad, r, toggles, k;
    logic prev;
    logic [31:0] err_base;
    logic [47:0] bits_base;

    initial begin
        if (!$value$plusargs("symbols=%d", symbols)) symbols = 200_000;

        $display("");
        $display("tb_tx_pattern_source: symbol engine (%0d symbols in the PRBS run)", symbols);
        $display("");

        // -------------------------------------------------------------------
        $display("C1-C3. Reset, disabled state, enable");

        rst         = 1'b1;
        tx_enable   = 1'b0;
        pattern_sel = PAT_ZERO;
        rate_sel    = 2'b00;
        chk_rst     = 1'b1;
        repeat (4) @(negedge clk);

        check(tx_oe_n === 1'b1,     "C1a tx_oe_n is high (interface disabled) during reset");
        check(tx_symbol === 1'b0,   "C1b tx_symbol is at the documented idle level during reset");
        check(symbol_tick === 1'b0, "C1c no symbol ticks during reset");

        rst = 1'b0;
        repeat (64) @(negedge clk);
        check(tx_oe_n === 1'b1,   "C2a tx_oe_n stays high while tx_enable is low");
        check(tx_symbol === 1'b0, "C2b tx_symbol stays idle while tx_enable is low");

        bad = 0;
        repeat (256) begin
            @(negedge clk);
            if (symbol_tick) bad++;
        end
        check(bad == 0, $sformatf("C2c no symbol ticks while disabled (saw %0d)", bad));

        tx_enable = 1'b1;
        repeat (2) @(negedge clk);
        check(tx_oe_n === 1'b0, "C3 tx_oe_n goes low once tx_enable is asserted");

        // -------------------------------------------------------------------
        $display("");
        $display("C4. Symbol timing for each rate_sel");

        monitor_on = 1'b1;
        for (r = 0; r < 4; r++) begin
            rate_sel = r[1:0];
            // rate_sel is sampled at a symbol boundary, so let the change land
            // before measuring.
            wait_tick();
            wait_tick();
            measure_period(period);
            check(period == exp_div(r),
                  $sformatf("C4.%0d rate_sel=%0d gives %0d clocks per symbol (expected %0d)",
                            r, r, period, exp_div(r)));
        end

        // Fastest rate for the rest of the run.
        rate_sel = 2'b11;
        wait_tick();
        wait_tick();

        // -------------------------------------------------------------------
        $display("");
        $display("C5-C6. Patterns");

        pattern_sel = PAT_ZERO;
        wait_tick(); wait_tick();
        count_level_errors(2000, 1'b0, bad);
        check(bad == 0, $sformatf("C5a pattern 00 holds zero for 2000 symbols (%0d wrong)", bad));

        pattern_sel = PAT_ONE;
        wait_tick(); wait_tick();
        count_level_errors(2000, 1'b1, bad);
        check(bad == 0, $sformatf("C5b pattern 01 holds one for 2000 symbols (%0d wrong)", bad));

        pattern_sel = PAT_ALT;
        wait_tick(); wait_tick();
        wait_tick();
        prev    = tx_symbol;
        toggles = 0;
        for (k = 0; k < 2000; k++) begin
            wait_tick();
            if (tx_symbol !== prev) toggles++;
            prev = tx_symbol;
        end
        check(toggles == 2000,
              $sformatf("C6 pattern 10 toggles every symbol, so half the symbol rate (%0d/2000)",
                        toggles));

        // -------------------------------------------------------------------
        $display("");
        $display("C8. PRBS-7 through the loopback checker");

        pattern_sel = PAT_PRBS;
        wait_tick(); wait_tick();
        chk_rst = 1'b0;

        run_symbols(256);
        check(locked, "C8a checker locks on the PRBS-7 symbol stream");

        err_base  = error_count;
        bits_base = bit_count;
        run_symbols(symbols);

        check(error_count == err_base,
              $sformatf("C8b zero errors over %0d symbols (delta=%0d)",
                        symbols, error_count - err_base));
        check(bit_count - bits_base >= symbols - 8,
              $sformatf("C8c checker counted the symbols (%0d checked)",
                        bit_count - bits_base));
        check(loss_count == 16'd0,
              $sformatf("C8d no lock losses (%0d)", loss_count));
        check(locked, "C8e still locked at the end of the run");

        // -------------------------------------------------------------------
        $display("");
        $display("C7. Registered-output monitor");
        check(monitor_hits == 0,
              $sformatf("C7 tx_symbol never changed outside a symbol tick (%0d violations)",
                        monitor_hits));

        // -------------------------------------------------------------------
        $display("");
        $display("C9. Disable and re-enable");

        monitor_on = 1'b0;
        tx_enable  = 1'b0;
        repeat (64) @(negedge clk);
        check(tx_oe_n === 1'b1,   "C9a tx_oe_n high again when disabled");
        check(tx_symbol === 1'b0, "C9b tx_symbol returns to the idle level");

        bad = 0;
        repeat (256) begin
            @(negedge clk);
            if (symbol_tick) bad++;
        end
        check(bad == 0, $sformatf("C9c no ticks while disabled (saw %0d)", bad));

        tx_enable = 1'b1;
        wait_tick();
        wait_tick();
        measure_period(period);
        check(period == exp_div(3),
              $sformatf("C9d timing resumes on a clean boundary (%0d clocks, expected %0d)",
                        period, exp_div(3)));

        monitor_on = 1'b1;
        run_symbols(4000);
        check(locked, "C9e checker re-locks after the enable cycle");
        check(monitor_hits == 0, "C9f no output glitches after re-enable");

        // -------------------------------------------------------------------
        $display("");
        if (errors == 0)
            $display("tb_tx_pattern_source: PASS");
        else
            $display("tb_tx_pattern_source: FAIL - %0d check(s) failed", errors);
        $display("");

        if (errors != 0) $fatal(1, "tb_tx_pattern_source failed");
        $finish;
    end

    initial begin
        #200_000_000;
        $display("tb_tx_pattern_source: FAIL - timeout");
        $fatal(1, "tb_tx_pattern_source timeout");
    end

`ifdef WAVES
    initial begin
        $dumpfile("build/tb_tx_pattern_source.vcd");
        $dumpvars(0, tb_tx_pattern_source);
    end
`endif

endmodule

`default_nettype wire
