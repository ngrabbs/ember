// ---------------------------------------------------------------------------
// uart_tx - 8N1 transmitter
//
// EMBER experimental S-band payload. Vendor-neutral: no primitives, no IP.
// It outlived one platform change already and is written to outlive the next.
//
// Handshake: assert valid with data; the byte is accepted on the cycle where
// valid and ready are both high.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module uart_tx #(
    parameter int unsigned CLOCK_HZ = 125_000_000,
    parameter int unsigned BAUD     = 115_200
) (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] data,
    input  wire       valid,
    output logic      ready,
    output logic      tx
);
    // 125e6/115200 = 1085.07, so the realised rate is 115,207 baud - 0.006%
    // off, far inside the ~2% a UART receiver tolerates.
    localparam int unsigned DIVISOR = CLOCK_HZ / BAUD;
    localparam int unsigned DW      = $clog2(DIVISOR);

    logic [DW-1:0] baud_count;
    logic [3:0]    bit_index;
    logic [8:0]    shifter;      // {stop, data[7:0]} - the start bit is driven
                                 // directly when the byte is accepted
    logic          busy;

    assign ready = ~busy;

    always_ff @(posedge clk) begin
        if (rst) begin
            busy       <= 1'b0;
            tx         <= 1'b1;   // idle high
            baud_count <= '0;
            bit_index  <= '0;
            shifter    <= '1;
        end else if (!busy) begin
            tx <= 1'b1;
            if (valid) begin
                shifter    <= {1'b1, data};
                busy       <= 1'b1;
                bit_index  <= '0;
                baud_count <= '0;
                tx         <= 1'b0;             // start bit
            end
        end else if (baud_count == DW'(DIVISOR-1)) begin
            // Eight data bits LSB first, then the stop bit: nine after start.
            // busy is held one bit time PAST the stop bit. Dropping it as soon
            // as the stop bit is driven lets a back-to-back sender pull the
            // line low a clock later, so the stop bit lasts one clock instead
            // of one bit time and every byte fails framing at the receiver.
            baud_count <= '0;
            shifter    <= {1'b1, shifter[8:1]};
            tx         <= shifter[0];
            if (bit_index == 4'd9) busy <= 1'b0;
            else                   bit_index <= bit_index + 1'b1;
        end else begin
            baud_count <= baud_count + 1'b1;
        end
    end
endmodule

`default_nettype wire
