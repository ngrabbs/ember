// ---------------------------------------------------------------------------
// tb_refclk_gen - the AD9910 reference divider
//
//   G1  the period is exactly DIVIDE input clocks
//   G2  the duty cycle is 50% - a reference clock feeding a PLL phase detector
//       wants symmetry, and an asymmetric one degrades close-in phase noise
//   G3  reset produces a defined low output
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module tb_refclk_gen;
    localparam int DIV = 4;

    logic clk = 1'b0;
    always #4 clk = ~clk;            // 125 MHz
    logic rst = 1'b1;
    logic refclk;

    refclk_gen #(.DIVIDE(DIV)) dut (.clk(clk), .rst(rst), .refclk(refclk));

    int errors = 0;
    task automatic check(input bit c, input string m);
        if (c) $display("  ok    %s", m);
        else begin errors++; $display("  FAIL  %s", m); end
    endtask

    int high = 0, low = 0, edges = 0;
    always @(posedge clk) if (!rst) begin
        if (refclk) high++; else low++;
    end
    always @(refclk) if (!rst) edges++;

    initial begin
        $display("\ntb_refclk_gen: AD9910 reference divider\n");
        repeat (4) @(negedge clk);
        check(refclk === 1'b0, "G3 reset holds the reference low");
        rst = 1'b0;

        repeat (DIV * 500) @(negedge clk);

        // 500 full periods -> 1000 transitions
        check(edges >= DIV*500/(DIV/2) - 2 && edges <= DIV*500/(DIV/2) + 2,
              $sformatf("G1 period is %0d input clocks (%0d edges in %0d clocks)",
                        DIV, edges, DIV*500));
        check(high > 0 && low > 0 && (high > low ? high-low : low-high) <= 2,
              $sformatf("G2 duty is 50%% (high %0d, low %0d)", high, low));

        $display("");
        if (errors == 0) $display("tb_refclk_gen: PASS");
        else             $display("tb_refclk_gen: FAIL - %0d check(s) failed", errors);
        $display("");
        if (errors != 0) $fatal(1, "tb_refclk_gen failed");
        $finish;
    end
endmodule

`default_nettype wire
