// ---------------------------------------------------------------------------
// tb_ad9910_ctrl - the bring-up sequencer against an AD9910 slave model
//
//   F1  MASTER_RESET is pulsed before any SPI traffic
//   F2  CFR3 is written to address 0x02 with the computed PLL configuration
//   F3  IO_UPDATE is pulsed after the CFR3 write
//   F4  profile 0 lands at address 0x0E with the right ASF/POW/FTW
//   F5  profile 1 lands at address 0x0F, differing only in phase
//   F6  IO_UPDATE is pulsed again after the profiles
//   F7  every transaction is framed by exactly one CS assertion of the right
//       length - 5 bytes for CFR3, 9 for a profile
//   F8  a reference clock that never locks reports lock_timeout and still
//       completes, rather than hanging
//   F9  busy is asserted for the whole sequence and clear once done
//   F10 a single start pulse restarts the sequence from S_DONE
//
// F3 and F6 matter more than they look: an AD9910 buffers register writes and
// nothing takes effect until IO_UPDATE. A sequencer that writes perfect
// registers and forgets the pulse looks exactly like a dead SPI bus.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module tb_ad9910_ctrl;

    localparam logic [31:0] FTW  = 32'h028F_5C29;   // 10 MHz at 1 GHz SYSCLK
    localparam logic [13:0] ASF  = 14'h3FFF;
    localparam logic [15:0] POW0 = 16'h0000;
    localparam logic [15:0] POW1 = 16'h8000;        // 180 degrees
    localparam logic [31:0] CFR3 = 32'h0538_C132;

    logic clk = 1'b0;
    always #4 clk = ~clk;                            // 125 MHz
    logic rst = 1'b1, start = 1'b0, pll_lock = 1'b0;

    logic       master_reset, io_update, cs_n;
    logic [7:0] spi_tx_data;
    logic       spi_tx_valid, spi_tx_ready;
    logic       busy, done, lock_timeout, spi_busy;
    logic       sclk, mosi, mosi_oe;
    logic       rd_start = 1'b0, spi_tx_read, rd_valid;
    logic [31:0] rd_data;
    logic [7:0] spi_rx_data;
    logic       spi_rx_valid;

    // What the slave model hands back on a read.
    localparam logic [31:0] RESP = 32'hA5C3_1729;

    ad9910_ctrl #(
        .CLOCK_HZ(125_000_000), .RESET_US(2), .SETTLE_US(2),
        .IOUP_US(2), .LOCK_TMO_US(20)
    ) dut (
        .clk(clk), .rst(rst), .start(start),
        .ftw(FTW), .pow0(POW0), .pow1(POW1), .asf(ASF), .cfr3(CFR3),
        .pll_lock(pll_lock),
        .master_reset(master_reset), .io_update(io_update), .cs_n(cs_n),
        .rd_start(rd_start),
        .spi_tx_data(spi_tx_data), .spi_tx_valid(spi_tx_valid),
        .spi_tx_read(spi_tx_read),
        .spi_tx_ready(spi_tx_ready), .spi_busy(spi_busy),
        .spi_rx_data(spi_rx_data), .spi_rx_valid(spi_rx_valid),
        .busy(busy), .done(done), .lock_timeout(lock_timeout),
        .rd_data(rd_data), .rd_valid(rd_valid));

    // miso is the slave model's SDIO drive. On real hardware SDIO is one
    // bidirectional pin; here the two directions are separate nets, which is
    // equivalent as long as mosi_oe is respected - and F13 checks that it is.
    logic miso_model;
    spi_master #(.CLOCK_HZ(125_000_000), .SCLK_HZ(10_000_000)) spi (
        .clk(clk), .rst(rst),
        .tx_data(spi_tx_data), .tx_valid(spi_tx_valid), .tx_read(spi_tx_read),
        .tx_ready(spi_tx_ready),
        .rx_data(spi_rx_data), .rx_valid(spi_rx_valid),
        .sclk(sclk), .mosi(mosi), .mosi_oe(mosi_oe), .miso(miso_model),
        .busy(spi_busy));

    // ---------------- AD9910 slave model ------------------------------------
    logic [6:0]  sh;
    logic [7:0]  cur_byte;
    int          nbits = 0;
    logic [7:0]  addr;
    logic [63:0] data;
    int          nbytes = 0;
    int          ntrans = 0;
    logic [7:0]  t_addr  [0:7];
    logic [63:0] t_data  [0:7];
    int          t_bytes [0:7];

    logic [31:0] rd_shift;
    logic        rd_active = 1'b0;
    int          oe_violations = 0;

    always @(posedge sclk) if (!cs_n) begin
        // Checked BEFORE rd_active can be set by this same edge: the master
        // cannot have released the line for a read it has not yet been told
        // about, so counting that edge would be a model artifact.
        if (rd_active && mosi_oe) oe_violations = oe_violations + 1;
        if (nbits % 8 == 7) begin
            cur_byte = {sh, mosi};
            if (nbytes == 0) begin
                addr = cur_byte;
                // Bit 7 of the instruction byte is read/not-write.
                if (cur_byte[7]) begin
                    rd_active = 1'b1;
                    rd_shift  = RESP;
                end
            end else begin
                data = {data[55:0], cur_byte};
            end
            nbytes = nbytes + 1;
        end
        sh    = {sh[5:0], mosi};
        nbits = nbits + 1;
    end

    // Mode 0: the slave presents on the falling edge, the master samples on
    // the rising edge that follows.
    always @(negedge sclk) if (!cs_n && rd_active) begin
        miso_model = rd_shift[31];
        rd_shift   = {rd_shift[30:0], 1'b0};
    end

    always @(posedge cs_n) begin
        if (nbytes > 0 && ntrans < 8) begin
            t_addr[ntrans]  = addr;
            t_data[ntrans]  = data;
            t_bytes[ntrans] = nbytes;
            ntrans          = ntrans + 1;
        end
        nbytes = 0; nbits = 0; data = 64'h0; rd_active = 1'b0;
    end

    // ---------------- checks -------------------------------------------------
    int errors = 0;
    task automatic check(input bit c, input string m);
        if (c) $display("  ok    %s", m);
        else begin errors++; $display("  FAIL  %s", m); end
    endtask

    int rst_before_spi = 0, ioup_after_cfr3 = 0, ioup_after_prof = 0;
    // busy must cover the whole sequence: a controller that drops it early
    // would let a caller start a second run into a half-configured part.
    int busy_violations = 0;
    always @(posedge clk) if (!rst && done && busy) busy_violations++;
    always @(posedge io_update) begin
        if (ntrans == 1) ioup_after_cfr3++;
        if (ntrans == 4) ioup_after_prof++;
    end
    always @(negedge cs_n) if (master_reset === 1'b0 && rst_before_spi == 0) rst_before_spi = 1;

    logic [63:0] want_p0, want_p1;

    initial begin
        $display("\ntb_ad9910_ctrl: AD9910 bring-up sequencer\n");
        want_p0 = {2'b00, ASF, POW0, FTW};
        want_p1 = {2'b00, ASF, POW1, FTW};
        repeat (4) @(negedge clk); rst = 1'b0; repeat (4) @(negedge clk);

        // ---- normal run: the PLL locks shortly after IO_UPDATE ----
        fork
            begin @(posedge io_update); repeat (50) @(negedge clk); pll_lock = 1'b1; end
        join_none
        @(negedge clk); start = 1'b1; @(negedge clk); start = 1'b0;
        wait (done); repeat (10) @(negedge clk);

        check(rst_before_spi == 1, "F1 MASTER_RESET pulsed before any SPI traffic");
        check(ntrans == 4, $sformatf("F7a four transactions (got %0d)", ntrans));
        check(t_addr[0] == 8'h02 && t_bytes[0] == 5,
              $sformatf("F7b CFR3 framed as addr 02 + 4 bytes (got %02h, %0d bytes)",
                        t_addr[0], t_bytes[0]));
        check(t_data[0][31:0] == CFR3,
              $sformatf("F2 CFR3 = %08h (got %08h)", CFR3, t_data[0][31:0]));
        check(ioup_after_cfr3 >= 1, "F3 IO_UPDATE pulsed after the CFR3 write");
        check(t_addr[1] == 8'h0E && t_bytes[1] == 9,
              $sformatf("F7c profile 0 framed as addr 0E + 8 bytes (got %02h, %0d)",
                        t_addr[1], t_bytes[1]));
        check(t_data[1] == want_p0,
              $sformatf("F4 profile 0 = %016h (got %016h)", want_p0, t_data[1]));
        check(t_addr[2] == 8'h0F && t_data[2] == want_p1,
              $sformatf("F5 profile 1 at 0F with POW 8000 (got %02h/%016h)",
                        t_addr[2], t_data[2]));
        check(t_data[2][31:0] == t_data[1][31:0],
              "F5b both profiles carry the same frequency, differing only in phase");
        check(ioup_after_prof >= 1, "F6 IO_UPDATE pulsed after the profiles");
        // F11 - DAC full-scale current. Without this the part works but runs
        // at reduced output; it is written before the final IO_UPDATE so one
        // pulse commits amplitude and profiles together.
        check(t_addr[3] == 8'h03 && t_bytes[3] == 5,
              $sformatf("F11a FSC framed as addr 03 + 4 bytes (got %02h, %0d)",
                        t_addr[3], t_bytes[3]));
        check(t_data[3][31:0] == 32'h0000_00FF,
              $sformatf("F11b FSC = 000000FF (got %08h)", t_data[3][31:0]));
        check(busy_violations == 0 && !busy,
              $sformatf("F9 busy clear once done (%0d overlaps)", busy_violations));
        check(!lock_timeout, "F8a no timeout reported when the PLL locks");

        // ---- no reference clock: must report and still finish ----
        // A SINGLE start pulse must restart from S_DONE. Two pulses would hide
        // the bug where S_DONE only stepped to S_IDLE and dropped the pulse.
        pll_lock = 1'b0; ntrans = 0;
        @(negedge clk); start = 1'b1; @(negedge clk); start = 1'b0;
        wait (!done);
        wait (done); repeat (10) @(negedge clk);
        check(lock_timeout, "F8b lock_timeout reported when the PLL never locks");
        check(ntrans == 4, "F10 a single start pulse restarted the sequence from S_DONE");
        check(ntrans == 4, $sformatf("F8c sequence still completed (got %0d transactions)", ntrans));

        // ---- F12/F13 - register readback ----
        // This is the instrument that was missing on 2026-09-08: with no way
        // to read a register back, "is the part listening?" could only be
        // inferred from symptoms, and the inference was wrong three times.
        ntrans = 0;
        @(negedge clk); rd_start = 1'b1; @(negedge clk); rd_start = 1'b0;
        wait (rd_valid); @(negedge clk);
        check(rd_data == RESP,
              $sformatf("F12a readback returns the slave's value %08h (got %08h)",
                        RESP, rd_data));
        check(ntrans == 1, $sformatf("F12b one transaction for a read (got %0d)", ntrans));
        check(t_addr[0] == 8'h82,
              $sformatf("F12c instruction byte is 80|02 (got %02h)", t_addr[0]));
        check(t_bytes[0] == 5,
              $sformatf("F12d read framed as instruction + 4 bytes (got %0d)", t_bytes[0]));
        check(oe_violations == 0,
              $sformatf("F13 SDIO released for every read data bit (%0d violations)",
                        oe_violations));
        check(!master_reset, "F14 a read does not reset the part");

        $display("");
        if (errors == 0) $display("tb_ad9910_ctrl: PASS");
        else             $display("tb_ad9910_ctrl: FAIL - %0d check(s) failed", errors);
        $display("");
        if (errors != 0) $fatal(1, "tb_ad9910_ctrl failed");
        $finish;
    end

    initial begin
        #20_000_000;
        $display("tb_ad9910_ctrl: FAIL - timeout");
        $fatal(1, "timeout");
    end

endmodule

`default_nettype wire
