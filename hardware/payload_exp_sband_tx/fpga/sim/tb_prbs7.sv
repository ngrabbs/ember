// ---------------------------------------------------------------------------
// tb_prbs7 - self-checking testbench for prbs7_gen and prbs7_check
//
// EMBER experimental S-band payload, milestone M0.
//
// Covers the M0 acceptance items that concern the sequence itself and the
// checker that will later count bit errors:
//
//   A1  generated bits match the golden model's vector file, bit for bit
//   A2  the period is exactly 127, not merely a divisor of it
//   A3  one period contains 64 ones and 63 zeros
//   A4  all 127 nonzero states are visited, and all-zeros never is
//   B1  the checker locks on a clean stream and counts zero errors
//   B2  one injected bit error counts exactly one error and keeps lock
//   B3  a second injected error counts exactly one more
//   B4  a continuously inverted stream costs lock and never re-locks
//   B5  removing the inversion restores lock with no further errors
//   B6  a dropped bit costs lock, then the checker re-locks at the new phase
//
// B2 is the check that distinguishes this free-running checker from a
// self-synchronising one: a self-synchronising checker would report three
// errors for one channel error.
//
// Run from the fpga/ directory, after `make vectors`.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

`define VECTOR_FILE "sim/vectors/prbs7_expected.txt"

module tb_prbs7;

    localparam int PERIOD         = 127;
    localparam int LOCK_THRESHOLD = 32;
    localparam int DECAY_BITS     = 64;

    // -----------------------------------------------------------------------
    // Clock, DUTs, stimulus controls
    // -----------------------------------------------------------------------
    logic clk = 1'b0;
    always #5 clk = ~clk;   // 100 MHz

    logic       gen_rst = 1'b1;
    logic       gen_en  = 1'b0;
    logic       gen_bit;
    logic [6:0] gen_state;

    logic        chk_rst = 1'b1;
    logic        chk_en  = 1'b0;
    logic        invert  = 1'b0;
    logic        rx_bit;
    logic        locked;
    logic [47:0] bit_count;
    logic [31:0] error_count;
    logic [15:0] loss_count;

    assign rx_bit = gen_bit ^ invert;

    prbs7_gen u_gen (
        .clk     (clk),
        .rst     (gen_rst),
        .en      (gen_en),
        .bit_o   (gen_bit),
        .state_o (gen_state)
    );

    prbs7_check #(
        .LOCK_THRESHOLD (LOCK_THRESHOLD),
        .LOSS_THRESHOLD (8),
        .DECAY_BITS     (DECAY_BITS)
    ) u_chk (
        .clk         (clk),
        .rst         (chk_rst),
        .en          (chk_en),
        .rx_bit      (rx_bit),
        .locked      (locked),
        .bit_count   (bit_count),
        .error_count (error_count),
        .loss_count  (loss_count)
    );

    // -----------------------------------------------------------------------
    // Check plumbing
    // -----------------------------------------------------------------------
    int errors = 0;

    task automatic check(input bit cond, input string msg);
        if (cond) $display("  ok    %s", msg);
        else begin
            errors++;
            $display("  FAIL  %s", msg);
        end
    endtask

    task automatic run_bits(input int n);
        repeat (n) @(negedge clk);
    endtask

    // -----------------------------------------------------------------------
    // Captured sequence
    // -----------------------------------------------------------------------
    logic       seq [0:2*PERIOD-1];
    logic [6:0] st  [0:PERIOD-1];
    logic       exp_bits [0:PERIOD-1];
    logic       visited [0:127];

    int i, j, p, ones, found_period, distinct;
    logic mismatch;
    logic [31:0] err_base;
    logic [15:0] loss_base;
    logic [47:0] bits_base;

    initial begin
        $display("");
        $display("tb_prbs7: PRBS-7 generator and checker");
        $display("");

        // -------------------------------------------------------------------
        // Part A - sequence properties, checker held in reset
        // -------------------------------------------------------------------
        $display("A. Sequence properties");

        for (i = 0; i < PERIOD; i++) exp_bits[i] = 1'bx;
        $readmemb(`VECTOR_FILE, exp_bits);
        if (exp_bits[0] === 1'bx) begin
            $display("  FAIL  could not read %s - run 'make vectors' first", `VECTOR_FILE);
            $fatal(1, "missing golden vectors");
        end

        gen_rst = 1'b1;
        gen_en  = 1'b0;
        chk_rst = 1'b1;
        chk_en  = 1'b0;
        run_bits(4);
        gen_rst = 1'b0;
        gen_en  = 1'b1;
        @(negedge clk);

        for (i = 0; i < 2*PERIOD; i++) begin
            seq[i] = gen_bit;
            if (i < PERIOD) st[i] = gen_state;
            @(negedge clk);
        end

        // A1 - match the golden model bit for bit.
        mismatch = 1'b0;
        for (i = 0; i < PERIOD; i++)
            if (seq[i] !== exp_bits[i]) mismatch = 1'b1;
        check(!mismatch, "A1 generated bits match the golden model vector file");

        // A2 - period is exactly 127.
        found_period = 0;
        for (p = 1; p <= PERIOD; p++) begin
            if (found_period == 0) begin
                mismatch = 1'b0;
                for (i = 0; i < PERIOD; i++)
                    if (seq[i] !== seq[i+p]) mismatch = 1'b1;
                if (!mismatch) found_period = p;
            end
        end
        check(found_period == PERIOD,
              $sformatf("A2 period is exactly %0d (measured %0d)", PERIOD, found_period));

        // A3 - balance.
        ones = 0;
        for (i = 0; i < PERIOD; i++) ones += seq[i];
        check(ones == 64, $sformatf("A3 balance is 64 ones per period (measured %0d)", ones));

        // A4 - every nonzero state exactly once, all-zeros never.
        for (i = 0; i <= 127; i++) visited[i] = 1'b0;
        distinct = 0;
        mismatch = 1'b0;
        for (i = 0; i < PERIOD; i++) begin
            if (st[i] == 7'b0) mismatch = 1'b1;
            if (!visited[st[i]]) begin
                visited[st[i]] = 1'b1;
                distinct++;
            end
        end
        check(!mismatch, "A4a the all-zeros lock-up state is never reached");
        check(distinct == PERIOD,
              $sformatf("A4b visits all %0d nonzero states (measured %0d)", PERIOD, distinct));

        // -------------------------------------------------------------------
        // Part B - checker behaviour
        // -------------------------------------------------------------------
        $display("");
        $display("B. Checker lock, error counting and recovery");

        gen_rst = 1'b1;
        chk_rst = 1'b1;
        run_bits(4);
        gen_rst = 1'b0;
        chk_rst = 1'b0;
        chk_en  = 1'b1;
        run_bits(4);

        // B1 - clean stream.
        check(!locked, "B1a not locked before enough bits have been seen");
        run_bits(PERIOD + LOCK_THRESHOLD + 64);
        check(locked, "B1b locks on a clean stream");
        bits_base = bit_count;
        run_bits(4000);
        check(error_count == 32'd0,
              $sformatf("B1c zero errors over a clean run (error_count=%0d)", error_count));
        check(bit_count > bits_base + 3900,
              $sformatf("B1d bit_count advances while locked (%0d bits)", bit_count));
        check(loss_count == 16'd0, "B1e no lock losses on a clean stream");

        // B2 - one injected error counts exactly one.
        err_base = error_count;
        invert = 1'b1;
        @(negedge clk);
        invert = 1'b0;
        run_bits(4);
        check(error_count == err_base + 1,
              $sformatf("B2a one injected error counts exactly one (delta=%0d)",
                        error_count - err_base));
        check(locked, "B2b lock survives an isolated error");

        // B3 - the bucket drains, so a later isolated error counts one again.
        run_bits(DECAY_BITS + 16);
        err_base = error_count;
        invert = 1'b1;
        @(negedge clk);
        invert = 1'b0;
        run_bits(DECAY_BITS + 16);
        check(error_count == err_base + 1,
              $sformatf("B3 a second isolated error counts exactly one (delta=%0d)",
                        error_count - err_base));
        check(locked, "B3b lock still held");

        // B4 - continuous inversion must cost lock and must not re-lock.
        loss_base = loss_count;
        invert = 1'b1;
        run_bits(2000);
        check(!locked, "B4a a continuously inverted stream costs lock");
        check(loss_count > loss_base, "B4b the lock loss is counted");
        run_bits(4000);
        check(!locked, "B4c never re-locks on an inverted stream");

        // B5 - removing the inversion restores lock cleanly.
        invert = 1'b0;
        run_bits(PERIOD + LOCK_THRESHOLD + 64);
        check(locked, "B5a re-locks once the inversion is removed");
        err_base = error_count;
        run_bits(4000);
        check(error_count == err_base,
              $sformatf("B5b no further errors after re-lock (delta=%0d)",
                        error_count - err_base));

        // B6 - a dropped bit is a phase slip: lose lock, then re-lock.
        loss_base = loss_count;
        chk_en = 1'b0;
        @(negedge clk);          // generator advances, checker does not
        chk_en = 1'b1;
        run_bits(2000);
        check(loss_count > loss_base, "B6a a dropped bit costs lock");
        run_bits(4000);
        check(locked, "B6b re-locks at the new phase after the slip");
        err_base = error_count;
        run_bits(4000);
        check(error_count == err_base,
              $sformatf("B6c no further errors once re-locked (delta=%0d)",
                        error_count - err_base));

        // -------------------------------------------------------------------
        $display("");
        if (errors == 0)
            $display("tb_prbs7: PASS");
        else
            $display("tb_prbs7: FAIL - %0d check(s) failed", errors);
        $display("");

        if (errors != 0) $fatal(1, "tb_prbs7 failed");
        $finish;
    end

    // Watchdog. A hang is a failure, not a reason to wait.
    initial begin
        #10_000_000;
        $display("tb_prbs7: FAIL - timeout");
        $fatal(1, "tb_prbs7 timeout");
    end

`ifdef WAVES
    initial begin
        $dumpfile("build/tb_prbs7.vcd");
        $dumpvars(0, tb_prbs7);
    end
`endif

endmodule

`default_nettype wire
