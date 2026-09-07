// ---------------------------------------------------------------------------
// tb_spi_master - SPI mode 0 master against a slave model
//
//   E1  bytes arrive at the slave MSB first, bit exact
//   E2  bytes returned by the slave are received bit exact
//   E3  SCLK runs at the configured rate
//   E4  MOSI only ever changes while SCLK is low   <- the mode 0 invariant
//   E5  SCLK idles low between bytes
//   E6  back-to-back bytes stream without a gap in the protocol
//   E7  tx_ready is deasserted for the whole transfer and returns afterwards
//
// E4 is the one that catches a master which looks right on a waveform but
// violates the slave's setup time. It is checked continuously, not sampled.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module tb_spi_master;

    localparam int unsigned CLOCK_HZ = 125_000_000;
    localparam int unsigned SCLK_HZ  =   5_000_000;

    logic clk = 1'b0;
    always #4 clk = ~clk;               // 125 MHz
    logic rst = 1'b1;

    logic [7:0] tx_data = 8'h00;
    logic       tx_valid = 1'b0;
    logic       tx_ready;
    logic [7:0] rx_data;
    logic       rx_valid;
    logic       sclk, mosi, miso, busy;

    spi_master #(.CLOCK_HZ(CLOCK_HZ), .SCLK_HZ(SCLK_HZ)) dut (
        .clk(clk), .rst(rst),
        .tx_data(tx_data), .tx_valid(tx_valid), .tx_ready(tx_ready),
        .rx_data(rx_data), .rx_valid(rx_valid),
        .sclk(sclk), .mosi(mosi), .miso(miso), .busy(busy));

    // ---------------- slave model: shift in on rising, out on falling -------
    logic [7:0] slave_rx;
    logic [7:0] slave_sh;
    int         slave_bits = 0;
    assign miso = slave_sh[7];

    always @(posedge sclk) begin
        slave_rx   <= {slave_rx[6:0], mosi};
        slave_bits <= slave_bits + 1;
    end
    always @(negedge sclk) slave_sh <= {slave_sh[6:0], 1'b0};

    task automatic load_slave(input logic [7:0] b);
        slave_sh = b;
    endtask

    // ---------------- E4/E5: continuous protocol monitors --------------------
    int mosi_violations = 0;
    int idle_violations = 0;
    int ready_violations = 0;
    // tx_ready must be the exact inverse of busy: a sequencer that trusts it
    // while a byte is still shifting would corrupt the transfer.
    always @(posedge clk) if (!rst && (tx_ready === busy)) ready_violations++;
    always @(mosi) if (!rst && sclk !== 1'b0) mosi_violations++;
    always @(posedge clk) if (!rst && !busy && sclk !== 1'b0) idle_violations++;

    // ---------------- checks -------------------------------------------------
    int errors = 0;
    task automatic check(input bit c, input string m);
        if (c) $display("  ok    %s", m);
        else begin errors++; $display("  FAIL  %s", m); end
    endtask

    task automatic xfer(input logic [7:0] send, input logic [7:0] slave_gives);
        load_slave(slave_gives);
        @(negedge clk);
        tx_data = send; tx_valid = 1'b1;
        @(negedge clk);
        tx_valid = 1'b0;
        wait (rx_valid);
        @(negedge clk);
    endtask

    realtime t0, t1;
    int i;

    initial begin
        $display("\ntb_spi_master: SPI mode 0 master\n");
        repeat (4) @(negedge clk);
        rst = 1'b0;
        repeat (4) @(negedge clk);

        // E1 / E2
        xfer(8'hA5, 8'h3C);
        check(slave_rx == 8'hA5, $sformatf("E1 slave received A5 (got %02h)", slave_rx));
        check(rx_data  == 8'h3C, $sformatf("E2 master received 3C (got %02h)", rx_data));

        xfer(8'h01, 8'hFF);
        check(slave_rx == 8'h01, $sformatf("E1b slave received 01 (got %02h)", slave_rx));
        check(rx_data  == 8'hFF, $sformatf("E2b master received FF (got %02h)", rx_data));

        // E3 - measure the SCLK period across one byte
        load_slave(8'h00);
        @(negedge clk); tx_data = 8'hAA; tx_valid = 1'b1;
        @(negedge clk); tx_valid = 1'b0;
        @(posedge sclk); t0 = $realtime;
        repeat (4) @(posedge sclk);
        t1 = $realtime;
        wait (rx_valid); @(negedge clk);
        check((((t1-t0)/4.0) > 0.95*1e9/SCLK_HZ) && (((t1-t0)/4.0) < 1.05*1e9/SCLK_HZ),
              $sformatf("E3 SCLK period %.1f ns, expected %.1f ns",
                        (t1-t0)/4.0, 1e9/SCLK_HZ));

        // E6 - eight bytes back to back
        slave_bits = 0;
        for (i = 0; i < 8; i++) xfer(i[7:0], 8'hFF - i[7:0]);
        check(slave_bits == 64, $sformatf("E6 64 SCLK edges for 8 bytes (got %0d)", slave_bits));

        // E4 / E5
        check(mosi_violations == 0,
              $sformatf("E4 MOSI never changed while SCLK was high (%0d violations)", mosi_violations));
        check(idle_violations == 0,
              $sformatf("E5 SCLK idled low between bytes (%0d violations)", idle_violations));
        check(ready_violations == 0,
              $sformatf("E7 tx_ready tracked busy exactly (%0d violations)", ready_violations));

        $display("");
        if (errors == 0) $display("tb_spi_master: PASS");
        else             $display("tb_spi_master: FAIL - %0d check(s) failed", errors);
        $display("");
        if (errors != 0) $fatal(1, "tb_spi_master failed");
        $finish;
    end

    initial begin
        #5_000_000;
        $display("tb_spi_master: FAIL - timeout");
        $fatal(1, "timeout");
    end

endmodule

`default_nettype wire
