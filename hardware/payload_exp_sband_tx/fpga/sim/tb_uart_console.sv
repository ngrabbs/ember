// ---------------------------------------------------------------------------
// tb_uart_console - UART pair plus the M0 console
//
//   D1  a status line comes back byte-exact, with the counters formatted right
//   D2  the banner comes back byte-exact
//   D3  p<n> and r<n> set the pattern and rate
//   D4  e and d drive tx_enable
//   D5  z pulses clear
//   D6  a malformed argument is ignored rather than acted on
//   D7  the counters are snapshotted at 's', not sampled while transmitting
//
// D7 is the one worth having: at 1 Msym/s the bit count advances by thousands
// during the ~4 ms a status line takes to send, so sampling per character
// would print a value that never existed.
//
// The baud divisor is shrunk here so the run takes milliseconds; only the
// ratio matters.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module tb_uart_console;

    localparam int unsigned CLOCK_HZ = 1_000_000;
    localparam int unsigned BAUD     =   125_000;   // divisor 8

    logic clk = 1'b0;
    always #5 clk = ~clk;
    logic rst = 1'b1;

    // console <-> uart
    logic [7:0] c_tx_data;
    logic       c_tx_valid, c_tx_ready;
    logic       line;                    // the serial wire
    logic [7:0] r_data;
    logic       r_valid, r_frame_err;

    // console command input, driven directly
    logic [7:0] cmd_data = 8'h00;
    logic       cmd_valid = 1'b0;

    // status inputs
    logic        locked      = 1'b1;
    logic [47:0] bit_count   = 48'h0000_DEAD_BEEF;
    logic [31:0] error_count = 32'h0000_002A;
    logic [15:0] loss_count  = 16'h0007;

    logic [1:0] pattern_sel, rate_sel;
    logic       tx_enable, clear;

    logic        dds_lock = 1'b1, dds_done = 1'b1, dds_timeout = 1'b0;
    logic [31:0] dds_ftw, dds_cfr3;
    logic        dds_start;
    logic        refclk_en;
    int          dds_starts = 0;
    always @(posedge clk) if (dds_start) dds_starts++;

    m0_console u_con (
        .clk(clk), .rst(rst),
        .rx_data(cmd_data), .rx_valid(cmd_valid),
        .tx_data(c_tx_data), .tx_valid(c_tx_valid), .tx_ready(c_tx_ready),
        .locked(locked), .bit_count(bit_count),
        .error_count(error_count), .loss_count(loss_count),
        .dds_lock(dds_lock), .dds_done(dds_done), .dds_timeout(dds_timeout),
        .dds_ftw(dds_ftw), .dds_cfr3(dds_cfr3), .dds_start(dds_start),
        .refclk_en(refclk_en),
        .pattern_sel(pattern_sel), .rate_sel(rate_sel),
        .tx_enable(tx_enable), .clear(clear));

    uart_tx #(.CLOCK_HZ(CLOCK_HZ), .BAUD(BAUD)) u_tx (
        .clk(clk), .rst(rst), .data(c_tx_data),
        .valid(c_tx_valid), .ready(c_tx_ready), .tx(line));

    uart_rx #(.CLOCK_HZ(CLOCK_HZ), .BAUD(BAUD)) u_rx (
        .clk(clk), .rst(rst), .rx(line),
        .data(r_data), .valid(r_valid), .frame_error(r_frame_err));

    // -----------------------------------------------------------------------
    int errors = 0;
    task automatic check(input bit cond, input string msg);
        if (cond) $display("  ok    %s", msg);
        else begin errors++; $display("  FAIL  %s", msg); end
    endtask

    // Collect everything the console sends.
    logic [7:0] got [0:255];
    int         ngot = 0;
    logic       clr_got = 1'b0;
    logic       saw_frame_err = 1'b0;
    always_ff @(posedge clk) begin
        if (clr_got) begin
            ngot <= 0;
        end else if (r_valid && ngot < 256) begin
            got[ngot] <= r_data;
            ngot      <= ngot + 1;
        end
        if (r_frame_err) saw_frame_err <= 1'b1;
    end

    task automatic clear_got();
        @(negedge clk); clr_got = 1'b1;
        @(negedge clk); clr_got = 1'b0;
    endtask

    task automatic send(input logic [7:0] b);
        @(negedge clk);
        cmd_data  = b;
        cmd_valid = 1'b1;
        @(negedge clk);
        cmd_valid = 1'b0;
    endtask

    // Wait until the console has been quiet for a while.
    task automatic settle();
        int quiet, last;
        quiet = 0; last = ngot;
        while (quiet < 400) begin
            @(negedge clk);
            if (ngot != last) begin last = ngot; quiet = 0; end
            else quiet++;
        end
    endtask

    task automatic expect_string(input string s, input string label);
        int i; bit ok;
        ok = (ngot == s.len());
        if (!ok) $display("        length %0d, expected %0d", ngot, s.len());
        for (i = 0; i < s.len() && i < ngot; i++)
            if (got[i] !== s[i]) begin
                ok = 1'b0;
                $display("        byte %0d is '%c' (%02h), expected '%c'", i, got[i], got[i], s[i]);
            end
        if (!ok) begin
            $write("        got: ");
            for (i = 0; i < ngot; i++)
                if (got[i] >= 8'h20 && got[i] < 8'h7f) $write("%c", got[i]);
            $display("");
        end
        check(ok, label);
    endtask

    initial begin
        $display("\ntb_uart_console: UART pair and the M0 console\n");
        repeat (8) @(negedge clk);
        rst = 1'b0;
        repeat (8) @(negedge clk);

        // D1 - status line, byte exact
        clear_got(); send("s"); settle();
        expect_string({"LOCK 1 BITS 0000DEADBEEF ERR 0000002A LOSS 0007", 8'h0D, 8'h0A},
                      "D1 status line is byte-exact with the counters formatted");

        // D2 - banner
        clear_got(); send("?"); settle();
        expect_string({"EMBER M0 s p0-3 r0-3 e d z k i x0-1 fXXXXXXXX cXXXXXXXX ? ", 8'h0D, 8'h0A},
                      "D2 banner is byte-exact");

        // D3 - pattern and rate
        clear_got(); send("p"); send("2"); settle();
        check(pattern_sel == 2'd2, $sformatf("D3a p2 sets pattern_sel (%0d)", pattern_sel));
        send("r"); send("3"); settle();
        check(rate_sel == 2'd3, $sformatf("D3b r3 sets rate_sel (%0d)", rate_sel));

        // D4 - enable / disable
        send("d"); settle();
        check(tx_enable == 1'b0, "D4a d deasserts tx_enable");
        send("e"); settle();
        check(tx_enable == 1'b1, "D4b e asserts tx_enable");

        // D5 - clear pulses for exactly one cycle
        begin
            int pulses; pulses = 0;
            fork
                begin : watch
                    repeat (40) begin
                        @(posedge clk);
                        if (clear) pulses++;
                    end
                end
            join_none
            send("z");
            wait fork;
            check(pulses == 1, $sformatf("D5 z pulses clear once (%0d)", pulses));
        end

        // D6 - a bad argument is ignored, not acted on
        send("p"); send("x"); settle();
        check(pattern_sel == 2'd2, "D6 a malformed pattern argument is ignored");

        // D7 - counters are snapshotted at 's', not sampled during the send
        clear_got();
        bit_count = 48'h0000_0000_0001;
        send("s");
        repeat (60) @(negedge clk);
        bit_count = 48'hFFFF_FFFF_FFFF;   // move it mid-transmission
        settle();
        expect_string({"LOCK 1 BITS 000000000001 ERR 0000002A LOSS 0007", 8'h0D, 8'h0A},
                      "D7 counters are snapshotted at 's', not sampled per character");

        // D9 - DDS status line
        clear_got(); send("k"); settle();
        expect_string({"DDS LOCK 1 DONE 1 TMO 0 REF 0 FTW 028F5C29", 8'h0D, 8'h0A},
                      "D9 DDS status line is byte-exact");

        // D10 - eight hex digits set the tuning word and trigger a reload
        dds_starts = 0;
        send("f"); send("1"); send("2"); send("3"); send("4");
        send("A"); send("b"); send("C"); send("d"); settle();
        check(dds_ftw == 32'h1234_ABCD,
              $sformatf("D10a f1234AbCd sets the tuning word (got %08h)", dds_ftw));
        check(dds_starts == 1, $sformatf("D10b and reloads once (%0d)", dds_starts));

        // D11 - a bad digit aborts rather than loading half a word
        dds_starts = 0;
        send("f"); send("1"); send("2"); send("q"); settle();
        check(dds_ftw == 32'h1234_ABCD, "D11a a malformed tuning word is ignored");
        check(dds_starts == 0, "D11b and does not trigger a reload");

        // D13 - 'c' targets CFR3, not the tuning word
        dds_starts = 0;
        send("c"); send("0"); send("5"); send("3"); send("8");
        send("C"); send("1"); send("3"); send("2"); settle();
        check(dds_cfr3 == 32'h0538_C132,
              $sformatf("D13a c0538C132 sets CFR3 (got %08h)", dds_cfr3));
        check(dds_ftw == 32'h1234_ABCD, "D13b and leaves the tuning word alone");
        check(dds_starts == 1, "D13c and reloads once");

        // D12 - explicit re-init
        dds_starts = 0;
        send("i"); settle();
        check(dds_starts == 1, $sformatf("D12 i re-runs the DDS bring-up (%0d)", dds_starts));

        // D14 - the reference generator. It must come out of reset OFF: ck_io0
        // lands on the same node the DDS module's own oscillator drives, so a
        // default-on reference is a driver collision waiting for someone to
        // forget a jumper.
        check(refclk_en == 1'b0, "D14a refclk_en is off after reset");
        send("x"); send("1"); settle();
        check(refclk_en == 1'b1, "D14b x1 enables the reference generator");
        send("x"); send("0"); settle();
        check(refclk_en == 1'b0, "D14c x0 releases it again");
        send("x"); send("9"); settle();
        check(refclk_en == 1'b0, "D14d a malformed argument leaves it off");
        send("x"); send("1"); settle();
        clear_got();
        send("k"); settle();
        expect_string({"DDS LOCK 1 DONE 1 TMO 0 REF 1 FTW 1234ABCD", 8'h0D, 8'h0A},
                      "D14e the status line reports REF 1");
        send("x"); send("0"); settle();

        // D8 - every byte in this run framed correctly. A stop bit that is not
        // held for a full bit time shows up here and nowhere else.
        check(!saw_frame_err, "D8 no framing errors across the whole run");

        $display("");
        if (errors == 0) $display("tb_uart_console: PASS");
        else             $display("tb_uart_console: FAIL - %0d check(s) failed", errors);
        $display("");
        if (errors != 0) $fatal(1, "tb_uart_console failed");
        $finish;
    end

    initial begin
        #50_000_000;
        $display("tb_uart_console: FAIL - timeout");
        $fatal(1, "timeout");
    end

endmodule

`default_nettype wire
